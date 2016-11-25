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
sys.path.append("../")
import psutil

from tests.crash_testcase import Testcase as CrashTestcase
from tests.exception_testcase import Testcase as ExceptionTestcase
from mbed_test.bench import ReturnCodes

def get_processes_by_name(name):
    procs = []
    for proc in psutil.process_iter():
        if name in proc.name():
            procs.append(proc)
    return procs

class TestVerify(unittest.TestCase):

    def test_pass(self):
        retcode = ExceptionTestcase().run()
        self.assertEqual( retcode, ReturnCodes.RETCODE_SUCCESS, "Test execution returned fail retcode %s" % retcode)

    def test_crash_fail(self):
        retcode = CrashTestcase(inRampUp=True).run()
        self.assertNotEqual( retcode, 0, "Crash in rampUp returned wrong retcode %s" % retcode)
        retcode = CrashTestcase(inCase=True).run()
        self.assertNotEqual( retcode, 0, "Crash in testcase returned wrong retcode %s" % retcode)
        retcode = CrashTestcase(inRampUp=True).run()
        self.assertNotEqual( retcode, 0, "Crash in rampDown returned wrong retcode %s" % retcode)

    def test_testStepFail_inRampUp(self):
        self.assertNotEqual( ExceptionTestcase(testStepFail=True, inRampUp=True).run(), 0, "Test execution returned success retcode")

    def test_testStepFail_inTc(self):
        self.assertNotEqual( ExceptionTestcase(testStepFail=True, inCase=True).run(), 0, "Test execution returned success retcode")

    def test_testStepFail_inRampDown(self):
        self.assertNotEqual( ExceptionTestcase(testStepFail=True, inRampDown=True).run(), 0, "Test execution returned success retcode")

    def test_multiple_sequential_testcases(self):
        ExceptionTestcase().run()
        self.assertEqual(get_processes_by_name("dummyDut"), [])
        ExceptionTestcase().run()
        self.assertEqual(get_processes_by_name("dummyDut"), [])
        ExceptionTestcase().run()
        self.assertEqual(get_processes_by_name("dummyDut"), [])
        ExceptionTestcase().run()
        self.assertEqual(get_processes_by_name("dummyDut"), [])