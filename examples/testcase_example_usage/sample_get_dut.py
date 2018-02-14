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
Icetea test case additional function usage example.

function:
    self.get_dut(index):  Get a handle to a DUT with index. There are functions can be accessed using DUT handle.


DUT public API:
    Please see tc_api.md section [DUT public API] for more details.

    1. open_connection(): Open the communication channel to DUT (eg. serial port).
                         By default testcase automatically calls this during rampup.

    2. close_connection(): Close the communication channel to DUT (eg. serial port)

    3. comport: returns serial port name or path (eg. COM0 or /dev/ttyACM0), If DUT has serial communication channel.
                 Please Note: only local hardware has comport!
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_get_dut",
                       title="get_dut(index) functions example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of Icetea get_dut(index) functions",
                       component=["Icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 1, # devices number
                                    "type": "hardware", # "hardware" (by default) or "process"
                                    "application": {
                                        "bin": "build_path/build_full_name",  # build binary path
                                    }
                                }
                            }
                        }
                       )

    def case(self):
        # Close connection
        self.get_dut(1).close_connection()

        # wait a second
        self.delay(1)

        # open connection
        self.get_dut(1).open_connection()

        # get port name or path
        if self.get_dut(1).comport:
            self.logger.info("DUT serial port is %s", self.get_dut(1).comport)
