# pylint: disable=missing-docstring,broad-except,too-few-public-methods,too-many-instance-attributes
# pylint: disable=too-many-arguments,protected-access,too-many-branches,unused-argument
# pylint: disable=too-many-statements,no-member,wrong-import-order
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

import inspect
import unittest
import threading
import logging

import mock

from icetea_lib.bench import Bench, ReturnCodes
from icetea_lib.LogManager import BenchLoggerAdapter
from icetea_lib.Plugin.PluginManager import PluginManager
from icetea_lib.ResourceProvider.ResourceConfig import ResourceConfig
from icetea_lib.ResourceProvider.ResourceProvider import ResourceProvider
from icetea_lib.TestStepError import TestStepFail, TestStepError, InconclusiveError, TestStepTimeout
from test.tests.test_tcTearDown import Testcase as TearDownTest


class MockDut(object):
    def __init__(self):
        self.traces = ["this is test line 1", "this is test line 2"]


class TestingTestcase(Bench):
    """
    Testcase class for testing all exception cases
    """
    def __init__(self, teststep_fail=False, teststep_error=False,
                 name_error=False, value_error=False, kbinterrupt=False,
                 exception=False, inconclusive_error=False, in_setup=False,
                 in_case=False, in_teardown=False, test_step_timeout=False):
        self.teststep_error = teststep_error
        self.teststep_fail = teststep_fail
        self.name_error = name_error
        self.value_error = value_error
        self.kbinterrupt = kbinterrupt
        self.exception = exception
        self.in_setup = in_setup
        self.in_case = in_case
        self.in_teardown = in_teardown
        self.inconclusive = inconclusive_error
        self.test_step_timeout = test_step_timeout
        Bench.__init__(self,
                       name="ut_exception",
                       title="unittest exception in testcase",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       requirements={
                           "duts": {
                               '*': {  # requirements for all nodes
                                   "count": 0,
                               }
                           }}
                      )

    def raise_exc(self):
        if self.teststep_fail:
            raise TestStepFail("This is a TestStepFail")
        if self.teststep_error:
            raise TestStepError("This is a TestStepError")
        elif self.name_error:
            raise NameError("This is a NameError")
        elif self.value_error:
            raise ValueError("This is a ValueError")
        elif self.exception:
            raise Exception("This is a generic exception")
        elif self.kbinterrupt:
            raise KeyboardInterrupt()
        elif self.inconclusive:
            raise InconclusiveError("This will result in an inconclusive retcode.")
        elif self.test_step_timeout:
            raise TestStepTimeout("This is TestStepTimeout")

    def setup(self):
        self.args.silent = True
        if self.in_setup:
            self.raise_exc()

    def case(self):
        if self.in_case:
            self.raise_exc()

    def teardown(self):
        if self.in_teardown:
            self.raise_exc()


