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

import sys
from icedtea_lib.bench import Bench
from icedtea_lib.TestStepError import TestStepFail, TestStepError, TestStepTimeout

'''
Testcase for Testcase and Bench, test teardown with invalid command sent to dut.
Should fail in all cases and cause execution to skip case and go to from setUp to tearDown.
'''


class Testcase(Bench):
    def __init__(self, testStepFail=None, testStepError=None, testStepTimeout=None,
                 exception=None, nameError=None, valueError=None, testStepTimeoutInCase=None):
        self.testStepFail = testStepFail
        self.testStepError = testStepError
        self.testStepTimeout = testStepTimeout
        self.exception = exception
        self.nameError = nameError
        self.valueError = valueError
        self.testStepTimeoutInCase = testStepTimeoutInCase
        Bench.__init__(self,
                       name="test_tcTearDown",
                       title="Test Testcase teardown with invalid command",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["IcedTea_ut"],
                       requirements={
                           "duts": {
                               '*': {  # requirements for all nodes
                                   "count": 0,
                               }
                           }}
                       )

    def setup(self):
        # Send invalid command to test if tearDown is launched.
        if self.testStepFail:
            raise TestStepFail("Failed!")
        elif self.testStepError:
            raise TestStepError("Error!")
        elif self.testStepTimeout:
            raise TestStepTimeout("Timeout!")
        elif self.nameError:
            raise NameError("This is a NameError")
        elif self.valueError:
            raise ValueError("This is a ValueError")
        elif self.exception:
            raise Exception("This is a generic exception")

    # If no exception thrown in setUp, case should be run
    def case(self):
        if self.testStepTimeoutInCase:
            raise TestStepTimeout("Timeout in case!")

    def teardown(self):
        pass


if __name__=='__main__':
    sys.exit(Testcase().run())