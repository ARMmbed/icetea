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

import sys
from mbed_clitest.bench import Bench

class Testcase(Bench):

    def __init__(self):
        Bench.__init__(self, name="subsubsubdirtest",
                        title="Level 3 testcase test file",
                        status="broken",  #allowed values: released, development, maintenance, broken, unknown
                        purpose="dummy",
                        component=["None"],
                        type="regression", # allowed values: installation, compatibility, smoke, regression, acceptance, alpha, beta, destructive, performance
                        requirements={
                            "duts": {
                                '*': { #requirements for all nodes
                                    "count": 0
                                    }
                                }
                            }
                        )

    def case(self):
        pass