class ApiTestcase(Bench):
    """
    Testcase class for testing all exception cases
    """

    def __init__(self):
        Bench.__init__(self,
                       name="ut_apis",
                       title="unittest apis in testcase",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["UT"],
                       feature=["public apis"],
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 0,
                                   "allowed_platforms": ["TEST1"]
                               }
                           }
                       }
                      )
        self.expected_config = {'status': 'development',
                                'component': ["UT"],
                                'feature': ["public apis"],
                                'requirements': {
                                    'duts': {
                                        '*': {
                                            'count': 0,
                                            'application': {
                                                'bin': None
                                            },
                                            "allowed_platforms": ["TEST1"]
                                        }
                                    },
                                    'external': {
                                        'apps': []
                                    }
                                },
                                'name': 'ut_apis',
                                'title': 'unittest apis in testcase',
                                'compatible': {
                                    'framework': {
                                        'version': '>=1.0.0',
                                        'name': 'Icetea'
                                    }, 'hw': {
                                        'value': True
                                    }, 'automation': {
                                        'value': True}
                                }, 'purpose': 'dummy',
                                'type': 'acceptance',
                                'sub_type': None
                               }

    def setup(self):
        pass

    def raise_exc(self, step):  # pylint: disable=no-self-use
        print(step)
        raise TestStepFail(step)

    def case(self):
        if self.test_name != "ut_apis":
            self.raise_exc("test_name broken.")

        if self.config != self.expected_config:
            self.raise_exc("config getter broken.")
        self.expected_config["test"] = "test"
        self.config = self.expected_config

        if self.config != self.expected_config:
            self.raise_exc("config setter broken.")

        if self.env != {'sniffer': {'iface': 'Sniffer'}}:
            self.raise_exc("env broken.")

        if self.is_hardware_in_use():
            self.raise_exc("is_hardware_in_use broken.")

        if self.get_platforms() != list():
            self.raise_exc("get_platforms broken.")

        if self.get_serialnumbers():
            self.raise_exc("get_serialnumbers broken")

        if self.get_test_component() != self.expected_config["component"]:
            self.raise_exc("get_test_component broken")
        if len(self.get_allowed_platforms()) != 1 or self.get_allowed_platforms()[0] != "TEST1":
            self.raise_exc("Allowed platforms broken.")
        if self.status() != self.expected_config['status']:
            self.raise_exc("status broken")
        if self.type() != self.expected_config["type"]:
            self.raise_exc("type broken")
        if self.get_features_under_test() != self.expected_config["feature"]:
            self.raise_exc("features broken")
        if self.subtype() != self.expected_config["sub_type"]:
            self.raise_exc("subtype broken")
        if self.config != self.get_config():
            self.raise_exc("config not the same as get_config()")
        if self.skip() is not None:
            self.raise_exc("skip is not None")
        if self.skip_info() is not None:
            self.raise_exc("skip_info is not None")
        if self.skip_reason() != "":
            self.raise_exc("skip_reason is not empty")
        if self.check_skip() is not False:
            self.raise_exc("check_skip was not False")
        if self.get_tc_abspath(__file__) != __file__:
            self.raise_exc("get_tc_abspath file name did not match")
        self.set_config({"test": "test1"})
        if self.config != {"test": "test1"}:
            self.raise_exc("set_config broken.")
        self.set_config(self.expected_config)
        if self.dut_count() != 0:
            self.raise_exc("dut_count broken.")
        if self.get_dut_count() != 0:
            self.raise_exc("get_dut_count broken.")
        if not isinstance(self.resource_provider, ResourceProvider):
            self.raise_exc("resource_provider broken.")
        if not isinstance(self.resource_configuration, ResourceConfig):
            self.raise_exc("resource_configuration broken.")
        if self.duts != list():
            self.raise_exc("duts broken.")
        self.duts = ["D1"]
        if self.duts != ["D1"]:
            self.raise_exc("duts setter broken.")
        self.duts = []
        if self.dut_indexes:
            self.raise_exc("dut_indexes broken.")
        if not inspect.isgenerator(self.duts_iterator_all()):
            self.raise_exc("duts_iterator_all broken.")
        if not inspect.isgenerator(self.duts_iterator()):
            self.raise_exc("duts_iterator is broken.")
        if self.is_allowed_dut_index(1) is not False:
            self.raise_exc("is_allowed_dut_index broken")
        try:
            self.get_dut(1)
        except ValueError:
            pass
        except Exception:
            self.raise_exc("get_dut is broken.")
        try:
            self.get_node_endpoint(1)
        except ValueError:
            pass
        except Exception:
            self.raise_exc("get_node_endpoint is broken.")
        if not self.is_my_dut_index(1):
            self.raise_exc("is_my_dut_index is broken.")
        if self.dutinformations != list():
            self.raise_exc("dutinformations is broken.")
        if self.get_dut_nick(1) != "1":
            self.raise_exc("get_dut_nick is broken.")
        try:
            self.get_dut_nick("does not exists")
        except KeyError:
            pass
        except Exception:
            self.raise_exc("get_dut_nick is broken.")
        try:
            self.get_dut_index("does not exist")
        except ValueError:
            pass
        except Exception:
            self.raise_exc("get_dut_index is broken.")
        if not self.is_my_dut(1):
            self.raise_exc("is_my_dut broken.")
        if self.results is None:
            self.raise_exc("results broken.")
        if self.retcode != ReturnCodes.RETCODE_SUCCESS:
            self.raise_exc("retcode broken.")
        if self.wshark is not None:
            self.raise_exc("wshark default is broken.")
        if self.tshark_arguments != dict():
            self.raise_exc("tshark_arguments default is broken.")
        if self.sniffer_required is not False:
            self.raise_exc("sniffer_required is broken.")
        if not self.get_nw_log_filename().endswith("network.nw.pcap"):
            self.raise_exc("get_nw_log_filename broken.")
        if not isinstance(self.pluginmanager, PluginManager):
            self.raise_exc("pluginmanager broken.")
        logger = self.get_logger()
        if not isinstance(logger, BenchLoggerAdapter):
            self.raise_exc("get_logger broken.")
        if not isinstance(self.unknown, list):
            self.raise_exc("unknown broken.")
        old_list = self.unknown
        new_list = ["val1"]
        self.unknown = new_list
        if self.unknown is not new_list:
            self.raise_exc("unknown setter broken.")
        self.unknown = old_list
        old_res_conf = self.resource_configuration
        new_res_conf = ["val1"]
        self.resource_configuration = new_res_conf
        if self.resource_configuration is not new_res_conf:
            self.raise_exc("resource_configuration setter broken.")
        self.resource_configuration = old_res_conf
        if self.retcode != 0:
            self.raise_exc("retcode broken.")
        self.retcode = 1
        if self.retcode != 1:
            self.raise_exc("retcode setter broken")
        self.retcode = 0
        try:
            self.append_result()
        except Exception:
            self.raise_exc("append_result broken.")
        self.delay(0.1)
        if not isinstance(self.get_time(), float):
            self.raise_exc("get_time broken.")
        try:
            self.verify_trace_skip_fail(1, "a")
        except IndexError:
            pass
        except Exception:
            self.raise_exc("verify_trace_skip_fail broken.")
        retval = None
        try:
            retval = self.wait_for_async_response("a", "b")
        except AttributeError:
            pass
        except Exception:
            self.raise_exc("wait_for_async_response broken.")
        if retval is not None:
            self.raise_exc("wait_for_async_response broken.")
        try:
            self.execute_command(1, "a")
        except ValueError:
            pass
        except Exception:
            self.raise_exc("execute_command broken.")
        old_pm = self.pluginmanager
        new_pm = ["val1"]
        self.pluginmanager = new_pm
        if self.pluginmanager is not new_pm:
            self.raise_exc("pluginmanager setter broken")
        self.pluginmanager = old_pm
        if self.parse_response("a", "b"):
            self.raise_exc("parse_response broken.")
        if self.get_test_name() != "ut_apis":
            self.raise_exc("get_test_name broken.")
        if self.dut_count() != 0:
            self.raise_exc("dut_count broken.")
        try:
            self.init_duts()
        except Exception:
            self.raise_exc("init_duts broken")
        if self.name != "ut_apis":
            self.raise_exc("name broken.")
        mock_dut = mock.MagicMock()
        type(mock_dut).index = mock.PropertyMock(return_value=0)
        mock_dut.close_dut = mock.MagicMock()
        mock_dut.close_connection = mock.MagicMock()
        try:
            self.sync_cli("1", retries=0)
        except ValueError:
            pass
        else:
            self.raise_exc("sync_cli broken")

    def teardown(self):
        pass


