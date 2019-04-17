# pylint: disable=too-many-instance-attributes

"""
Copyright 2017 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import platform
import signal
import subprocess
import time
import select
from threading import Thread, Lock
from collections import deque
from icetea_lib.TestStepError import TestStepError
from icetea_lib.tools.tools import strip_escape, is_pid_running, UNIXPLATFORM, IS_PYTHON3
import icetea_lib.LogManager as LogManager


class StreamDescriptor(object):  # pylint: disable=too-few-public-methods
    """
    StreamDescriptor class, container for stream components.
    """
    def __init__(self, stream, callback):
        self.stream = stream
        self.buf = ""
        self.read_queue = deque()  # pylint: disable=invalid-name
        self.has_error = False
        self.callback = callback


class NonBlockingStreamReader(object):
    """
    Implementation for a non-blocking stream reader.
    """
    _instance = None
    _streams = None
    _stream_mtx = None
    _rt = None
    _run_flag = False

    def __init__(self, stream, callback=None):
        # Global class variables
        if NonBlockingStreamReader._rt is None:
            NonBlockingStreamReader._streams = []
            NonBlockingStreamReader._stream_mtx = Lock()
            NonBlockingStreamReader._run_flag = True
            NonBlockingStreamReader._rt = Thread(target=NonBlockingStreamReader.run)
            NonBlockingStreamReader._rt.setDaemon(True)
            NonBlockingStreamReader._rt.start()
        # Instance variables
        self._descriptor = StreamDescriptor(stream, callback)

    def start(self):
        """
        Start the reader, acquires the global lock before appending the descriptor on the stream.
        Releases the lock afterwards.
        :return: Nothing
        """
        NonBlockingStreamReader._stream_mtx.acquire()
        NonBlockingStreamReader._streams.append(self._descriptor)
        NonBlockingStreamReader._stream_mtx.release()

    @staticmethod
    def _get_sd(file_descr):
        """
        Get streamdescriptor matching file_descr fileno.

        :param file_descr: file object
        :return: StreamDescriptor or None
        """
        for stream_descr in NonBlockingStreamReader._streams:
            if file_descr == stream_descr.stream.fileno():
                return stream_descr
        return None

    @staticmethod
    def _read_fd(file_descr):
        """
        Read incoming data from file handle.
        Then find the matching StreamDescriptor by file_descr value.

        :param file_descr: file object
        :return: Return number of bytes read
        """
        try:
            line = os.read(file_descr, 1024 * 1024)
        except OSError:
            stream_desc = NonBlockingStreamReader._get_sd(file_descr)
            if stream_desc is not None:
                stream_desc.has_error = True
                if stream_desc.callback is not None:
                    stream_desc.callback()
            return 0

        if line:
            stream_desc = NonBlockingStreamReader._get_sd(file_descr)
            if stream_desc is None:
                return 0 # Process closing

            if IS_PYTHON3:
                try:
                    # @TODO: further develop for not ascii/unicode binary content
                    line = line.decode("ascii")
                except UnicodeDecodeError:
                    line = repr(line)
            stream_desc.buf += line
            # Break lines
            split = stream_desc.buf.split(os.linesep)
            for line in split[:-1]:
                stream_desc.read_queue.appendleft(strip_escape(line.strip()))
                if stream_desc.callback is not None:
                    stream_desc.callback()
            # Store the remainded, its either '' if last char was '\n'
            # or remaining buffer before line end
            stream_desc.buf = split[-1]
            return len(line)
        return 0

    @staticmethod
    def _read_select_poll(poll):
        """
        Read PIPEs using select.poll() method
        Available on Linux and some Unixes
        """
        npipes = len(NonBlockingStreamReader._streams)
        for stream_descr in NonBlockingStreamReader._streams:
            if not stream_descr.has_error:
                poll.register(stream_descr.stream,
                              select.POLLIN | select.POLLERR | select.POLLHUP | select.POLLNVAL)

        while NonBlockingStreamReader._run_flag:
            for (file_descr, event) in poll.poll(500):
                if event == select.POLLIN:
                    NonBlockingStreamReader._read_fd(file_descr)
                else:
                    # Because event != select.POLLIN, the pipe is closed
                    # but we still want to read all bytes
                    while NonBlockingStreamReader._read_fd(file_descr) != 0:
                        pass
                    # Dut died, signal the processing thread so it notices that no lines coming in
                    stream_descr = NonBlockingStreamReader._get_sd(file_descr)
                    if stream_descr is None:
                        return # PIPE closed but DUT already disappeared
                    stream_descr.has_error = True
                    if stream_descr.callback is not None:
                        stream_descr.callback()
                        return # Force poll object to reregister only alive descriptors

            # Check if new pipes added, don't need mutext just for reading the size
            # If we will not get it right now, we will at next time
            if npipes != len(NonBlockingStreamReader._streams):
                return

    @staticmethod
    def _read_select_kqueue(k_queue):
        """
        Read PIPES using BSD Kqueue
        """
        npipes = len(NonBlockingStreamReader._streams)
        # Create list of kevent objects
        # pylint: disable=no-member
        kevents = [select.kevent(s.stream.fileno(),
                                 filter=select.KQ_FILTER_READ,
                                 flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE)
                   for s in NonBlockingStreamReader._streams]
        while NonBlockingStreamReader._run_flag:
            events = k_queue.control(kevents, npipes, 0.5)  # Wake up twice in second
            for event in events:
                if event.filter == select.KQ_FILTER_READ:  # pylint: disable=no-member
                    NonBlockingStreamReader._read_fd(event.ident)
            # Check if new pipes added.
            if npipes != len(NonBlockingStreamReader._streams):
                return

    @staticmethod
    def run():
        """
        Run loop
        """
        while NonBlockingStreamReader._run_flag:
            # Wait for streams to appear
            if not NonBlockingStreamReader._streams:
                time.sleep(0.2)
                continue
            # Try to get correct select/poll method for this OS
            # Try if select.poll() is supported (Linux/UNIX)
            try:
                poll = select.poll()
            except AttributeError:
                pass
            else:
                NonBlockingStreamReader._read_select_poll(poll)
                del poll
                continue
            # Try is select.kqueue is supported (BSD/OS X)
            try:
                k_queue = select.kqueue()  # pylint: disable=no-member
            except AttributeError:
                pass
            else:
                NonBlockingStreamReader._read_select_kqueue(k_queue)
                k_queue.close()
                continue
            # Not workable polling method found
            raise RuntimeError('This OS is not supporting select.poll() or select.kqueue()')

    def stop(self):
        """
        Stop the reader
        """
        # print('stopping NonBlockingStreamReader..')
        # print('acquire..')
        NonBlockingStreamReader._stream_mtx.acquire()
        # print('acquire..ok')
        NonBlockingStreamReader._streams.remove(self._descriptor)
        if not NonBlockingStreamReader._streams:
            NonBlockingStreamReader._run_flag = False
        # print('release..')
        NonBlockingStreamReader._stream_mtx.release()
        # print('release..ok')
        if NonBlockingStreamReader._run_flag is False:
            # print('join..')
            NonBlockingStreamReader._rt.join()
            # print('join..ok')
            del NonBlockingStreamReader._rt
            NonBlockingStreamReader._rt = None
            # print('stopping NonBlockingStreamReader..ok')

    def has_error(self):
        """
        :return: Boolean, True if _descriptor.has_error is True. False otherwise
        """
        return self._descriptor.has_error

    def readline(self):
        """
        Readline implementation.

        :return: popped line from descriptor queue. None if nothing found
        :raises: RuntimeError if errors happened while reading PIPE
        """
        try:
            return self._descriptor.read_queue.pop()
        except IndexError:
            # No lines in queue
            if self.has_error():
                raise RuntimeError("Errors reading PIPE")
        return None


class GenericProcess(object):
    """
    Generic process implementation for use with Dut.
    """
    # Contstruct GenericProcess instance
    def __init__(self, name, cmd=None, path=None, logger=None):
        self.name = name
        self.proc = None
        self.logger = logger
        self.cmd = None
        self.cmd_arr = None
        self.path = None
        self.gdb = False
        self.gdbs = False
        self.vgdb = False
        self.gdbs_port = None
        self.nobuf = False
        self.valgrind = None
        self.valgrind_xml = None
        self.valgrind_console = None
        self.valgrind_track_origins = None
        self.valgrind_extra_params = None
        self.__print_io = True
        self.__valgrind_log_basename = None
        self.read_thread = None
        self.__ignore_return_code = False
        self.default_retcode = 0

        if not self.logger:
            self.logger = LogManager.get_bench_logger(name, 'GP', False)
        self.cmd = cmd
        self.path = path

    def enable_io_prints(self):
        """
        Enable IO prints
        """
        self.__print_io = True

    def disable_io_prints(self):
        """
        Disable IO prints
        """
        self.__print_io = False

    @property
    def ignore_return_code(self):
        """
        Return value of __ignoreReturnCode
        """
        return self.__ignore_return_code

    @ignore_return_code.setter
    def ignore_return_code(self, value):
        """
        Set __ignoreReturnCode
        """
        self.__ignore_return_code = value

    # use gdb for process
    def use_gdb(self, gdb=True):
        """
        Set gdb use for process.

        :param gdb: Boolean, defaults to True.
        """
        self.gdb = gdb

    def use_gdbs(self, gdbs=True, port=2345):
        """
        Set gdbs use for process.

        :param gdbs: Boolean, default is True
        :param port: Port number for gdbserver
        """
        self.gdbs = gdbs
        self.gdbs_port = port

    # use vgdb for process
    def use_vgdb(self, vgdb=True):
        """
        Set vgdb for process.

        :param vgdb: Boolean, defaults to True
        """
        self.vgdb = vgdb

    def no_std_buf(self, nobuf=True):
        """
        Set buffering of stdio.

        :param nobuf: Defaults to True (no buffering)
        """
        self.nobuf = nobuf

    # pylint: disable=too-many-arguments
    def use_valgrind(self, tool, xml, console, track_origins, valgrind_extra_params):
        """
        Use Valgrind.

        :param tool: Tool name, must be memcheck, callgrind or massif
        :param xml: Boolean output xml
        :param console: Dump output to console, Boolean
        :param track_origins: Boolean, set --track-origins=yes
        :param valgrind_extra_params:  Extra parameters
        :return: Nothing
        :raises: AttributeError if invalid tool set.
        """
        self.valgrind = tool
        self.valgrind_xml = xml
        self.valgrind_console = console
        self.valgrind_track_origins = track_origins
        self.valgrind_extra_params = valgrind_extra_params
        if not tool in ['memcheck', 'callgrind', 'massif']:
            raise AttributeError("Invalid valgrind tool: %s" % tool)

    def __get_valgrind_params(self):
        """
        Get Valgrind command as list.

        :return: list
        """
        valgrind = []
        if self.valgrind:
            valgrind.extend(['valgrind'])
            if self.valgrind == 'memcheck':
                valgrind.extend(['--tool=memcheck', '--leak-check=full'])
                if self.valgrind_track_origins:
                    valgrind.extend(['--track-origins=yes'])
                if self.valgrind_console:
                    # just dump the default output, which is text dumped to console
                    valgrind.extend([])
                elif self.valgrind_xml:
                    valgrind.extend([
                        '--xml=yes',
                        '--xml-file=' + LogManager.get_testcase_logfilename(
                            self.name + '_valgrind_mem.xml', prepend_tc_name=True)
                    ])
                else:
                    valgrind.extend([
                        '--log-file=' + LogManager.get_testcase_logfilename(
                            self.name + '_valgrind_mem.txt')
                    ])

            elif self.valgrind == 'callgrind':
                valgrind.extend([
                    '--tool=callgrind',
                    '--dump-instr=yes',
                    '--simulate-cache=yes',
                    '--collect-jumps=yes'])
                if self.valgrind_console:
                    # just dump the default output, which is text dumped to console
                    valgrind.extend([])
                elif self.valgrind_xml:
                    valgrind.extend([
                        '--xml=yes',
                        '--xml-file=' + LogManager.get_testcase_logfilename(
                            self.name + '_valgrind_calls.xml', prepend_tc_name=True)
                    ])
                else:
                    valgrind.extend([
                        '--callgrind-out-file=' + LogManager.get_testcase_logfilename(
                            self.name + '_valgrind_calls.data')
                    ])
            elif self.valgrind == 'massif':
                valgrind.extend(['--tool=massif'])
                valgrind.extend([
                    '--massif-out-file=' + LogManager.get_testcase_logfilename(
                        self.name + '_valgrind_massif.data')
                    ])
            # this allows one to specify misc params to valgrind,
            # eg. "--threshold=0.4" to get some more data from massif
            if self.valgrind_extra_params != '':
                valgrind.extend(self.valgrind_extra_params.split())

        return valgrind

    def start_process(self, cmd=None, path="", processing_callback=None):
        """
        Start the process.

        :param cmd: Command to run
        :param path: cwd
        :param processing_callback: Callback for processing lines
        :return: Nothing
        :raises: NameError if Connection fails
        """
        self.cmd = self.cmd if not cmd else cmd
        self.path = self.path if not path else path
        if self.path:
            self.path = os.path.abspath(self.path)
        self.cmd_arr = []

        # set stdbuf in/out/err to zero size = no buffers in use
        if self.nobuf:
            self.cmd_arr.extend(['stdbuf', '-i0', '-o0', '-e0'])

        # check if user want to debug this process
        if self.gdb:
            # add gdb parameters, run program immediately
            self.cmd_arr.extend(['gdb', '-ex=run', '--args'])
        elif self.gdbs:
            # add gdbserver parameters, run program immediately
            self.cmd_arr.extend(['gdbserver', 'localhost:' + str(self.gdbs_port)])
        elif self.vgdb:
            # add valgrind vgdb parameters, run program but wait for remote gdb connection
            self.cmd_arr.extend(['valgrind', '--vgdb=yes', '--vgdb-error=0'])

        if self.valgrind:
            self.cmd_arr.extend(self.__get_valgrind_params())

        self.cmd_arr.extend(self.cmd)
        prefn = None
        if not platform.system() == "Windows":
            prefn = os.setsid

        self.logger.debug("Instantiating process "
                          "%s at %s with command %s"
                          % (self.name, self.path, " ".join(self.cmd_arr)),
                          extra={"type": "   "})
        self.proc = subprocess.Popen(self.cmd_arr, cwd=self.path, stdout=subprocess.PIPE,
                                     stdin=subprocess.PIPE, preexec_fn=prefn)

        if UNIXPLATFORM:
            import fcntl
            file_descr = self.proc.stdout.fileno()
            fcntl_var = fcntl.fcntl(file_descr, fcntl.F_GETFL)
            fcntl.fcntl(file_descr, fcntl.F_SETFL, fcntl_var | os.O_NONBLOCK)

        if self.proc.pid:
            # Start stream reader thread
            self.read_thread = NonBlockingStreamReader(self.proc.stdout, processing_callback)
            self.read_thread.start()
            self.logger.info("Process '%s' running with pid: %i" % (' '.join(self.cmd_arr),
                                                                    self.proc.pid),
                             extra={'type': '<->'})
        else:
            self.logger.warning("Process start fails", extra={'type': '<->'})
            raise NameError('Connection Fails')

    def stop_process(self):
        """
        Stop the process.

        :raises: EnvironmentError if stopping fails due to unknown environment
        TestStepError if process stops with non-default returncode and return code is not ignored.
        """
        if self.read_thread is not None:
            self.logger.debug("stop_process::readThread.stop()-in")
            self.read_thread.stop()
            self.logger.debug("stop_process::readThread.stop()-out")
        returncode = None
        if self.proc:
            self.logger.debug("os.killpg(%d)", self.proc.pid)

            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGKILL):
                timeout = 5
                try:
                    try:
                        self.logger.debug("Trying signal %s", sig)
                        os.killpg(self.proc.pid, sig)
                    except AttributeError:
                        self.logger.debug("os.killpg::AttributeError")
                        # Failed most likely because in windows,
                        # so use taskkill to kill whole process tree of proc
                        if platform.system() == "Windows":
                            subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.proc.pid)])
                        else:
                            self.logger.debug("os.killpg::unknown env")
                            raise EnvironmentError("Unknown platform, "
                                                   "don't know how to terminate process")
                    while self.proc.poll() is None and timeout > 0:
                        time.sleep(1)
                        timeout -= 1
                    returncode = self.proc.poll()
                    if returncode is not None:
                        break
                except OSError as error:
                    self.logger.info("os.killpg::OSError: %s", error)
            self.proc = None

        if returncode is not None:
            self.logger.debug("Process stopped with returncode %s" % returncode)
            if returncode != self.default_retcode and not self.__ignore_return_code:
                raise TestStepError("Process stopped with returncode %d" % returncode)
        self.logger.debug("stop_process-out")

    def stop(self):
        """
        Stop the process
        See stop_process for more information
        """
        self.stop_process()

    def readline(self, timeout=1):  # pylint: disable=unused-argument
        """
        Readline implementation.

        :param timeout: Timeout, not used
        :return: Line read or None
        """
        data = None
        if self.read_thread:
            # Ignore the timeout value, return imediately if no lines in queue
            data = self.read_thread.readline()
            if data and self.__print_io:
                self.logger.info(data, extra={'type': '<--'})
        return data

    def writeline(self, data, crlf="\r\n"):
        """
        Writeline implementation.

        :param data: Data to write
        :param crlf: Line end characters, defailt is \r\n
        :return: Nothing
        :raises: RuntimeError if errors happen while writing to PIPE or process stops.
        """
        if self.read_thread:
            if self.read_thread.has_error():
                raise RuntimeError("Error writing PIPE")
        # Check if process still alive
        if self.proc.poll() is not None:
            raise RuntimeError("Process stopped")
        if self.__print_io:
            self.logger.info(data, extra={'type': '-->'})
        self.proc.stdin.write(bytearray(data + crlf, 'ascii'))
        self.proc.stdin.flush()

    def is_alive(self):
        """
        Is process alive.

        :return: Boolean, True is process is still running.
        """
        return is_pid_running(self.proc.pid) if self.proc else False
