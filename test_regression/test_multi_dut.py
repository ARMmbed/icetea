from icetea_lib.bench import Bench


'''
Regression test: test multiple local devices  
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_multi_dut",
                       title="",
                       status="development",
                       type="regression",
                       purpose="",
                       component=["icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 2,
                                    "type": "hardware",
                                    "allowed_platforms": ['K64F'],
                                    "application": {
                                        "bin": "examples/cliapp/mbed-os5/bin/mbed_cliapp_K64F.bin"
                                    }
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
        # send command to all duts by '*'
        responses = self.command('*', "echo hello world! ")
        # the 'responses' will be a list of all the returned response
        for response in responses:
            response.verify_message("hello world!")
            response.verify_response_time(1)
