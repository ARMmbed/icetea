#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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

import unittest
import sys
import os
import subprocess

#Adds mbedtest/ to path, to allow importing using mbed_test.module form
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(libpath)
from mbed_test.mbedtestManagement import mbedtestManager, ExitCodes

class TestFileTestCase(unittest.TestCase):
    def setUp(self):
        self.ctm = mbedtestManager()

        #variables for testing getLocalTestcases, parseLocalTestcases, parseLocalTest, loadClass, printListTestcases

        self.testpath = os.path.abspath(os.path.dirname(__file__))
        self.root_path = os.getcwd()
        sys.path.append(self.testpath)
        self.testdir = os.path.join(self.testpath, 'testbase')
        #variables for testing run()

    def test_init_with_non_existing_file(self):
        proc = subprocess.Popen(['python', os.path.join(self.root_path, 'mbedtest.py'), '-s', '--tc', 'test_cmdline', '--tcdir', 'examples', '--type', 'process', '--bin', 'file.bin'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = proc.communicate()
        self.assertTrue(out.find('Given binary file.bin does not exist') != -1, "non exitent file error was not risen")
        self.assertEqual(proc.returncode, ExitCodes.EXIT_FAIL, "mbedtest execution with nonexisting file crashed")

    def test_init_with_an_existing_file(self):
        proc = subprocess.Popen(['python', os.path.join(self.root_path, 'mbedtest.py'), '-s', '--tc', 'test_cmdline', '--tcdir', 'examples', '--type', 'process', '--bin', os.path.join(self.testpath, 'dut/dummyDut')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = proc.communicate()
        self.assertTrue(out.find('test_cmdline') != -1, "test case was not accepted")
        self.assertTrue(out.find('pass') != -1, "verdict was not accepted")
        self.assertEqual(proc.returncode, ExitCodes.EXIT_SUCCESS, "mbedtest execution with existing file crashed")

    def tearDown(self):
        #Delete generated log files
        self.ctm.cleanLogs()

if __name__=='__main__':
    unittest.main()
