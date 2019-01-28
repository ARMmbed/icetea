# pylint: disable=missing-docstring
# -*- coding: utf-8 -*-

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

import time
from icetea_lib.bench import Bench
from icetea_lib.bench import TestStepFail


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(
            self,
            name="test_quick_process",
            type="smoke",
            requirements={
                "duts": {
                    "*": {
                        "count": 1,
                        "type": "process"
                    },
                    1: {
                        "application": {
                            "bin": "/bin/echo",
                            "bin_args": ["If this is found, the test passed"],
                            "init_cli_cmds": [],
                            "post_cli_cmds": []
                        }
                    }
                }
            }
        )

    def setup(self):  # pylint: disable=method-hidden
        pass

    def case(self):
        time_start = time.time()
        result = False
        while (time.time() - time_start) < 10.0 and result is False:
            result = self.verify_trace(
                0, "If this is found, the test passed", False)
            time.sleep(1.0)
        if result is False:
            raise TestStepFail("Didn't get trace")

    def teardown(self):  # pylint: disable=method-hidden
        pass
