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
import mock
import subprocess
import threading
import logging
import sys
import os

# Add mbedtest/ to path, to allow importing using mbed_test.module form
libpath = '/'.join(os.path.abspath(sys.modules[__name__].__file__).split('/')[:-2])
sys.path.append(libpath)

from mbed_test.bench import Bench
from mbed_test.TestStepError import TestStepError
from mbed_test.TestStepError import TestStepFail
from mbed_test.TestStepError import TestStepTimeout
from testcases.test_tcTearDown import Testcase as TearDownTest

"""
Testcase class for testing all exception cases
"""
class TestingTestcase(Bench):
    def __init__(self, testStepFail=False, testStepError=False, nameError=False, valueError=False, kbinterrupt=False, exception=False, inSetUp=False, inCase=False, inTearDown=False):
        self.testStepError = testStepError
        self.testStepFail = testStepFail
        self.nameError = nameError
        self.valueError = valueError
        self.kbinterrupt = kbinterrupt
        self.exception = exception
        self.inSetUp = inSetUp
        self.inCase = inCase
        self.inTearDown = inTearDown
        Bench.__init__(self,
                       name="ut_exception",
                       title = "unittest exception in testcase",
                       status="development",
                       type="acceptance",
                       purpose = "dummy",
                       requirements={
                           "duts": {
                               '*': { #requirements for all nodes
                                    "count":0,
                                }
                           }}
        )


    def raiseExc(self):

        if self.testStepFail:
            raise TestStepFail("This is a TestStepFail")
        if self.testStepError:
            raise TestStepError("This is a TestStepError")
        elif self.nameError:
            raise NameError("This is a NameError")
        elif self.valueError:
            raise ValueError("This is a ValueError")
        elif self.exception:
            raise Exception( "This is a generic exception" )
        elif self.kbinterrupt:
            raise KeyboardInterrupt()

    def setUp(self):
        self.args.silent = True
        if self.inSetUp:
            self.raiseExc()

    def case(self):
        if self.inCase:
            self.raiseExc()

    def tearDown(self):
        if self.inTearDown:
            self.raiseExc()

def mock_initialize():
    m = mock.Mock()
    args =  {"side_effect": [Exception, 0, 0, 0, 0, 0, 0, 0]}
    m.configure_mock(**args)
    return m

def mock_setUpBench():
    m = mock.Mock()
    args =  {"side_effect": [EnvironmentError, TestStepTimeout, TestStepFail, NameError, KeyboardInterrupt, SystemExit,  Exception, 0]}
    m.configure_mock(**args)
    return m

class TestVerify(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.FATAL)

    #def test_mbedtest(self):
    #    proc = subprocess.Popen(['python', 'mbedtest.py', '-s', '--tc', 'dummy', '--tcdir'], cwd="./")
    #    proc.communicate()
    #    self.assertEqual( proc.returncode, 0, "Test execution didn't return success retcode")

    def test_exceptions_in_case(self):
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(exception=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepFail=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepError=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(nameError=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(valueError=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(kbinterrupt=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())

    def test_exceptions_in_setup(self):
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(exception=True, inSetUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepFail=True, inSetUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepError=True, inSetUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(nameError=True, inSetUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(valueError=True, inSetUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(kbinterrupt=True, inSetUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())

    @mock.patch("testcases.test_tcTearDown.Testcase.tearDown")
    def test_rampDown_called(self, mock_tearDown):
        retCode = TearDownTest(testStepFail=True).run()
        self.assertEquals(retCode, 1001)
        self.assertTrue(mock_tearDown.called)
        mock_tearDown.reset_mock()
        retCode = TearDownTest(testStepError=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)
        mock_tearDown.reset_mock()
        retCode = TearDownTest(exception=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)
        retCode = TearDownTest(testStepTimeout=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)
        mock_tearDown.reset_mock()
        retCode = TearDownTest(nameError=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)
        mock_tearDown.reset_mock()
        retCode = TearDownTest(valueError=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)


    def test_exceptions_in_rampdown(self):
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(exception=True, inTearDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepFail=True, inTearDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepError=True, inTearDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(nameError=True, inTearDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(valueError=True, inTearDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(kbinterrupt=True, inTearDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())

    def test_no_hanging_threads(self):
        n = threading.active_count()
        TestingTestcase().run()
        self.assertEqual(n, threading.active_count())

    @mock.patch('mbed_test.bench.resource_provider', create=True)
    @mock.patch('mbed_test.bench.executeCommand', create=True)
    def test_precmds_to_two_duts(self, mock_ec, mock_rp):
        tc = Bench()
        tc.resource_provider = mock.Mock()
        tc.executeCommand = mock.MagicMock()
        mock_resconf = mock.Mock()
        mock_resconf.get_dut_configuration = mock.MagicMock(return_value=[{"pre_cmds": ["first", "second"]}, {"pre_cmds": ["first2", "second2"]}])
        tc.resource_provider.get_resource_configuration = mock.MagicMock(return_value=mock_resconf)
        # Call using mangled name of __send_pre_commands method
        tc._Bench__send_pre_commands()
        tc.executeCommand.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"), mock.call(2, "first2"), mock.call(2, "second2")])

        tc.executeCommand.reset_mock()
        # Test again with argument cmds
        tc._Bench__send_pre_commands("somecommand")
        tc.executeCommand.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"),
                                            mock.call(2, "first2"), mock.call(2, "second2"),
                                            mock.call("*", "somecommand")])


    @mock.patch('mbed_test.bench.resource_provider', create=True)
    @mock.patch('mbed_test.bench.executeCommand', create=True)
    def test_run_exceptions(self, mock_ec, mock_rp):
        tc = Bench()
        with mock.patch.object(tc, "_Bench__initialize", mock_initialize()):
            self.assertGreater(tc.run(), 0, "Success retcode returned!")
            with mock.patch.object(tc, "_Bench__setUpBench", mock_setUpBench()):
                with mock.patch.object(tc, "_Bench__tearDownBench", mock.Mock()):
                    for i in range(0, 7):
                        self.assertGreater(tc.run(), 0, "Success retcode returned!")




if __name__=='__main__':
    unittest.main()

