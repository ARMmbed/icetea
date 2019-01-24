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
# pylint: disable=missing-docstring
from icetea_lib.bench import Bench
from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.TestStepError import TestStepError


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_close_open",
                       title="Smoke test for testing dut connection "
                             "opening and closing in testcase",
                       status="released",
                       purpose="Verify Command Line Interface",
                       component=["cmdline"],
                       type="smoke",
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 1,
                                   "type": "hardware",
                                   "allowed_platforms": ['K64F', "SAM4E", 'NRF51_DK'],
                                   "application": {"name": "generalTestApplication",
                                                   "version": "1.0"}
                               }
                           }}
                      )

    def case(self):
        # Test command line works before closing
        self.command(1, "echo helloworld")

        # Close connection, wait a second and reopen connection
        self.get_dut(1).close_connection()

        # We could use the serial port at this point for
        # communicating with the DUT in another manner (eg. terminal)
        print("DUT serial port is %s" % self.get_dut(1).comport)

        self.delay(1)
        self.get_dut(1).open_connection()

        # Again test command line works correctly after reopening
        self.command(1, "echo helloworld")

        # Check that exception is raised if we try to reopen connection
        try:
            self.get_dut(1).open_connection()
            # We should never get here,
            # since previous line should raise DutConnectionError exception
            raise TestStepError("Calling open_connection twice didn't raise error as expected!")
        except DutConnectionError:
            pass