class TestVerify(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.FATAL)

    def test_bench_apis(self):
        testcase = ApiTestcase()
        retcode = testcase.run()
        self.assertEqual(retcode, ReturnCodes.RETCODE_SUCCESS)

    def test_exceptions_in_case(self):
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(exception=True, in_case=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(teststep_fail=True, in_case=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(teststep_error=True, in_case=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(name_error=True, in_case=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(value_error=True, in_case=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(test_step_timeout=True, in_case=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        result = TestingTestcase(kbinterrupt=True, in_case=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES,
                        "Test return code not in inconclusive!")
        result = TestingTestcase(inconclusive_error=True, in_case=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES,
                        "Test return code not in inconclusive!")

    def test_verify_trace(self):
        bench = Bench()
        bench.duts.append(MockDut())
        bench.verify_trace(1, "this is test line 2")
        bench.verify_trace(1, ["this is test line 2"])
        with self.assertRaises(LookupError):
            bench.verify_trace(1, "This is not found in traces")

    def test_exceptions_in_rampup(self):
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(exception=True, in_setup=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(teststep_fail=True, in_setup=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(teststep_error=True, in_setup=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(name_error=True, in_setup=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(value_error=True, in_setup=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(kbinterrupt=True, in_setup=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        result = TestingTestcase(inconclusive_error=True, in_setup=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES,
                        "Test return code not in inconclusive!")

    @mock.patch("test.tests.test_tcTearDown.Testcase.teardown")
    def test_rampdown_called(self, mock_teardown):
        retcode = TearDownTest(teststepfail=True).run()
        self.assertEquals(retcode, 1001)
        self.assertTrue(mock_teardown.called)
        mock_teardown.reset_mock()

        retcode = TearDownTest(teststeperror=True).run()
        self.assertEquals(retcode, 1001)
        self.assertFalse(mock_teardown.called)

        retcode = TearDownTest(exception=True).run()
        self.assertEquals(retcode, 1001)
        self.assertFalse(mock_teardown.called)

        retcode = TearDownTest(teststeptimeout=True).run()
        self.assertEquals(retcode, 1001)
        self.assertFalse(mock_teardown.called)

        # Test tearDown is called when TestStepTimeout raised in test case
        retcode = TearDownTest(teststeptimeout_in_case=True).run()
        self.assertEquals(retcode, 1005)
        self.assertTrue(mock_teardown.called)
        mock_teardown.reset_mock()

        retcode = TearDownTest(name_error=True).run()
        self.assertEquals(retcode, 1001)
        self.assertFalse(mock_teardown.called)

        retcode = TearDownTest(value_error=True).run()
        self.assertEquals(retcode, 1001)
        self.assertFalse(mock_teardown.called)

    def test_exceptions_in_rampdown(self):
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(exception=True, in_teardown=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(teststep_fail=True, in_teardown=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(teststep_error=True, in_teardown=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(name_error=True, in_teardown=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(value_error=True, in_teardown=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        thread_count = threading.active_count()
        self.assertNotEqual(TestingTestcase(kbinterrupt=True, in_teardown=True).run(), 0,
                            "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        result = TestingTestcase(inconclusive_error=True, in_teardown=True).run()
        self.assertNotEqual(result, 0, "Test execution returned success retcode")
        self.assertEqual(thread_count, threading.active_count())
        self.assertTrue(result in ReturnCodes.INCONCLUSIVE_RETCODES,
                        "Test return code not in inconclusive!")

    def test_no_hanging_threads(self):
        thread_count = threading.active_count()
        TestingTestcase().run()
        self.assertEqual(thread_count, threading.active_count())

    @mock.patch('icetea_lib.TestBench.Resources.ResourceFunctions.resource_provider', create=True)
    @mock.patch('icetea_lib.TestBench.Commands.Commands.execute_command', create=True)
    def test_precmds_to_two_duts(self, mock_ec, mock_rp):
        # pylint: disable=no-self-use
        bench = Bench()
        bench._resource_provider = mock.Mock()
        bench.args = mock.MagicMock()
        bench.args.my_duts = mock.MagicMock(return_value=False)
        bench.execute_command = mock.MagicMock()
        mock_resconf = mock.Mock()
        mock_resconf.get_dut_configuration = mock.MagicMock(return_value=[{
            "pre_cmds": ["first", "second"]}, {"pre_cmds": ["first2", "second2"]}])
        bench.resource_configuration = mock_resconf
        mock_resconf.count_duts = mock.MagicMock(return_value=2)
        # Call using mangled name of __send_pre_commands method
        bench.send_pre_commands()
        mock_ec.assert_has_calls([mock.call(1, "first"),
                                  mock.call(1, "second"),
                                  mock.call(2, "first2"),
                                  mock.call(2, "second2")])

        bench.execute_command.reset_mock()
        # Test again with argument cmds
        bench.send_pre_commands("somecommand")
        mock_ec.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"),
                                  mock.call(2, "first2"), mock.call(2, "second2"),
                                  mock.call("*", "somecommand")])

    @mock.patch('icetea_lib.TestBench.Resources.ResourceFunctions.resource_provider', create=True)
    @mock.patch('icetea_lib.TestBench.Commands.Commands.execute_command', create=True)
    def test_postcmds_to_two_duts(self, mock_ec, mock_rp):
        # pylint: disable=no-self-use
        bench = Bench()
        bench._resource_provider = mock.MagicMock()
        bench.execute_command = mock.MagicMock()
        bench.args = mock.MagicMock()
        bench.logger = mock.MagicMock()
        type(bench.args).my_duts = mock.PropertyMock(return_value=False)
        type(bench.args).pause_when_external_dut = mock.MagicMock(return_value=False)
        bench._resources.init(mock.MagicMock())
        bench._commands.init()
        mock_dut1 = mock.MagicMock()
        type(mock_dut1).index = mock.PropertyMock(return_value=1)
        mock_dut2 = mock.MagicMock()
        type(mock_dut2).index = mock.PropertyMock(return_value=2)
        bench._resources.duts = [mock_dut1, mock_dut2]
        mock_resconf = mock.Mock()
        mock_resconf.get_dut_configuration = mock.MagicMock(
            return_value=[{"post_cmds": ["first", "second"]}, {"post_cmds": ["first2", "second2"]}])
        bench.resource_configuration = mock_resconf
        mock_resconf.count_duts = mock.MagicMock(return_value=2)
        bench.send_post_commands()
        mock_ec.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"),
                                  mock.call(2, "first2"), mock.call(2, "second2")])

        mock_ec.reset_mock()
        # Test again with argument cmds
        bench.send_post_commands("somecommand")
        mock_ec.assert_has_calls([mock.call(1, "first"), mock.call(1, "second"),
                                  mock.call(2, "first2"), mock.call(2, "second2"),
                                  mock.call("*", "somecommand")])

    def test_reset_duts(self):
        bench = Bench()
        bench.logger = mock.MagicMock()
        bench.args = mock.MagicMock()
        bench._resources._args = bench.args
        type(bench.args).my_duts = mock.PropertyMock(return_value=False)
        type(bench.args).pause_when_external_dut = mock.MagicMock(return_value=False)
        bench._resources.init(mock.MagicMock())
        mock_dut = mock.MagicMock()
        dutconf = {"reset.return_value": True, "initCLI.return_value": True}
        mock_dut.configure_mock(**dutconf)
        mock_dutrange = range(2)
        mock_duts = [mock_dut, mock_dut]
        bench.duts = mock_duts
        # TODO: This mocking does not work somehow
        with mock.patch.object(bench.resource_configuration, "get_dut_range",
                               return_value=mock_dutrange):
            with mock.patch.object(bench, "is_my_dut_index", return_value=True):
                for method in ["hard", "soft", None]:
                    bench.args.reset = method
                    bench.reset_dut()
                    mock_dut.reset.assert_called_with(method)
                    self.assertEqual(mock_dut.reset.call_count, 2)
                    mock_dut.reset.reset_mock()

    def test_check_skip(self):
        testcase = TestingTestcase()
        testcase.config["requirements"]["duts"]["*"]["type"] = "process"
        testcase.config["execution"] = {"skip": {"value": True, "only_type": "process"}}
        self.assertEqual(testcase.run(), -1)
        self.assertTrue(testcase.get_result().skipped())

    def test_check_skip_invalid_platform(self):  # pylint: disable=invalid-name
        testcase = TestingTestcase()
        testcase.config["requirements"]["duts"]["*"]["allowed_platforms"] = ["K64F"]
        testcase.config["execution"] = {"skip": {"value": True, "platforms": ["K64F", "K65F"]}}
        self.assertEqual(testcase.run(), 0)
        self.assertFalse(testcase.get_result().skipped())

    def test_check_skip_valid_platform(self):  # pylint: disable=invalid-name
        testcase = TestingTestcase()
        testcase.config["requirements"]["duts"]["*"]["allowed_platforms"] = ["K64F"]
        testcase.config["requirements"]["duts"]["*"]["platform_name"] = "K64F"
        testcase.config["execution"] = {"skip": {"value": True, "platforms": ["K64F"]}}
        self.assertEqual(testcase.run(), -1)
        self.assertTrue(testcase.get_result().skipped())

    def test_check_no_skip(self):
        testcase = TestingTestcase()
        testcase.config["execution"] = {"skip": {"value": True}}
        self.assertEqual(testcase.run(), 0)
        self.assertFalse(testcase.get_result().skipped())

    def test_create_new_result(self):
        test_data = dict()
        test_data["reason"] = "this is a reason"
        result = Bench.create_new_result("fail", 1, 10, test_data)
        self.assertTrue(result.failure)

    def test_create_and_add_new_result(self):
        test_data = dict()
        test_data["reason"] = "this is a reason"
        bench = Bench()
        result = bench.add_new_result("fail", 1, 10, test_data)
        self.assertEqual(len(bench.results), 1)
        self.assertEqual(result.fail_reason, "this is a reason")


if __name__ == '__main__':
    unittest.main()
