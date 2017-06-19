__author__ = 'jaakuk01'

from mbed_test.bench import Bench

class Testcase(Bench):
    def __init__(self, inRampUp=False, inCase=False, inRampDown=False):
        Bench.__init__(self,
                       name="ut_dut_crash",
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

        self.inRampUp = inRampUp
        self.inCase = inCase
        self.inRampDown = inRampDown

    def setUp(self):
        if self.inRampUp:
            self.command(1, "crash", timeout=0.5)

    def case(self):
        if self.inCase:
            self.command(1, "crash", timeout=0.5)

    def tearDown(self):
        if self.inRampDown:
            self.command(1, "crash", timeout=0.5)