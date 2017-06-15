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

from threading import Thread, Lock, Event, Semaphore
import time
import types
#compatible fix with python 2.6 and 3.4:
import sys
from collections import deque, namedtuple
from mbed_clitest.timer import Timer
from mbed_clitest.tools import *
from mbed_clitest.CliRequest import *
from mbed_clitest.CliResponse import *
from mbed_clitest.CliAsyncResponse import CliAsyncResponse
from mbed_clitest.TestStepError import TestStepError, TestStepFail, TestStepTimeout
import mbed_clitest.LogManager as LogManager

class DutConnectionError(Exception):
    pass

class DutInformation:
    def __init__(self, name):
        self.Testcase = ''
        self.version = {}
        self.mesh0 = {}
        self.eth0  = {}
        self.ble0  = {}
        self.name = name

class Location(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Dut(DutInformation):
    _dutlist = None
    _run = False
    _th = None
    _logger = None
    _sem = None
    _signalled_duts = None

    def __init__(self, name, params=None):
        if Dut._th is None:
            Dut._dutlist = []
            Dut._run = True
            Dut._sem = Semaphore(0)
            Dut._signalled_duts = deque()
            Dut._logger = LogManager.get_bench_logger('Dut')
            Dut._th = Thread(target=Dut.run, name='DutThread')
            Dut._th.daemon = True
            Dut._th.start()
        self.name = name
        self.dutName = name
        self._finished = False
        self.comport = False
        self.type = None
        self.MAC = None
        self.go = False
        self.type = None
        self.location = Location(0, 0)
        self.logger = LogManager.get_bench_logger('Dut.%s' % name, name)
        self.get_time = time.time
        DutInformation.__init__(self, name)
        self.q = None # Query to node
        self.q_timeout = 0
        self.q_async_expected = None # Expected retcode for async cmd
        self.q_async_response = None  # The async response to fullfill once the response is available
        self.w = None # Waiting for response
        self.r = None # Response coming in
        self.prev = None # Previous command, stored for logging purposes
        self.traces = [] # All traces
        self.r_traces = [] # Incoming response lines
        self.response_received = Event()
        self.response_received.set()
        self.config = {}
        self.init_cli_cmds = None
        self.post_cli_cmds = None
        self.params = params
        Dut._dutlist.append(self)

    # Minimum requirements from Dut Implementation
    def openConnection(self):
        """open connection to DUT.
        connection information is stored in variable self.comport
        """
        raise NotImplementedError("openConnection is not implemented")

    def closeConnection(self):
        """close connection to DUT
        """
        raise NotImplementedError("closeConnection is not implemented")

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

    def printInfo(self):
        '''
        Log information relevant to this DUT.
        :return: Nothing
        '''
        raise NotImplementedError("printInfo has not been implemented")

    # Minimum requirements from Dut Implementation - END

    def setLogLevel(self, level):
        self.logger.setLevel( level )

    # Set dut number for logging purpose
    def setDutName(self, name):
        self.name = name
        self.dutName = name

    def getDutName(self):
        return self.dutName

    def setInitCLICmds(self, cmds):    
        self.init_cli_cmds = cmds

    def setPostCLICmds(self, cmds):
        self.post_cli_cmds = cmds

    # default init cli commands
    def setDefaultInitCLICmds(self):
        init_cli_cmds = []
        init_cli_cmds.append("set --retcode true")
        init_cli_cmds.append("echo off")
        init_cli_cmds.append("set --vt100 off")

        #set dut name as variable
        init_cli_cmds.append('set dut "'+self.name+'"')
        init_cli_cmds.append(['set testcase "'+self.Testcase+'"', True])
        return init_cli_cmds

    # default init cli commands
    def setDefaultinitCLIhumanCmds(self):
        post_cli_cmds = []
        post_cli_cmds.append("echo on")
        post_cli_cmds.append("set --vt100 on")
        post_cli_cmds.append(["set --retcode false", False, False]) # last True is wait=<Boolean>
        return post_cli_cmds

    # init cli for script
    def initCLI(self):
        if self.init_cli_cmds == None:
            self.init_cli_cmds = self.setDefaultInitCLICmds()            
        for cli_cmd in self.init_cli_cmds:
            if isinstance(cli_cmd, list) and len(cli_cmd) >= 2:
                async = cli_cmd[1]
                if len(cli_cmd) > 2:
                    wait = cli_cmd[2]
                else:
                    wait = True
                self.executeCommand(cli_cmd[0], wait = wait, async = async)
            else:
                self.executeCommand(cli_cmd)

    # init cli for human
    def initCLIhuman(self):
        if self.post_cli_cmds == None:
            self.post_cli_cmds = self.setDefaultinitCLIhumanCmds()
        for cli_cmd in self.post_cli_cmds:
            if isinstance(cli_cmd, list) and len(cli_cmd) >= 2:
                async = cli_cmd[1]
                if len(cli_cmd) > 2:
                    wait = cli_cmd[2]
                else:
                    wait = True
                self.executeCommand(cli_cmd[0], wait = wait, async = async)
            else:
                self.executeCommand(cli_cmd)

    def setTimeFn(self, fn):
        if type(fn) == types.FunctionType:
            self.get_time = fn
        else:
            raise ValueError("Invalid value for DUT time function")

    def Open(self, port=None):
        if port!=None:
            self.comport = port

        try:
            self.openConnection()
        except DutConnectionError:
            self.Close(usePrepare=False)
            raise

    def _waitForExecutionReady(self):
        #wait for response
        while not self.response_received.wait(1):
            if self.q_timeout!=0 and self.q_timeout < self.get_time():
                if self.prev:
                    cmd = self.prev.cmd
                else:
                    cmd = "???"
                self.logger.error("CMD timeout: "+ cmd)
                raise TestStepTimeout(self.name + " CMD timeout: " + cmd)
            #self.logger.debug("Waiting for response_received flag...timeout=%d time=%d r=%s" % (self.q_timeout, self.get_time(), str(self.r)), extra={'type': '<->'})
            self.logger.debug("Waiting for response... timeout=%d" % (self.q_timeout - self.get_time()))

        if self.r == -1:
            if self.q_async_response is not None:
                # fullfill the async response with a dummy response and clean the state
                self.q_async_response._setResponse(CliResponse())
                self.q_async_response = None
            # raise and log the error
            self.logger.error("No response received, DUT died")
            raise TestStepError("No response received, DUT "+self.name+" died")

        # if an async response is pending, fullfill it with the result
        if self.q_async_response is not None:
            self.q_async_response._setResponse(self.r)
            self.q_async_response = None

        self.q_timeout = 0
        return self.r

    ''' execute command and return CliResponse
     \param req[string] command to be executed in DUT
     \param req[CliRequest] command class which contains all configurations like timeout
     \param kwargs configurations (wait, timeout), which will be used when string mode is in use
     \return CliResponse which contains all received data from DUT and parsed retcode.
    '''
    def executeCommand(self, req, **kwargs):
        if isinstance(req, basestring):
            # backward compatible
            timeout = 50 # Use same default timeout as bench.py
            wait = True
            async = False
            for key in kwargs:
                if key == 'wait':
                    wait = kwargs[key]
                elif key == 'timeout':
                    timeout = kwargs[key] #[ms]
                elif key == 'async':
                    async = kwargs[key]
            req = CliRequest(req, timestamp = self.get_time(), wait = wait, timeout=timeout, async = async)

        # wait for previous command ready
        if req.wait:
            r = self._waitForExecutionReady()
            if r is not None and self.q_async_expected is not None:
                if r.retcode != self.q_async_expected:
                    self.logger.error("Asynch call returned unexpected result, expected %d was %d" % (self.q_async_expected, r.retcode) )
                    raise TestStepFail("Asynch call returned unexpected result")
                self.q_async_expected = None

        # Tell Query to worker thread
        self.response_received.clear()
        if req.wait:
            self.q_timeout = self.get_time() + req.timeout
        else:
            self.q_timeout = 0
        self.q = req

        if req.async:
            self.logger.debug("Async CMD '%s' timeout=%d time=%d" % (req.cmd, self.q_timeout, self.get_time()), extra={'type': '<->'})
        else:
            self.logger.debug("CMD '%s' timeout=%d time=%d" % (req.cmd, self.q_timeout, self.get_time()), extra={'type': '<->'})

        Dut.process_dut(self)

        if req.async is True:
            self.q_async_expected = req.expectedRetcode
            async_response = CliAsyncResponse(self)
            self.q_async_response = async_response
            return async_response

        if req.wait is False:
            self.q_async_expected = req.expectedRetcode
            # if an async response was waiting, just discard the result
            # since the new command has already been sent...
            # This is not ideal but when a command has its flags "Wait == False"
            # the result of the previous command is already discarded in previous
            # stages
            if self.q_async_response is not None:
                self.q_async_response._setResponse(CliResponse())
            self.q_async_response = None
            return CliResponse()

        return self._waitForExecutionReady()

    def Close(self, usePrepare=True):
        if not self._finished:
            self.logger.debug("Close '%s' connection" % self.dutName, extra = {'type': '<->'} )
            if usePrepare:
                try:
                    self.prepareConnectionClose()
                except TestStepFail:
                    # We can ignore this for dead Duts, just continue with cleanup
                    pass
            self._finished = True
            Dut._dutlist.remove(self)
            # Remove myself from signalled dut list, if I'm still there
            if Dut._signalled_duts.count(self):
                try:
                    Dut._signalled_duts.remove(self)
                except:
                    pass
            if 0 == len(Dut._dutlist):
                Dut._run = False
                Dut._sem.release()
                Dut._th.join()
                del Dut._th
                Dut._th = None
            self.closeConnection()

    def reset(self, method=None):
        raise NotImplemented("reset function not implemented")

    @staticmethod
    def process_dut(dut):
        """Signal worker thread that specified Dut needs processing"""
        if dut._finished:
            return
        Dut._signalled_duts.appendleft(dut)
        Dut._sem.release()

    # Thread runner
    @staticmethod
    def run():
        Dut._logger.debug("Start DUT communication", extra = {'type': '<->'})
        while Dut._run:
            Dut._sem.acquire()
            try:
                dut = Dut._signalled_duts.pop()
                # Check for pending requests
                if dut.w is not None:
                    item = dut.w
                    #dut.logger.debug("Has wait queue", extra = {'type': '<->'})
                    dut.r = dut.__readResponse()
                    if dut.r is None:
                        # Continue to next node
                        continue
                    if isinstance(dut.r, CliResponse):
                        dut.r.set_response_time( item.get_timedelta(dut.get_time()) )
                    dut.w = None
                    dut.logger.debug("Got reponse", extra = {'type': '<->'})
                    dut.response_received.set()
                    continue

                # Check for new Request
                if dut.q is not None:
                    item = dut.q
                    dut.q = None
                    dut.logger.info(item.cmd, extra = {'type': '-->'})
                    try:
                        dut.writeline(item.cmd)
                    except RuntimeError:
                        dut.r = -1
                        dut.response_received.set()
                        continue
                    dut.prev = item # Save previous command for logging purposes
                    if item.wait:
                        # Only caller will care if this was asynchronous.
                        dut.w = item
                    else:
                        dut.q_timeout = 0
                        dut.response_received.set()
                    continue

                try:
                    line = dut.readline()
                except RuntimeError:
                    dut.r = -1
                    dut.response_received.set()
                    continue
                if line:
                    dut.traces.append(line)
                    retcode = dut.checkRetcode(line)
                    if retcode != None:
                        dut.logger.warning("unrequested retcode", extra = {'type': '!<-'})
                    dut.logger.debug(line, extra = {'type': '<<<'})

            except IndexError:
                pass
        Dut._logger.debug("End DUT communication", extra = {'type': '<->'})

    # response reader
    def __readResponse(self):
        #self.logger.debug("waiting for response.. timeout=%d time=%d" % (timeout, self.get_time()), extra = {'type': '   '})
        try:
           line = self.readline()
        except RuntimeError:
            Dut._logger.warning("Failed to read PIPE", extra = {'type': '!<-'})
            return -1
        if line:
            self.traces.append(line)
            self.r_traces.append(line)
            match = re.search("^\[([\w\W]{4})\]\[([\W\w]{4})\]\: (.*)", line)
            if match:
                self.logger.debug(line, extra = {'type': '<<<' } )
            else:
                self.logger.info(line, extra = {'type': '<--' } )

            retcode = self.checkRetcode(line)
            if retcode != None:
                resp = CliResponse()
                resp.retcode = retcode
                resp.traces = self.r_traces
                resp.lines = self.r_traces
                self.r_traces = []
                return resp
        return None

    # check retcode
    def checkRetcode(self, line):
        retcode = None
        match = re.search("retcode\: ([-\d]{1,})", line)
        if match:
            retcode = num(str(match.group(1)))

        match = re.search("cmd tasklet init", line)
        if match:
            self.logger.debug("Device Boot up", extra={'type': '   '})
            return -1
        return retcode

    def finished(self):
        return self._finished

if __name__ == '__main__':
    from DutProcess import ProcessDut
    dut = ProcessDut()
    #dut = SerialDut()

    dut.setDutName("D1")
    dut.setLogLevel(logging.DEBUG)

    # use process:
    dut.Open('../tools/sample.exe')
    # use serial port:
    #dut.Open("COM14")

    ret = dut.executeCommand("ifconfig")  # wait for reponse
    print(ret.lines)  # print just retcode

    ret = dut.executeCommand("hep2")  # wait for reponse
    print(ret.lines)  # print just retcode

    ret = dut.executeCommand("hep3")  # wait for reponse
    print(ret.lines)  # print just retcode

    #dut.Wait(5)
    Timer().Wait(5)  # wait all duts
    dut.Close()
