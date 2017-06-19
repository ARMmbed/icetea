__author__ = 'jaakuk01'

from mbed_test.bench import Bench
from mbed_test.TestStepError import TestStepFail, TestStepError, TestStepTimeout

class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="ut_dut_failing_command",
                       title = "unittest dut crash in testcase",
                       status="development",
                       type="acceptance",
                       purpose = "dummy",
                       component=["clitest_ut"],
                       requirements={
                           "duts": {
                               '*': { #requirements for all nodes
                                    "count":1,
                                    "type": "process",
                                    "application":{
                                        "bin": "test/dut/dummyDut"
                                    },
                                }
                           }}
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


