__author__ = 'jaakuk01'

from mbed_test.bench import Bench
from mbed_test.TestStepError import TestStepFail
from mbed_test.TestStepError import TestStepError


class Testcase(Bench):
    def __init__(self, testStepFail=False, testStepError=False, nameError=False, valueError=False, exception=False, inRampUp=False, inCase=False, inRampDown=False):
        self.testStepError = testStepError
        self.testStepFail = testStepFail
        self.nameError = nameError
        self.valueError = valueError
        self.exception = exception
        self.inRampUp = inRampUp
        self.inCase = inCase
        self.inRampDown = inRampDown
        Bench.__init__(self,
                       name="ut_exception",
                       title = "unittest exception in testcase",
                       status="development",
                       type="acceptance",
                       purpose = "dummy",
                       component=["clitest_ut"],
                       requirements={
                           "duts": {
                               '*': { #requirements for all nodes
                                    "count": 1,
                                    "type": "process",
                                    "application": {
                                        "bin": "test/dut/dummyDut"
                                    }
                               }
                           }
                       })

    def raiseExc(self):
        if self.testStepFail:
            raise TestStepFail("This is a TestStepFail")
        elif self.testStepError:
            raise TestStepError("This is a TestStepError")
        elif self.nameError:
            raise NameError("This is a NameError")
        elif self.valueError:
            raise ValueError("This is a ValueError")
        elif self.exception:
            raise Exception( "This is a generic exception" )

    def setUp(self):
        if self.inRampUp:
            self.raiseExc()
        self.command(1, "ifup")

    def case(self):
        if self.inCase:
            self.raiseExc()
        self.command(1, "ping a:b::c:d")

    def tearDown(self):
        if self.inRampDown:
            self.raiseExc()
        self.command(1, "ifdown")