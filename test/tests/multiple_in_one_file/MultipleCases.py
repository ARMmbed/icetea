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

from icedtea_lib.bench import Bench, TestStepFail
from icedtea_lib.tools.tools import test_case

"""
    Example testcase file that implements multiple cases that share a setUp and tearDown function.
"""


class MultipleTestcase(Bench):
    def __init__(self, **kwargs):
        tc_args = {
            'title': "dummy",
            'status': "unknown",
            'type': "functional",
            'purpose': "dummy",
            'requirements': {
                "duts": {
                    '*': { #requirements for all nodes
                        "count":0,
                    }
                }
            }
        }
        tc_args.update(kwargs)
        Bench.__init__(self, **tc_args)

    def setUp(self):
        pass

    def tearDown(self):
        pass


@test_case(MultipleTestcase, name="passing_case")
def passcase(test_env):
    pass

@test_case(MultipleTestcase, name="fail_case")
def fail_case(test_env):
    raise TestStepFail("This must fail!")