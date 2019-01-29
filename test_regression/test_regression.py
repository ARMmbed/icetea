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

import unittest
from subprocess import Popen, PIPE
import os


class TestRegression(unittest.TestCase):
    def test_regression_tests(self):
        icetea_verbose = '-vv'
        icetea_bin = "icetea"
        this_file_path = os.path.dirname(os.path.realpath(__file__))
        tc_name_list = ["test_async", "test_cli_init", "test_close_open", "test_cmdline", "test_multi_dut",
                        "test_cmd_resp", "test_serial_port"]
        test_result = []
        # start spawn tests
        for tc in tc_name_list:
            parameters = [icetea_bin, "--tcdir", this_file_path, "--tc", tc, "--failure_return_value", icetea_verbose]
            if tc == "test_cli_init":
                parameters.append("--reset")
            proc = Popen(parameters, stdout=PIPE)
            proc.communicate()

            test_result.append((tc, proc.returncode))

        raise_exception = False
        for tc, result in test_result:
            if result != 0:
                raise_exception = True
                print(tc + " failed with retCode: " + str(result))

        if raise_exception:
            raise Exception("Regression tests have failure")


if __name__ == '__main__':
    unittest.main()
