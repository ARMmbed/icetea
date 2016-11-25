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

__author__ = 'jaakuk03'
# These two lines are required when calling this test case directly without run.py
import sys
sys.path.append('../')

# Import Bench Class
from mbed_clitest.bench import Bench
class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_process_multidut_testcase",
                       title = "unittest exception in testcase",
                       status="development",
                       type="acceptance",
                       purpose = "dummy",
                       requirements={
                           "duts": {
                               '*': {
                                    "count":200,
                                    "type": "process",
                                    "application":{
                                        "name":"sample", "version": "1.0",
                                        "bin": "test/dut/dummyDut"
                                    }
                                }
                           }
                       }
        )

    def case(self):
        self.command("*", "Hello")