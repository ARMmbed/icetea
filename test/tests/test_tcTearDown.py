import sys
from mbed_test.bench import Bench
from mbed_test.TestStepError import TestStepFail, TestStepError, TestStepTimeout
'''
Testcase for Testcase and Bench, test teardown with invalid command sent to dut.
Should fail in all cases and cause execution to skip case and go to from setUp to tearDown.
'''


class Testcase(Bench):
    def __init__(self, testStepFail=None, testStepError=None, testStepTimeout=None, exception=None, nameError=None,
                 valueError=None):
        self.testStepFail = testStepFail
        self.testStepError = testStepError
        self.testStepTimeout = testStepTimeout
        self.exception = exception
        self.nameError = nameError
        self.valueError = valueError
        Bench.__init__(self,
                       name="test_tcTearDown",
                       title="Test Testcase teardown with invalid command",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["clitest_ut"],
                       requirements={
                           "duts": {
                               '*': {  # requirements for all nodes
                                   "count": 0,
                               }
                           }}
                       )

    def setUp(self):
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
        elif self.kbinterrupt:
            raise KeyboardInterrupt()

    def case(self):
        pass

    def tearDown(self):
        pass
