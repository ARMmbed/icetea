from icetea_lib.bench import Bench


'''
Regression test: test CLI command and response --> with correct and wrong command
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_cmd_resp",
                       title="icetea command and response APIs example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of icetea command and response APIs",
                       component=["icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 2,
                                    "type": "hardware",
                                    "allowed_platforms": ['K64F'],
                                    "application": {"bin": "examples/cliapp/mbed-os5/bin/mbed_cliapp_K64F.bin"}
                                },
                                "1": {
                                    "nick": "dut1"
                                },
                                "2": {
                                    "nick": "dut2"
                                }
                            }
                        }
                       )

    def case(self):
        # send known command "echo hello" and retcode expected to be 0 --> success() is True
        response = self.command("dut1", "echo hello", expected_retcode=0)
        self.assertTrue(response.success())
        response.verify_message("hello")

        # send unknown command "hello" and the retcode for unknown command is -5 --> fail() is True
        response = self.command("dut2", "hello", expected_retcode=-5)
        self.assertTrue(response.fail())
