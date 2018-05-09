from icetea_lib.bench import Bench
from icetea_lib.Events.EventMatcher import EventMatcher
from icetea_lib.Events.Generics import EventTypes


'''
Regression test: test cli init.
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_cli_init",
                       title="test cli init with EventMatcher",
                       status="development",
                       type="regression",
                       purpose="test cli init with EventMatcher ",
                       component=["icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 1,
                                    "type": "hardware",
                                    "allowed_platforms": ["K64F"],
                                    "application": {
                                        "bin": "examples/cliapp/mbed-os5/bin/mbed_cliapp_K64F.bin",
                                        "cli_ready_trigger": "/>"
                                    }
                                }
                            }
                       }
                       )

    def case(self):
        self.logger.info("cli_ready_trigger will help icetea wait until application is ready for communication.")

        # create triggers from received data
        EventMatcher(EventTypes.DUT_LINE_RECEIVED,
                     "ping",
                     self.get_dut(1),
                     callback=self.ping_cb)
        # this will trig above callback
        self.command(1, "echo ping")

    def ping_cb(self, ref, line):
        self.logger.info("pong (because of received %s)", line)
