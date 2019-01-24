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
# pylint: disable=missing-docstring
from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_cmdline",
                       title="Smoke test for command line interface",
                       status="released",
                       purpose="Verify Command Line Interface",
                       component=["cmdline"],
                       type="smoke",
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 1,
                                   "type": "hardware",
                                   "allowed_platforms": ['K64F']
                               }
                           }
                       }
                      )

    def setup(self):
        # nothing for now
        self.device = self.get_node_endpoint(1)  # pylint: disable=attribute-defined-outside-init

    def case(self):
        self.command(1, "echo hello world", timeout=5)
        self.device.command("help")

    def teardown(self):
        # nothing for now
        pass
