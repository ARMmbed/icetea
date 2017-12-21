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
    self.get_time(): return time interval between current time and test case start time.
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_get_time",
                       title="get_time() functions example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of Icetea get_time() functions",
                       component=["Icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 1, # devices number
                                    "type": "process", # "hardware" (by default) or "process"
                                    "application": {
                                        "bin": "build_path/build_full_name",  # build binary path
                                    }
                                }
                            }
                        }
                       )

    def case(self):
        # wait for 3 seconds
        self.delay(3)
        # get time
        self.logger.info("time interval between current time and test case start time: %s",
                         self.get_time())
