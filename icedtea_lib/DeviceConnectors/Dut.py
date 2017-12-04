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

Dut module. Dut is the base class for all different Dut types and many of the lower level
functionalities of duts are implemented here, including the read thread run loop and signaling
mechanisms.
"""


import re
import time
import types
from collections import deque
from threading import Thread, Event, Semaphore


import icedtea_lib.LogManager as LogManager
from icedtea_lib.CliAsyncResponse import CliAsyncResponse
from icedtea_lib.CliRequest import CliRequest
from icedtea_lib.CliResponse import CliResponse
from icedtea_lib.Events.EventMatcher import EventMatcher
from icedtea_lib.Events.Generics import EventTypes
from icedtea_lib.Events.Generics import Event as EventObject
from icedtea_lib.TestStepError import TestStepError, TestStepFail, TestStepTimeout
from icedtea_lib.tools.tools import num


class DutConnectionError(Exception):
    """
    Exception for errors in connecting to dut.
    """
    pass


class Location(object):  # pylint: disable=too-few-public-methods
    """
    Location object for storing x and y coordinates of a dut in a network topology.
    """
    def __init__(self, x_coord=0, y_coord=0):
        self.x_coord = x_coord
        self.y_coord = y_coord


class Dut(object):
    """
    The Dut object is the base behind all our Dut types. It implements the read thread run loop
    and Dut signaling mechanisms and contains many of the shared attributes, methods and data of
    it's subclasses.
    """

    _dutlist = None
    _run = False
    _th = None
    _logger = None
    _sem = None
    _signalled_duts = None

    def __init__(self, name, params=None):
        if Dut._dutlist is None:
            Dut._dutlist = []
        self.testcase = ''
        self.version = {}
        self.dutinformation = None
        self.name = name
        self.dut_name = name
        self.stopped = False
        self.comport = False  # TODO: Move to DutProcess?
        # TODO: Move to MeshCommands
        self.MAC = None  # pylint: disable=invalid-name
        self.location = Location(0, 0)
        self.logger = LogManager.get_bench_logger('Dut.%s' % name, name)
        self.get_time = time.time
        self.query = None # Query to node
        self.query_timeout = 0
        self.query_async_expected = None  # Expected retcode for async cmd
        self.query_async_response = None  # Async response to fullfill when response is available
        self.waiting_for_response = None
        self.response_coming_in = None  # Response coming in
        self.prev = None  # Previous command, stored for logging purposes
        self.traces = []  # All traces
        self.response_traces = []  # Incoming response lines
        self.response_received = Event()
        self.response_received.set()
        self.config = {}
        self.init_cli_cmds = None
        self.post_cli_cmds = None
        self.params = params
        self.index = None
        self.init_done = Event()
        self.init_event_matcher = None
        self.init_wait_timeout = None
        Dut._dutlist.append(self)

    @property
    def platform(self):
        """
        Getter for dut platform.
        :return: Platform as string or None
        """
        if self.dutinformation:
            return self.dutinformation.platform
        return None

    @platform.setter
    def platform(self, value):
        if self.dutinformation:
            self.dutinformation.platform = value

    @property
    def index(self):
        """
        Getter for dut index.
        :return: Index as integer or None
        """
        if self.dutinformation:
            return self.dutinformation.index
        return None

    @index.setter
    def index(self, value):
        if self.dutinformation:
            self.dutinformation.index = value

    @property
    def resource_id(self):
        """
        Getter for dut resource id.
        :return: Resource id as string or None
        """
        if self.dutinformation:
            return self.dutinformation.resource_id
        return None

    @resource_id.setter
    def resource_id(self, value):
        if self.dutinformation:
            self.dutinformation.resource_id = value

    @property
    def vendor(self):
        """
        Getter for dut vendor
        :return: Vendor as string. If not found, will be empty string.
        """
        if self.dutinformation:
            return self.dutinformation.vendor

    @vendor.setter
    def vendor(self, value):
        if self.dutinformation:
            self.dutinformation.vendor = value

    @property
    def build(self):
        """
        Getter for build information.
        :return: Build object or None
        """
        if self.dutinformation:
            return self.dutinformation.build

    @build.setter
    def build(self, value):
        if self.dutinformation:
            self.dutinformation.build = value

    # Minimum requirements from Dut Implementation
    def open_connection(self):
        """open connection to DUT.
        connection information is stored in variable self.comport
        """
        raise NotImplementedError("openConnection is not implemented")

    def openConnection(self): # pylint: disable=invalid-name
        """
        Deprecated. Use open_connection instead
        """
        self.logger.warning("openConnection has been deprecated. Use open_connection instead.")
        return self.open_connection()

    def close_connection(self):
        """close connection to DUT
        """
        raise NotImplementedError("closeConnection is not implemented")

    def closeConnection(self): # pylint: disable=invalid-name
        """
        Deprecated, use close_connection instead.
        """
        self.logger.warning("closeConnection has been deprecated, use close_connection instead.")
        return self.close_connection()

    def writeline(self, data):
        """write single string line to DUT
        :param data: string to be write to DUT, not contains line feeds,
        instead writeline implementation should add line feeds when needed.
        """
        raise NotImplementedError("writeline is not implemented")

    def readline(self, timeout=1):
        """read single string line from DUT.
        :param timeout: readline timeout in seconds.
        :return string from DUT.
        """
        raise NotImplementedError("readline is not implemented")

    def print_info(self):
        '''
        Log information relevant to this DUT.
        :return: Nothing
        '''
        raise NotImplementedError("printInfo has not been implemented")

    def printInfo(self): # pylint: disable=invalid-name
        """
        Deprecated, use print_info instead.
        """
        self.logger.warning("printInfo has been deprecated. Use print_info instead.")
        self.print_info()

    def get_info(self):
        """
        Creates a DutInformation object that contains information on this DUT.
        :return: DutInformation object
        """
        raise NotImplementedError("getInfo has not been implemented")

    def getInfo(self):  # pylint: disable=invalid-name
        """
        Deprecated, use get_info instead.
        """
        self.logger.warning("getInfo has been deprecated. Use get_info instead.")
        return self.get_info()

    # Minimum requirements from Dut Implementation - END

    def set_log_level(self, level):
        """
        Set the level of logging for this dut. NOTE: AFFECTS FILES AS WELL
        :param level: Level to set (integer or constant from logging)
        :return: Nothing
        """
        self.logger.setLevel(level)

    def set_dut_name(self, name):
        """
        Set dut name
        :param name: name to set
        :return: Nothing
        """
        self.name = name
        self.dut_name = name

    def _flash_needed(self, **kwargs):
        """
        Check if flashing of dut is required.
        :return: Boolean. True if flashing is needed, else False
        """
        raise NotImplementedError("flashing needed check not implemented!")

    def get_dut_name(self):
        """
        Get dut dname
        :return: dut name
        """
        return self.dut_name

    def set_init_cli_cmds(self, cmds):
        """
        set cli initialization commands
        :param cmds: list of commands as either strings or lists of strings
        :return: Nothing
        """
        self.init_cli_cmds = cmds

    def set_post_cli_cmds(self, cmds):
        """
        set command to restore cli status to state before init_cli_cmds
        :param cmds: list of commands as either strings or lists of strings
        :return: Nothing
        """
        self.post_cli_cmds = cmds

    def set_default_init_cli_cmds(self):
        """
        Default init commands are set --retcode true, echo off, set --vt100 off, set dut <dut name>
        and set testcase <tc name>
        :return: List of default cli initialization commands.
        """
        init_cli_cmds = []
        init_cli_cmds.append("set --retcode true")
        init_cli_cmds.append("echo off")
        init_cli_cmds.append("set --vt100 off")

        #set dut name as variable
        init_cli_cmds.append('set dut "'+self.name+'"')
        init_cli_cmds.append(['set testcase "' + self.testcase + '"', True])
        return init_cli_cmds

    def set_default_init_cli_human_cmds(self):  # pylint: disable=no-self-use
        """
        Default commands to restore cli to human readable state are echo on, set --vt100 on,
        set --retcode false.
        :return: List of default commands to restore cli to human readable format
        """
        post_cli_cmds = []
        post_cli_cmds.append("echo on")
        post_cli_cmds.append("set --vt100 on")
        post_cli_cmds.append(["set --retcode false", False, False])  # last True is wait=<Boolean>
        return post_cli_cmds

    def init_cli(self):
        """
        Init cli for script
        :return: Nothing
        """
        if self.init_cli_cmds is None:
            self.init_cli_cmds = self.set_default_init_cli_cmds()

        for cli_cmd in self.init_cli_cmds:
            if isinstance(cli_cmd, list) and len(cli_cmd) >= 2:
                asynchronous = cli_cmd[1]
                if len(cli_cmd) > 2:
                    wait = cli_cmd[2]
                else:
                    wait = True
                self.execute_command(cli_cmd[0], wait=wait, async=asynchronous)
            else:
                self.execute_command(cli_cmd)

    def init_wait_register(self):
        """
        Initialize EventMatcher to wait for certain cli_ready_trigger to arrive from this Dut.
        :return: None
        """
        app = self.config.get("application")

        if app:
            bef_init_cmds = app.get("cli_ready_trigger")
            if bef_init_cmds:
                self.init_done.clear()
                self.init_event_matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED,
                                                       bef_init_cmds, self, self.init_done)
                self.init_wait_timeout = app.get("cli_ready_trigger_timeout", 30)
                return
        self.init_done.set()
        return

    def wait_init(self):
        """
        Block until init_done flag is set or until init_wait_timeout happens.
        :return: value of init_done
        """
        return self.init_done.wait(timeout=self.init_wait_timeout)

    def init_cli_human(self):
        """
        Send post_cli_cmds to dut
        :return: Nothing
        """
        if self.post_cli_cmds is None:
            self.post_cli_cmds = self.set_default_init_cli_human_cmds()
        for cli_cmd in self.post_cli_cmds:
            try:
                if isinstance(cli_cmd, list) and len(cli_cmd) >= 2:
                    asynchronous = cli_cmd[1]
                    if len(cli_cmd) > 2:
                        wait = cli_cmd[2]
                    else:
                        wait = True
                    self.execute_command(cli_cmd[0], wait=wait, async=asynchronous)
                else:
                    self.execute_command(cli_cmd)
            except (TestStepFail, TestStepError, TestStepTimeout):
                continue

    def set_time_function(self, function):
        """
        Set time function to be used.
        :param function: callable function
        :return: Nothing
        :raises: ValueError if function is not types.FunctionType.
        """
        if isinstance(function, types.FunctionType):
            self.get_time = function
        else:
            raise ValueError("Invalid value for DUT time function")

    def open_dut(self, port=None):
        """
        Open connection to dut.
        :param port: com port to use.
        :return:
        """
        if port is not None:
            self.comport = port

        try:
            self.open_connection()
        except (DutConnectionError, ValueError) as err:
            self.close_dut(use_prepare=False)
            raise DutConnectionError(str(err))
        except KeyboardInterrupt:
            self.close_dut(use_prepare=False)
            self.close_connection()
            raise

    def _wait_for_exec_ready(self):
        """
        Wait for response
        :return: CliResponse object coming in
        :raises: TestStepTimeout, TestStepError
        """
        #wait for response
        while not self.response_received.wait(1) and self.query_timeout != 0:
            if self.query_timeout != 0 and self.query_timeout < self.get_time():
                if self.prev:
                    cmd = self.prev.cmd
                else:
                    cmd = "???"
                self.logger.error("CMD timeout: "+ cmd)
                self.query_timeout = 0
                raise TestStepTimeout(self.name + " CMD timeout: " + cmd)
            self.logger.debug("Waiting for response... "
                              "timeout=%d", self.query_timeout - self.get_time())

        if self.response_coming_in == -1:
            if self.query_async_response is not None:
                # fullfill the async response with a dummy response and clean the state
                self.query_async_response.set_response(CliResponse())
                self.query_async_response = None
            # raise and log the error
            self.logger.error("No response received, DUT died")
            raise TestStepError("No response received, DUT "+self.name+" died")

        # if an async response is pending, fullfill it with the result
        if self.query_async_response is not None:
            self.query_async_response.set_response(self.response_coming_in)
            self.query_async_response = None

        self.query_timeout = 0
        return self.response_coming_in

    def execute_command(self, req, **kwargs):
        """
        Execute command and return CliResponse
        :param req: String, command to be executed in DUT, or CliRequest, command class which
        contains all configurations like timeout.
        :param kwargs: Configurations (wait, timeout) which will be used when string mode is in use.
        :return: CliResponse, which contains all received data from Dut and parsed retcode.
        """
        if isinstance(req, basestring):
            # backward compatible
            timeout = 50 # Use same default timeout as bench.py
            wait = True
            asynchronous = False
            for key in kwargs:
                if key == 'wait':
                    wait = kwargs[key]
                elif key == 'timeout':
                    timeout = kwargs[key]  # [ms]
                elif key == 'async':
                    asynchronous = kwargs[key]
            req = CliRequest(req,
                             timestamp=self.get_time(),
                             wait=wait,
                             timeout=timeout,
                             async=asynchronous)

        # wait for previous command ready
        if req.wait:
            response = self._wait_for_exec_ready()
            if response is not None and self.query_async_expected is not None:
                if response.retcode != self.query_async_expected:
                    self.logger.error("Asynch call returned unexpected result, "
                                      "expected %d was %d", self.query_async_expected,
                                      response.retcode)
                    raise TestStepFail("Asynch call returned unexpected result")
                self.query_async_expected = None

        # Tell Query to worker thread
        self.response_received.clear()
        self.query_timeout = self.get_time() + req.timeout if req.wait else 0
        self.query = req

        msg = "Async CMD {}, timeout={}, time={}" if req.async else "CMD {}, timeout={}, time={}"
        msg = msg.format(req.cmd, int(self.query_timeout), int(self.get_time()))
        self.logger.debug(msg, extra={'type': '<->'})

        Dut.process_dut(self)

        if req.async is True:
            self.query_async_expected = req.expectedRetcode
            async_response = CliAsyncResponse(self)
            self.query_async_response = async_response
            return async_response

        if req.wait is False:
            self.query_async_expected = req.expectedRetcode
            # if an async response was waiting, just discard the result
            # since the new command has already been sent...
            # This is not ideal but when a command has its flags "Wait == False"
            # the result of the previous command is already discarded in previous
            # stages
            if self.query_async_response is not None:
                self.query_async_response.set_response(CliResponse())
            self.query_async_response = None
            return CliResponse()

        return self._wait_for_exec_ready()

    def close_dut(self, use_prepare=True):
        """
        Close connection to dut
        :param use_prepare: Boolean, default is True. Call prepare_connection_close before
        closing connection.
        :return: Nothing
        """
        if not self.stopped:
            self.logger.debug("Close '%s' connection" % self.dut_name, extra={'type': '<->'})
            if use_prepare:
                try:
                    self.prepare_connection_close()
                except TestStepFail:
                    # We can ignore this for dead Duts, just continue with cleanup
                    pass
            self.stopped = True
            Dut._dutlist.remove(self)
            # Remove myself from signalled dut list, if I'm still there
            if Dut._signalled_duts and Dut._signalled_duts.count(self):
                try:
                    Dut._signalled_duts.remove(self)
                except ValueError:
                    pass

            try:
                if not Dut._dutlist:
                    Dut._run = False
                    Dut._sem.release()
                    Dut._th.join()
                    del Dut._th
                    Dut._th = None
            except AttributeError:
                pass

    def reset(self, method=None):  # pylint: disable=unused-argument
        """
        Reset the dut. Some duts implement different reset methods (hard/soft)
        :param method: String (hard or soft) or None
        :return: Nothing
        :raises: DutConnectionError if reset fails or connection is not restored.
        """
        raise NotImplementedError("reset function not implemented")

    def prepare_connection_close(self):
        """
        Run commands or other required things to prepare to close dut connection.
        :return: Nothing
        """
        pass

    @staticmethod
    def process_dut(dut):
        """Signal worker thread that specified Dut needs processing"""
        if dut.finished():
            return
        Dut._signalled_duts.appendleft(dut)
        Dut._sem.release()

    # Thread runner
    @staticmethod
    def run():
        """
        Main thread runner for all Duts.
        :return: Nothing
        """
        Dut._logger.debug("Start DUT communication", extra={'type': '<->'})
        while Dut._run:
            Dut._sem.acquire()
            try:
                dut = Dut._signalled_duts.pop()
                # Check for pending requests
                if dut.waiting_for_response is not None:
                    item = dut.waiting_for_response
                    # pylint: disable=protected-access
                    dut.response_coming_in = dut.__read_response()
                    if dut.response_coming_in is None:
                        # Continue to next node
                        continue
                    if isinstance(dut.response_coming_in, CliResponse):
                        dut.response_coming_in.set_response_time(item.get_timedelta(dut.get_time()))
                    dut.waiting_for_response = None
                    dut.logger.debug("Got response", extra={'type': '<->'})
                    dut.response_received.set()
                    continue

                # Check for new Request
                if dut.query is not None:
                    item = dut.query
                    dut.query = None
                    dut.logger.info(item.cmd, extra={'type': '-->'})
                    try:
                        dut.writeline(item.cmd)
                    except RuntimeError:
                        dut.response_coming_in = -1
                        dut.response_received.set()
                        continue
                    dut.prev = item # Save previous command for logging purposes
                    if item.wait:
                        # Only caller will care if this was asynchronous.
                        dut.waiting_for_response = item
                    else:
                        dut.query_timeout = 0
                        dut.response_received.set()
                    continue

                try:
                    line = dut.readline()
                except RuntimeError:
                    dut.response_coming_in = -1
                    dut.response_received.set()
                    continue
                if line:
                    dut.traces.append(line)
                    EventObject(EventTypes.DUT_LINE_RECEIVED, dut, line)
                    retcode = dut.check_retcode(line)
                    if retcode is not None:
                        dut.logger.warning("unrequested retcode", extra={'type': '!<-'})
                    dut.logger.debug(line, extra={'type': '<<<'})

            except IndexError:
                pass
        Dut._logger.debug("End DUT communication", extra={'type': '<->'})

    def __read_response(self):
        """
        Internal response reader.
        :return: CliResponse or None
        """
        try:
            line = self.readline()
        except RuntimeError:
            Dut._logger.warning("Failed to read PIPE", extra={'type': '!<-'})
            return -1
        if line:
            self.traces.append(line)
            EventObject(EventTypes.DUT_LINE_RECEIVED, self, line)
            self.response_traces.append(line)
            match = re.search(r"^\[([\w\W]{4})\]\[([\W\w]{4,}?)\]\: (.*)", line)
            if match:
                self.logger.debug(line, extra={'type': '<<<'})
            else:
                self.logger.info(line, extra={'type': '<--'})

            retcode = self.check_retcode(line)
            if retcode is not None:
                resp = CliResponse()
                resp.retcode = retcode
                resp.traces = self.response_traces
                resp.lines = self.response_traces
                self.response_traces = []
                return resp
        return None

    # check retcode
    def check_retcode(self, line):
        """
        Look for retcode on line line and return return code if found.
        :param line: Line to search from
        :return: integer return code or -1 if "cmd tasklet init" is found. None if retcode or cmd
        tasklet
        init not found.
        """
        retcode = None
        match = re.search(r"retcode\: ([-\d]{1,})", line)
        if match:
            retcode = num(str(match.group(1)))

        match = re.search("cmd tasklet init", line)
        if match:
            self.logger.debug("Device Boot up", extra={'type': '   '})
            return -1
        return retcode

    def finished(self):
        """
        Getter for stopped
        :return: Boolean
        """
        return self.stopped

    def start_dut_thread(self):  # pylint: disable=no-self-use
        """
        Start Dut thread.
        :return: Nothing
        """
        if Dut._th is None:
            Dut._run = True
            Dut._sem = Semaphore(0)
            Dut._signalled_duts = deque()
            Dut._logger = LogManager.get_bench_logger('Dut')
            Dut._th = Thread(target=Dut.run, name='DutThread')

            Dut._th.daemon = True
            Dut._th.start()
