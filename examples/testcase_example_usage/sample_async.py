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
Icetea test case example: Command and response public API

Command: async:
               Send command but wait for response in parallel. When sending next command previous response will be wait.
               When using async mode, response is dummy.
               For all command details, please read tc_api.md.

'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_async",
                       title="async command example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of async command",
                       component=["Icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 1,  # devices number
                                    "type": "hardware",  # "hardware" (by default) or "process"
                                    "application": {
                                        "bin": "build_path/build_full_name",  # build binary path
                                    }
                                }
                            }
                        }
                       )

    def case(self):
        # launch an async command
        asyncCmd = self.command(1, "echo hello!", async=True)

        # Wait_for_async_response:
        # Wait for the given asynchronous response to be ready and then parse it
        resp = self.wait_for_async_response("echo", asyncCmd)

        # Verifies that expected response messages found
        resp.verify_message("hello!")
