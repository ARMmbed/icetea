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


class Testcase(Bench):
    """
    Test case for testing skipping test cases.
    """
    def __init__(self):
        Bench.__init__(self,
                       name="skipcasetest",
                       title="Testcase test file",
                       status="development",
                       purpose="dummy",
                       component=["None"],
                       type="compatibility",
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 0
                               }
                           }
                       },
                       execution={
                           "skip": {
                               "value": True,
                               "only_type": "process",
                               "reason": "Because"
                           }
                       }
                      )

    def case(self):  # pylint: disable=missing-docstring
        pass
