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
                       name="test_multiple_processes",
                       title="Example test for multiple processes",
                       status="released",
                       purpose="Demo process duts",
                       component=["cmdline"],
                       type="smoke",
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 10,
                                   "type": "process",
                                   "application": {
                                       "name": "dummyDut",
                                       "bin": "test/dut/dummyDut"
                                   }
                               },
                               '1': {
                                   "nick": "DUT1"
                               },
                               '2..10': {
                                   "nick": "DUT#{i}"
                               }
                           }}
                      )

    def setup(self):
        pass

    def case(self):
        self.command("DUT1", "echo hello DUT1")
        while True:
            try:
                self.command("*", "echo hello world")
            except KeyboardInterrupt:
                break

    def teardown(self):
        pass
