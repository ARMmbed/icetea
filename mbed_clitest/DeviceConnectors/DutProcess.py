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

from Dut import Dut, DutConnectionError
from mbed_clitest.TestStepError import TestStepError,TestStepFail
from ..GenericProcess import GenericProcess

class DutProcess(Dut, GenericProcess):
    def __init__(self, type='process', name='process'):
        Dut.__init__(self, name=name)
        GenericProcess.__init__(self, self.name, logger=self.logger)
        self.disableIOPrints() #because those are printed in Dut object
        self.proc = False
        self.type = type

    def openConnection(self):
        self.logger.debug("Open CLI Process '%s'",
                          (self.comport), extra={'type': '<->'})
        self.cmd = self.comport
        # Start process&reader thread. Call Dut.process_dut() when new data is coming
        try:
            self.start_process(self.cmd, processing_callback=lambda:Dut.process_dut(self))
        except KeyboardInterrupt:
            raise
        except Exception:
            raise DutConnectionError("Couldn't start DUT target process")

    def prepareConnectionClose(self):
        if self.is_alive():
            self.logger.info("Process alive, trying to exit", extra={'type': 'XXX'})
            try:
                self.executeCommand("exit", wait=False)
            except (TestStepError,TestStepFail):
                self.logger.warning("exit timed out", extra={'type': 'XXX'})
                pass

    def closeConnection(self):
        self.logger.debug("Close CLI Process '%s'" % self.cmd,
            extra={'type': '<->'})
        self.stop_process()

    def writeline(self, data, crlf="\r\n"):
        GenericProcess.writeline(self, data, crlf=crlf)

    def readline(self, timeout=1):
        return GenericProcess.readline(self, timeout=timeout)

    def reset(self, method=None):
        self.logger.info("Reset not implemented for process DUT")

    def printInfo(self):
        info_string = "DutProcess {}, \n".format(self.name)
        if self.comport:
            info_string = info_string + "CMD {} \n".format(self.comport)
        if self.location:
            info_string = info_string + "Location: x = {}, y = {} \n".format(self.location.x, self.location.y)
        if self.config:
            info_string = info_string + "Configuration for this DUT:\n {} \n".format(self.config)
        self.logger.info(info_string)