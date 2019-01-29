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
