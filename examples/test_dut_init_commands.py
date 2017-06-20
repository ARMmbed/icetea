"""
Copyright 2016 ARM Limited

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

from mbed_test.bench import Bench


class Testcase(Bench):

    def __init__(self):
        Bench.__init__(self,
                       name="test_dut_init_commands",
                       title = "Test_DUT_init_commands",
                       status = "development",
                       type = "regression",
                       purpose = "",
                       component=["thread"],
                       requirements={
                           "duts": {
                               '*': { #requirements for all nodes
                                    "count":1,
                                    "type": "hardware", #allowed values: hardware(default), process
                                    "allowed_platforms": ['K64F'],
                                    "application":{ "name":"generalTestApplication", "version": "1.0", "init_cli_cmds": [], "post_cli_cmds": []},
                                    "rf_channel": 11
                               },
                               "1": { "nick": "LEADER" },
                           }}
        )

    def setUp(self):
        self.reset_dut(1)
        self.assertEqual(True, self.verifyTrace(1, {'/>'}), "Prompt was not found")
        self.assertEqual(False, self.verifyTrace(1, {'hello'}, breakInFail=False), "Unexpected message was found")


    def case(self):
        pass

    def tearDown(self):
        pass

