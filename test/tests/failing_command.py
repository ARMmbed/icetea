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

__author__ = 'jaakuk01'

from icedtea_lib.bench import Bench
from icedtea_lib.TestStepError import TestStepFail, TestStepError, TestStepTimeout


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="ut_dut_failing_command",
                       title = "unittest dut crash in testcase",
                       status="development",
                       type="acceptance",
                       purpose = "dummy",
                       component=["IcedTea_ut"],
                       requirements={
                           "duts": {
                               '*': { #requirements for all nodes
                                    "count":1,
                                    "type": "process",
                                    "application":{
                                        "bin": "test/dut/dummyDut"
                                    },
                                }
                           }
                       }
        )

    def case(self):
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
            pass


