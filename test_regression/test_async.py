from icetea_lib.bench import Bench


'''
Regression test: test async command and parse it's response

Command: async:
               Send command and wait for response in parallel. When sending next command previous response will be wait.
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_async",
                       title="async command and response test",
                       status="development",
                       type="regression",
                       purpose="test async command and response parse works",
                       component=["icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 1,
                                    "type": "hardware",
                                    "allowed_platforms": ["K64F"],
                                    "application": {
                                        "bin": "examples/cliapp/mbed-os5/bin/mbed_cliapp_K64F.bin"
                                    }
                                }
                            }
                        }
                       )

    def case(self):
        # launch an async command
        asyncCmd = self.command(1,  "echo HelloWorld!", asynchronous=True)

        # wait_for_async_response: Wait for the given asynchronous response to be ready and then parse it
        resp = self.wait_for_async_response("echo", asyncCmd)

        # Verifies that expected response messages found
        resp.verify_message("HelloWorld!")
        self.assertTrue(resp.success())
