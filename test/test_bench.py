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
import mock
import threading
import logging


from icetea_lib.bench import Bench, ReturnCodes
from icetea_lib.TestStepError import TestStepFail, TestStepError, InconclusiveError, TestStepTimeout
from test.tests.test_tcTearDown import Testcase as TearDownTest


class MockDut:
    def __init__(self):
        self.traces = ["this is test line 1", "this is test line 2"]


class TestingTestcase(Bench):
    """
    Testcase class for testing all exception cases
    """
    def __init__(self, testStepFail=False, testStepError=False,
                 nameError=False, valueError=False, kbinterrupt=False,
                 exception=False, inconclusive_error=False, inRampUp=False,
                 inCase=False, inRampDown=False, test_step_timeout=False):
        self.testStepError = testStepError
        self.testStepFail = testStepFail
        self.nameError = nameError
        self.valueError = valueError
        self.kbinterrupt = kbinterrupt
        self.exception = exception
        self.inRampUp = inRampUp
        self.inCase = inCase
        self.inRampDown = inRampDown
        self.inconclusive = inconclusive_error
        self.test_step_timeout = test_step_timeout
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
        elif self.inconclusive:
            raise InconclusiveError("This will result in an inconclusive retcode.")
        elif self.test_step_timeout:
            raise TestStepTimeout("This is TestStepTimeout")

    def rampUp(self):
        self.args.silent = True
        if self.inRampUp:
            self.raiseExc()

    def case(self):
        if self.inCase:
            self.raiseExc()

    def rampDown(self):
        if self.inRampDown:
            self.raiseExc()

