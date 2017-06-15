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
                       name="test_cmdline",
                       title = "Smoke test for command line interface",
                       status = "released",
                       purpose = "Verify Command Line Interface",
                       component=["cmdline"],
                       type="smoke", # allowed values: installation, compatibility, smoke, regression, acceptance, alpha, beta, destructive, performance
                       requirements={
                           "duts": {
                               '*': { #requirements for all nodes
                                    "count":1,
                                    "type": "hardware",
                                    "allowed_platforms": ["SAM4E", 'NRF51_DK', 'K64F'],
                                    "application":{ "name":"generalTestApplication", "version": "1.0"}
                               }
                           }}
        )

    def setUp(self):
        # nothing for now
        self.device = self.get_node_endpoint(1)


    def case(self):
        self.command(1, "echo hello world", timeout=5)
        #self.openPutty(1)
        self.device.command("help")

        #self.command(1, "retcode 1", reportCmdFail=False)

        #self.verifyTrace(1, ['version'])
        #self.verifyTrace(1, ['shouldnt be there'], False)
        pass

    def tearDown(self):
        # nothing for now
        pass
