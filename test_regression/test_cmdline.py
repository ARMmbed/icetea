from icetea_lib.bench import Bench


'''
Regression test: test command line interface

Send cli command and verify response
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_cmdline",
                       title="regression test for command line interface",
                       status="development",
                       purpose="Verify Command Line Interface",
                       component=["cmdline"],
                       type="regression",
                       requirements={
                           "duts": {
                               '*': {
                                    "count": 1,
                                    "type": "hardware",
                                    "allowed_platforms": ['K64F'],
                                    "application": {"bin": "examples/cliapp/mbed-os5/bin/mbed_cliapp_K64F.bin"}
                               }
                           }
                       }
                       )

    def case(self):
        # send cli command
        resp = self.command(1, "echo helloworld", timeout=5)
        resp.verify_message("helloworld", break_in_fail=True)
