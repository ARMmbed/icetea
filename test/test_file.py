# !/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable=missing-docstring

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


import os
import subprocess
import sys
import unittest

from test.dummy_dut import compile_dummy_dut
from icetea_lib.IceteaManager import IceteaManager


LIBPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".." + os.path.sep))
sys.path.append(LIBPATH)


class TestFileTestCase(unittest.TestCase):
    def setUp(self):
        self.ctm = IceteaManager()

        # variables for testing getLocalTestcases, parseLocalTestcases,
        # parseLocalTest, loadClass, printListTestcases

        self.testpath = os.path.abspath(os.path.dirname(__file__))
        self.root_path = os.getcwd()
        sys.path.append(self.testpath)
        self.testdir = os.path.join(self.testpath, 'testbase')
        #variables for testing run()

        compile_dummy_dut()

    def test_init_with_non_existing_file(self):  # pylint: disable=invalid-name
        proc = subprocess.Popen(['python', 'icetea.py', '-s', '--tc', 'test_cmdline',
                                 '--tcdir', 'examples', '--type', 'process', '--clean',
                                 '--bin', 'file.bin'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                cwd=self.root_path)
        out, error = proc.communicate()  # pylint: disable=unused-variable
        self.assertTrue(out.find(b"Binary not found") != -1,
                        "non exitent file error was not risen")
        self.assertEqual(proc.returncode, 0)

    @unittest.skipIf(sys.platform == 'win32', "windows doesn't support process test")
    def test_init_with_an_existing_file(self):
        bin_path = "test" + os.path.sep + "dut" + os.path.sep + "dummyDut"
        proc = subprocess.Popen(['python', 'icetea.py', '-s', '--tc', 'test_cmdline',
                                 '--tcdir', 'examples', '--type', 'process',
                                 '--clean', '--bin', bin_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                cwd=self.root_path)
        out, error = proc.communicate()  # pylint: disable=unused-variable
        self.assertTrue(out.find(b'test_cmdline |   pass') != -1, "exitent file was not accepted")
        self.assertEqual(proc.returncode, 0, "Icetea execution with existing file crashed")


if __name__ == '__main__':
    unittest.main()
