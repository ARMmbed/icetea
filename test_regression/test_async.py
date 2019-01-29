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