class TestVerify(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.FATAL)

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
        self.assertNotEqual( TestingTestcase(test_step_timeout=True, inCase=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        result = TestingTestcase(kbinterrupt=True, inCase=True).run()
        self.assertNotEqual( result, 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES, "Test return code not in inconclusive!")
        result = TestingTestcase(inconclusive_error=True, inCase=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES, "Test return code not in inconclusive!")

    def test_verifyTrace(self):
        b = Bench()
        b.duts.append(MockDut())
        b.verify_trace(1, "this is test line 2")
        b.verify_trace(1, ["this is test line 2"])
        with self.assertRaises(LookupError) as e:
            b.verify_trace(1, "This is not found in traces")

    def test_exceptions_in_rampup(self):
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(exception=True, inRampUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepFail=True, inRampUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepError=True, inRampUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(nameError=True, inRampUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(valueError=True, inRampUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(kbinterrupt=True, inRampUp=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        result = TestingTestcase(inconclusive_error=True, inRampUp=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES, "Test return code not in inconclusive!")

    @mock.patch("test.tests.test_tcTearDown.Testcase.teardown")
    def test_rampDown_called(self, mock_tearDown):
        retCode = TearDownTest(testStepFail=True).run()
        self.assertEquals(retCode, 1001)
        self.assertTrue(mock_tearDown.called)
        mock_tearDown.reset_mock()

        retCode = TearDownTest(testStepError=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)

        retCode = TearDownTest(exception=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)

        retCode = TearDownTest(testStepTimeout=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)

        # Test tearDown is called when TestStepTimeout raised in test case
        retCode = TearDownTest(testStepTimeoutInCase=True).run()
        self.assertEquals(retCode, 1005)
        self.assertTrue(mock_tearDown.called)
        mock_tearDown.reset_mock()

        retCode = TearDownTest(nameError=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)

        retCode = TearDownTest(valueError=True).run()
        self.assertEquals(retCode, 1001)
        self.assertFalse(mock_tearDown.called)

    def test_exceptions_in_rampdown(self):
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(exception=True, inRampDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepFail=True, inRampDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(testStepError=True, inRampDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(nameError=True, inRampDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(valueError=True, inRampDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        n = threading.active_count()
        self.assertNotEqual( TestingTestcase(kbinterrupt=True, inRampDown=True).run(), 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        result = TestingTestcase(inconclusive_error=True, inRampDown=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(n, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES, "Test return code not in inconclusive!")

    def test_no_hanging_threads(self):
        n = threading.active_count()
        TestingTestcase().run()
        self.assertEqual(n, threading.active_count())

    @mock.patch('icetea_lib.bench.resource_provider', create=True)
    @mock.patch('icetea_lib.bench.execute_command', create=True)
    def test_precmds_to_two_duts(self, mock_ec, mock_rp):
        tc = Bench()
        tc._resource_provider = mock.Mock()
        tc.execute_command = mock.MagicMock()
        mock_resconf = mock.Mock()
        mock_resconf.get_dut_configuration = mock.MagicMock(return_value=[{"pre_cmds": ["first", "second"]}, {"pre_cmds": ["first2", "second2"]}])
        tc.resource_configuration = mock_resconf
        # Call using mangled name of __send_pre_commands method
        tc._Bench__send_pre_commands()
        tc.execute_command.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"), mock.call(2, "first2"), mock.call(2, "second2")])

        tc.execute_command.reset_mock()
        # Test again with argument cmds
        tc._Bench__send_pre_commands("somecommand")
        tc.execute_command.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"),
                                            mock.call(2, "first2"), mock.call(2, "second2"),
                                            mock.call("*", "somecommand")])

    @mock.patch('icetea_lib.bench.resource_provider', create=True)
    @mock.patch('icetea_lib.bench.execute_command', create=True)
    def test_postcmds_to_two_duts(self, mock_ec, mock_rp):
        tc = Bench()
        tc._resource_provider = mock.Mock()
        tc.execute_command = mock.MagicMock()
        mock_resconf = mock.Mock()
        mock_resconf.get_dut_configuration = mock.MagicMock(
            return_value=[{"post_cmds": ["first", "second"]}, {"post_cmds": ["first2", "second2"]}])
        tc.resource_configuration = mock_resconf
        # Call using mangled name of __send_pre_commands method
        tc._Bench__send_post_commands()
        tc.execute_command.assert_has_calls(
            [mock.call(1, "first"), mock.call(1, "second"), mock.call(2, "first2"), mock.call(2, "second2")])

        tc.execute_command.reset_mock()
        # Test again with argument cmds
        tc._Bench__send_post_commands("somecommand")
        tc.execute_command.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"),
                                            mock.call(2, "first2"), mock.call(2, "second2"),
                                            mock.call("*", "somecommand")])

    def test_reset_duts(self):
        bench = Bench()
        mock_dut = mock.MagicMock()
        dutconf = {"reset.return_value": True, "initCLI.return_value": True}
        mock_dut.configure_mock(**dutconf)
        mock_dutrange = range(2)
        mock_duts = [mock_dut, mock_dut]
        bench.duts = mock_duts
        with mock.patch.object(bench, "get_dut_range", return_value=mock_dutrange):
            with mock.patch.object(bench, "is_my_dut", return_value=True):
                for method in ["hard", "soft", None]:
                    bench.args.reset = method
                    bench.reset_dut()
                    mock_dut.reset.assert_called_with(method)
                    self.assertEquals(mock_dut.reset.call_count, 2)
                    mock_dut.reset.reset_mock()

    def test_check_skip(self):
        tc = TestingTestcase()
        tc.config["requirements"]["duts"]["*"]["type"] = "process"
        tc.config["execution"] = {"skip": {"value": True, "only_type": "process"}}
        self.assertEqual(tc.run(), -1)
        self.assertTrue(tc.get_result().skipped())

    def test_check_skip_invalid_platform(self):
        tc = TestingTestcase()
        tc.config["requirements"]["duts"]["*"]["allowed_platforms"] = ["K64F"]
        tc.config["execution"] = {"skip": {"value": True, "platforms": ["K64F", "K65F"]}}
        self.assertEqual(tc.run(), 0)
        self.assertFalse(tc.get_result().skipped())

    def test_check_skip_valid_platform(self):
        tc = TestingTestcase()
        tc.config["requirements"]["duts"]["*"]["allowed_platforms"] = ["K64F"]
        tc.config["requirements"]["duts"]["*"]["platform_name"] = "K64F"
        tc.config["execution"] = {"skip": {"value": True, "platforms": ["K64F"]}}
        self.assertEqual(tc.run(), -1)
        self.assertTrue(tc.get_result().skipped())

    def test_check_no_skip(self):
        tc = TestingTestcase()
        tc.config["execution"] = {"skip": {"value": True}}
        self.assertEqual(tc.run(), 0)
        self.assertFalse(tc.get_result().skipped())

    def test_config_validation_bin_not_defined(self):
        duts_cfg = [{}]
        logger = logging.getLogger('unittest')
        logger.addHandler(logging.NullHandler())
        self.assertEqual(Bench._validate_dut_configs(duts_cfg, logger), None)

    def test_config_validation_bin_defined_but_not_exists(self):
        duts_cfg = [{"application": {"bin": "not.exist"}}]
        logger = logging.getLogger('unittest')
        logger.addHandler(logging.NullHandler())
        with self.assertRaises(EnvironmentError) as e:
            Bench._validate_dut_configs(duts_cfg, logger)

    def test_config_validation_bin_defined(self):
        duts_cfg = [{"application": {"bin": "./test/test_bench.py"}}]
        logger = logging.getLogger('unittest')
        logger.addHandler(logging.NullHandler())
        self.assertEqual(Bench._validate_dut_configs(duts_cfg, logger), None)

    def test_create_new_result(self):
        test_data = dict()
        test_data["reason"] = "this is a reason"
        result = Bench.create_new_result("fail", 1, 10, test_data)
        self.assertTrue(result.failure)

    def test_create_and_add_new_result(self):
        test_data = dict()
        test_data["reason"] = "this is a reason"
        bench = Bench()
        bench.add_new_result("fail", 1, 10, test_data)
        self.assertEqual(len(bench._results), 1)


if __name__=='__main__':
    unittest.main()
