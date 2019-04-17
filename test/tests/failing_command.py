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

from icetea_lib.bench import Bench
from icetea_lib.TestStepError import TestStepFail, TestStepTimeout


class Testcase(Bench):
    """
    Test case for testing failing command return codes.
    """
    def __init__(self):
        Bench.__init__(self,
                       name="ut_dut_failing_command",
                       title="unittest dut crash in testcase",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["Icetea_ut"],
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 1,
                                   "type": "process",
                                   "application": {
                                       "bin": "test/dut/dummyDut"
                                   },
                               }
                           }
                       }
                      )

    def case(self):  # pylint: disable=missing-docstring
        # Failing command with retcode
        try:
            self.command(1, "retcode -1")
        except TestStepFail:
            pass
        self.command(1, "retcode 0")

        # Failing command with timeout
        try:
            self.command(1, "sleep 5", timeout=4)
        except TestStepTimeout:
            print("TIMEOUT")
