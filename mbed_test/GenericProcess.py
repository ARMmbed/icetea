"""
Copyright 2016 ARM Limited

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
import logging
import time
import traceback
import select
import string
from sys import platform as _platform
from sys import version_info
from threading import Thread, Lock
from mbed_test.tools import strip_escape, is_pid_running
from collections import deque
from mbed_test.TestStepError import TestStepError
from mbed_test.tools import strip_escape, is_pid_running, unixPlatform
import mbed_test.LogManager as LogManager

class StreamDescriptor():
    def __init__(self, stream, callback):
        self.stream = stream
        self.buf = ""
        self.rq = deque()
        self.has_error = False
        self.callback = callback

class NonBlockingStreamReader():
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
        NonBlockingStreamReader._stream_mtx.acquire()
        NonBlockingStreamReader._streams.append(self._descriptor)
        NonBlockingStreamReader._stream_mtx.release()

    @staticmethod
    def _get_sd(fd):
        for sd in NonBlockingStreamReader._streams:
            if fd == sd.stream.fileno():
                return sd
        return None

    @staticmethod
    def _read_fd(fd):
        """ Read incoming data from file handle.
            Then find the matching StreamDescriptor by fd value."""
        try:
            line = os.read(fd, 1024*1024)
        except OSError:
            sd = NonBlockingStreamReader._get_sd(fd)
            if sd is not None:
                sd.has_error = True
                if sd.callback is not None:
                    sd.callback()
            return

        if len(line):
            sd = NonBlockingStreamReader._get_sd(fd)
            if sd is None:
                return # Process closing
            sd.buf += line
            # Break lines
            s = sd.buf.split(os.linesep)
            for line in s[:-1]:
                sd.rq.appendleft(strip_escape(line.strip()))
                if sd.callback is not None:
                    sd.callback()
            # Store the remainded, its either '' if last char was '\n'
            # or remaining buffer before line end
            sd.buf = s[-1]

    @staticmethod
    def _read_select_poll(poll):
        """ Read PIPEs using select.poll() method
            Available on Linux and some Unixes"""
        npipes = len(NonBlockingStreamReader._streams)
        for sd in NonBlockingStreamReader._streams:
            if not sd.has_error:
                poll.register(sd.stream, select.POLLIN | select.POLLERR | select.POLLHUP | select.POLLNVAL)

        while NonBlockingStreamReader._run_flag:
            for (fd,event) in poll.poll(500):
                if event == select.POLLIN:
                    NonBlockingStreamReader._read_fd(fd)
                else:
                    # Dut died, signal the processing thread so it notices that no lines coming in
                    sd = NonBlockingStreamReader._get_sd(fd)
                    if sd is None:
                        return # PIPE closed but DUT already disappeared
                    sd.has_error = True
                    if sd.callback is not None:
                        sd.callback()
                        return # Force poll object to reregister only alive descriptors

            # Check if new pipes added, don't need mutext just for reading the size
            # If we will not get it right now, we will at next time
            if npipes != len(NonBlockingStreamReader._streams):
                return

    @staticmethod
    def _read_select_kqueue(kq):
        """ Read PIPES using BSD Kqueue"""
        npipes = len(NonBlockingStreamReader._streams)
        # Create list of kevent objects
        kevents = [ select.kevent(s.stream.fileno(),
                           filter=select.KQ_FILTER_READ, # we are interested in reads
                           flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE)
                        for s in NonBlockingStreamReader._streams ]
        while NonBlockingStreamReader._run_flag:
            events = kq.control(kevents, npipes, 0.5) # Wake up twice in second
            for event in events:
                if (event.filter == select.KQ_FILTER_READ):
                    NonBlockingStreamReader._read_fd(event.ident)
            # Check if new pipes added.
            if npipes != len(NonBlockingStreamReader._streams):
                return

    @staticmethod
    def run():
        while NonBlockingStreamReader._run_flag:
            # Wait for streams to appear
            if 0 == len(NonBlockingStreamReader._streams):
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
                kq = select.kqueue()
            except AttributeError:
                pass
            else:
                NonBlockingStreamReader._read_select_kqueue(kq)
                kq.close()
                continue
            # Not workable polling method found
            raise RuntimeError('This OS is not supporting select.poll() or select.kqueue()')

    def stop(self):
        #print('stopping NonBlockingStreamReader..')
        #print('acquire..')
        NonBlockingStreamReader._stream_mtx.acquire()
        #print('acquire..ok')
        NonBlockingStreamReader._streams.remove(self._descriptor)
        if len(NonBlockingStreamReader._streams) == 0:
            NonBlockingStreamReader._run_flag = False
        #print('release..')
        NonBlockingStreamReader._stream_mtx.release()
        #print('release..ok')
        if NonBlockingStreamReader._run_flag == False:
            #print('join..')
            NonBlockingStreamReader._rt.join()
            #print('join..ok')
            del NonBlockingStreamReader._rt
            NonBlockingStreamReader._rt = None
            #print('stopping NonBlockingStreamReader..ok')

    def has_error(self):
        return self._descriptor.has_error

    def readline(self):
        if self.has_error():
            raise RuntimeError("Errors reading PIPE")
        try:
            return self._descriptor.rq.pop()
        except IndexError:
            # No lines in queue
            pass
        return None


class GenericProcess(object):

    # Contstruct GenericProcess instance
    def __init__(self, name, cmd=None, path=None, logger=None):
        self.name = name
        self.proc = None
        self.logger = logger
        self.cmd = None
        self.path = None
        self.gdb = False
        self.gdbs = False
        self.vgdb = False
        self.gdbsPort = None
        self.nobuf = False
        self.valgrind = None
        self.__printIO = True
        self.__valgrindLogBaseName = None
        self.readThread = None
        self.__ignoreReturnCode = False
        self.defaultReturnCode = 0

        if not self.logger:
            self.logger = LogManager.get_bench_logger(name, 'GP', False)
        self.cmd = cmd
        self.path = path

    def enableIOPrints(self):
        self.__printIO = True

    def disableIOPrints(self):
        self.__printIO = False

    @property
    def ignoreReturnCode(self):
        return self.__ignoreReturnCode

    @ignoreReturnCode.setter
    def ignoreReturnCode(self, value):
        self.__ignoreReturnCode = value

    # use gdb for process
    def useGdb(self, gdb=True):
        self.gdb = gdb

    def useGdbs(self, gdbs=True, port=2345):
        self.gdbs = gdbs
        self.gdbsPort = port

    # use vgdb for process
    def useVgdb(self, vgdb=True):
        self.vgdb = vgdb

    def noStdbuf(self, nobuf=True):
        self.nobuf = nobuf

    def useValgrind(self, tool, xml, console, trackOrigins, valgrind_extra_params):
        self.valgrind = tool
        self.valgrindXml = xml
        self.valgrindConsole = console
        self.valgrindTrackOrigins = trackOrigins
        self.valgrindExtraParams = valgrind_extra_params
        if not tool in ['memcheck', 'callgrind', 'massif']:
            raise AttributeError("Invalid valgrind tool: %s" % tool)

    def __getValgrindParameters(self):
        valgrind = []
        if self.valgrind:
            valgrind.extend(['valgrind'])
            if self.valgrind == 'memcheck':
                valgrind.extend(['--tool=memcheck', '--leak-check=full'])
                if self.valgrindTrackOrigins:
                    valgrind.extend(['--track-origins=yes'])
                if self.valgrindConsole:
                    # just dump the default output, which is text dumped to console
                    valgrind.extend([])
                elif self.valgrindXml:
                    valgrind.extend([
                        '--xml=yes',
                        '--xml-file=' + LogManager.get_testcase_logfilename(self.name+'_valgrind_mem.xml', prependTcName=True)
                    ])
                else:
                    valgrind.extend([
                        '--log-file=' + LogManager.get_testcase_logfilename(self.name+'_valgrind_mem.txt')
                    ])

            elif self.valgrind == 'callgrind':
                valgrind.extend([
                    '--tool=callgrind',
                    '--dump-instr=yes',
                    '--simulate-cache=yes',
                    '--collect-jumps=yes' ])
                if self.valgrindConsole:
                    # just dump the default output, which is text dumped to console
                    valgrind.extend([])
                elif self.valgrindXml:
                    valgrind.extend([
                        '--xml=yes',
                        '--xml-file=' + LogManager.get_testcase_logfilename(self.name+'_valgrind_calls.xml', prependTcName=True)
                    ])
                else:
                    valgrind.extend([
                        '--callgrind-out-file=' + LogManager.get_testcase_logfilename(self.name+'_valgrind_calls.data')
                    ])
            elif self.valgrind == 'massif':
                valgrind.extend(['--tool=massif'])
                if self.valgrindConsole:
                    # just dump the default output, which is text dumped to console
                    valgrind.extend([])
                elif self.valgrindXml:
                    valgrind.extend([
                        '--xml=yes',
                        '--xml-file=' + LogManager.get_testcase_logfilename(self.name+'_valgrind_massif.xml', prependTcName=True)
                    ])
                else:
                    valgrind.extend([
                        '--massif-out-file=' + LogManager.get_testcase_logfilename(self.name+'_valgrind_massif.data')
                        ])
            # this allows one to specify misc params to valgrind, eg. "--threshold=0.4" to get some more data from massif
            if self.valgrindExtraParams != '':
                valgrind.extend([self.valgrindExtraParams])
                
        return valgrind

    def start_process(self, cmd=None, path="", processing_callback=None):
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
            self.cmd_arr.extend(['gdbserver', 'localhost:'+ str(self.gdbsPort)])
        elif self.vgdb:
            # add valgrind vgdb parameters, run program but wait for remote gdb connection
            self.cmd_arr.extend(['valgrind', '--vgdb=yes', '--vgdb-error=0'])

        if self.valgrind:
            self.cmd_arr.extend(self.__getValgrindParameters())

        self.cmd_arr.extend( self.cmd.split(" ") )
        prefn = None
        if not platform.system() == "Windows":
            prefn = os.setsid

        self.logger.debug("Instantiating process %s at %s with command %s" % (self.name, self.path, " ".join(self.cmd_arr)), extra={"type" : "   "})
        self.proc = subprocess.Popen(self.cmd_arr, cwd=self.path, stdout=subprocess.PIPE, stdin=subprocess.PIPE, preexec_fn=prefn)

        if unixPlatform:
            import fcntl
            fd = self.proc.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl|os.O_NONBLOCK)

        if self.proc.pid:
            # Start stream reader thread
            self.readThread = NonBlockingStreamReader(self.proc.stdout, processing_callback)
            self.readThread.start()
            self.logger.info("Process '%s' running with pid: %i" % (' '.join(self.cmd_arr), (self.proc.pid)), extra={'type': '<->'})
        else:
            self.logger.warning("Process start fails", extra={'type': '<->'})
            raise NameError('Connection Fails')

    def stop_process(self):
        if self.readThread is not None:
            self.logger.info("stop_process::readThread.stop()-in")
            self.readThread.stop()
            self.logger.info("stop_process::readThread.stop()-out")
        returncode = None
        if self.proc:
            self.logger.info("os.killpg(%d)", self.proc.pid)
            try:
                try:
                    os.killpg(self.proc.pid, signal.SIGTERM)
                except AttributeError:
                    self.logger.info("os.killpg::AttributeError")
                    # Failed most likely because in windows, so use taskkill to kill whole process tree of proc
                    if platform.system() == "Windows":
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.proc.pid)])
                    else:
                        self.logger.info("os.killpg::unknown env")
                        raise EnvironmentError("Unknown platform, don't know how to terminate process")
                self.proc.communicate() # Wait for pipes to clear and process to stop.
                returncode = self.proc.wait()
            except OSError:
                self.logger.info("os.killpg::OSError")
                pass # Ignore
            del self.proc

        if returncode is not None:
            self.logger.info("stop_process::returncode is not None:")
            self.logger.info("Process stopped with returncode %s" % returncode)
            if returncode != self.defaultReturnCode and not self.__ignoreReturnCode:
                raise TestStepError("Process stopped with returncode %d" % returncode)
        self.logger.info("stop_process-out")

    def stop(self):
        self.stop_process()

    def readline(self, timeout=1):
        data = None

        if self.readThread:
            # Ignore the timeout value, return imediately if no lines in queue
            data = self.readThread.readline()
            if data and self.__printIO:
                self.logger.info(data, extra={'type': '<--'})
        return data

    def writeline(self, data, crlf="\r\n"):
        if self.readThread:
            if self.readThread.has_error():
                raise RuntimeError("Error writing PIPE")
        # Check if process still alive
        if self.proc.poll() is not None:
            raise RuntimeError("Process stopped")
        if self.__printIO:
            self.logger.info(data, extra={'type': '-->'})
        self.proc.stdin.write( (data + crlf).decode() )
        self.proc.stdin.flush()

    def is_alive(self):
        return is_pid_running(self.proc.pid)
