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
