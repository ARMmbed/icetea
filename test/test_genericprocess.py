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

import subprocess
import unittest
import platform
import os

from icetea_lib.IceteaManager import ExitCodes


class GenericProcessTestcase(unittest.TestCase):
    @unittest.skipIf(
        platform.system() == "Windows",
        "Launching process in Windows ends in icetea warning"
        "\"This OS is not supporting select.poll() or select.kqueue()\"")
    def test_quick_process(self):
        # Run testcase
        icetea_cmd = ["python", "icetea.py",
                      "--clean",
                      "--silent",
                      "--failure_return_value",
                      "--tc", "test_quick_process",
                      "--tcdir", '"{}"'.format(os.path.join("test", "tests"))]

        # Shouldn't need to join the argument array,
        # but it doesn't work for some reason without it (Python 2.7.12).
        retcode = subprocess.call(args=" ".join(icetea_cmd), shell=True)

        # Check success
        self.assertEqual(
            retcode, ExitCodes.EXIT_SUCCESS,
            "Non-success returncode {} returned.".format(retcode))

    def tearDown(self):
        # Run with --clean to clean up
        subprocess.call(
            "python icetea.py --clean ",
            shell=True)


if __name__ == '__main__':
    unittest.main()
