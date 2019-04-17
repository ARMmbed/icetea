"""
Copyright 2019 ARM Limited
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

from icetea_lib.TestBench.Bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_serial",
                       title="Example test for using serial type duts.",
                       status="released",
                       purpose="Act as an example of defining a serial type dut.",
                       component=["cmdline"],
                       type="smoke",
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 1,
                                   "type": "serial"
                               },
                               "1": {"serial_port": "/dev/ttyACM0"}
                           }
                       }
                      )

    def setup(self):
        pass

    def case(self):
        self.command(1, "echo 'Hello World'")

    def teardown(self):
        pass
