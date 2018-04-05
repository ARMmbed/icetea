# pylint: disable=missing-docstring,protected-access,unused-argument

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


import argparse
import json
import os
import unittest
from jsonmerge import merge

import mock

from icetea_lib.TestSuite.TestSuite import TestSuite, SuiteException, TestStatus
from icetea_lib.TestSuite.TestcaseContainer import DummyContainer
from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList
from icetea_lib.DeviceConnectors.DutInformation import DutInformation
from icetea_lib.build.build import Build


def mock_get_suite_tcs(arg1, arg2):
    return None

def mock_get_local_tcs(tcpath):
    return []

def mock_create_filter(tc):
    return -1

def mock_parse_local_tcs(arg1, arg2):
    return []


class TestSuiteTestcase(unittest.TestCase):

    def setUp(self):
        with open(os.path.join("./icetea_lib", 'tc_schema.json')) as data_file:
            self.tc_meta_schema = json.load(data_file)
        testpath = os.path.dirname(os.path.abspath(__file__))
        self.testdir = os.path.join(testpath, 'testbase')
        self.args_noprint = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None, nobuf=None,
            pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='all', tc_cfg=None, tcdir=self.testdir,
            testtype=False, type=None, platform_filter=None,
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None,
            verbose=False, repeat=0, feature=None, json=False)
        self.args_tc_no_exist = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None, nobuf=None,
            pause_when_external_dut=False, platform_filter=None,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='does_not_exist', tc_cfg=None, tcdir=self.testdir,
            testtype=False, type=None, subtype=None, use_sniffer=False,
            valgrind=False, valgrind_tool=None, verbose=False, repeat=0, feature=None,
            json=False)
        self.args_suite = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None,
            kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None,
            pause_when_external_dut=False, platform_filter=None,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False,
            status=False, suite="dummy_suite.json", tc=None, tc_cfg=None,
            tcdir="examples", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None,
            verbose=False, repeat=2, feature=None, suitedir="./test/suites", json=False)
        self.args_tc = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False, platform_filter=None,
            status=False, suite=None, tc="test_cmdline", tc_cfg=None,
            tcdir="examples", testtype=False, type="process",
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False, repeat=0, feature=None,
            suitedir="./test/suites", forceflash_once=True, forceflash=False,
            stop_on_failure=False, json=False)

    def test_create_suite_suitefile_some_not_found(self):
        suit = TestSuite(args=self.args_suite)
        self.assertEqual(len(suit), 5)

    def test_create_suite_list_success(self):
        suit = TestSuite(args=self.args_noprint)
        self.assertEqual(len(suit), 7, "Suite length ({}) did not match expected length of {}!".format(len(suit), 7))
        self.assertEqual(suit.status, TestStatus.READY)

    def test_create_suite_suitefile_fail(self):
        self.args_suite.suite = "malformed_suite.json"
        with self.assertRaises(SuiteException):
            suite = TestSuite(args=self.args_suite)

    def test_create_suite_list_empty(self):
        suit = TestSuite(args=self.args_tc_no_exist)
        self.assertEqual(len(suit), 1)

    def test_prepare_suite_success(self):
        self.args_suite.suite = "working_suite.json"
        suit = TestSuite(args=self.args_suite)
        self.assertEqual(suit.status, TestStatus.READY)
        tc = suit.get_testcases().get(0)
        self.assertEqual(tc.status, TestStatus.READY)

    def test_prepare_suite_merge_configs(self):
        self.args_suite.suite = "working_suite.json"
        suit = TestSuite(args=self.args_suite)
        tcs = suit.get_testcases()
        self.assertEqual(len(tcs), 2)
        tc = tcs.get(1)
        sconf = tc.get_suiteconfig()
        with open("test/suites/working_suite.json") as f:
            suite = json.load(f)
            cases = suite.get("testcases")
            case2 = cases[1]
            self.assertDictEqual(case2.get("config"), sconf)
        conf = tc.get_final_config()
        self.assertDictEqual(merge(tc.get_instance().get_config(), sconf), conf)

    def test_prepare_suite_merge_configs_missing_tc(self):
        self.args_suite.suite = "suite_missing_one.json"
        suit = TestSuite(args=self.args_suite)
        tcs = suit.get_testcases()
        self.assertEqual(len(tcs), 3)
        tc = tcs.get(2)
        sconf = tc.get_suiteconfig()
        with open("test/suites/suite_missing_one.json") as f:
            suite = json.load(f)
            cases = suite.get("testcases")
            case2 = cases[2]
            self.assertDictEqual(case2.get("config"), sconf)
        conf = tc.get_final_config()
        self.assertDictEqual(merge(tc.get_instance().get_config(), sconf), conf)
        self.assertTrue(isinstance(tcs.get(1), DummyContainer))
        all_duts = conf.get("requirements").get("duts").get("*")
        self.assertIsNotNone(all_duts)
        self.assertIsNone(all_duts.get("should_not"))
        self.assertTrue(all_duts.get("should_be") == "here")

    @mock.patch("icetea_lib.TestSuite.TestSuite.TestSuite._prepare_testcase")
    def test_prepare_suite_fail(self, mock_prep):
        self.args_suite.suite = "working_suite.json"
        mock_prep.side_effect = [TypeError, SyntaxError]
        with self.assertRaises(SuiteException):
            suit = TestSuite(args=self.args_suite)
        with self.assertRaises(SyntaxError):
            suit = TestSuite(args=self.args_suite)

    def test_get_suite_tcs_success(self):
        self.args_suite.suite = "working_suite.json"
        suit = TestSuite(args=self.args_suite)
        self.assertIsNone(suit._get_suite_tcs("dir", []))
        tcs = suit._get_suite_tcs("./examples", 'all')
        self.assertNotEqual(len(tcs), 0)
        # Make sure that the same testcase is found twice and that they both have different instances.
        tcs = suit._get_suite_tcs("./examples", ["sample_process_multidut_testcase", "sample_process_multidut_testcase"])
        self.assertEqual(len(tcs), 2)

    @mock.patch("icetea_lib.TestSuite.TestSuite.TestcaseFilter")
    def test_get_suite_tcs_errors(self, mock_filter):
        self.args_suite.suite = "working_suite.json"
        mock_filter.side_effect = [TypeError, {}]
        with self.assertRaises(SuiteException):
            suit = TestSuite(args=self.args_suite)

    def test_print_list_testcases(self):
        suit = TestSuite(args=self.args_noprint)
        table = suit.list_testcases()

    def test_get_suite_files(self):
        lst = TestSuite.get_suite_files("./test/suites")
        self.assertEqual(len(lst), 5)

    def test_load_suite_list(self):

        self.args_tc.tc = "tc_no_exist"
        suit = TestSuite(args=self.args_tc)
        suit._load_suite_list()
        self.assertEqual(len(suit), 1)
        suit.args.tcdir = "./test/suites"
        suit._load_suite_list()
        self.assertEqual(len(suit), 1)
        suit.args.status = 2
        self.assertFalse(suit._load_suite_list())
        suit.args.tc = False
        suit.args.status = "released"
        suit.args.tcdir = "examples"
        self.assertIsNot(suit._load_suite_list(), False)

    @mock.patch("icetea_lib.TestSuite.TestSuite.TestSuite._create_tc_list")
    def test_run(self, mock_tclist):
        testsuite = TestSuite(args=self.args_tc)
        cont1 = mock.MagicMock()
        pass_result = Result()
        pass_result.set_verdict('pass', 0, 10)
        fail_result = Result()
        fail_result.set_verdict('fail', 1000, 10)
        skipped_result = Result()
        skipped_result.set_verdict('skip', 0, 1)
        resultlist = ResultList()
        resultlist.append(pass_result)
        testsuite._default_configs["retryCount"] = 1
        cont1.run.side_effect = [pass_result, fail_result, skipped_result, KeyboardInterrupt, fail_result, pass_result]
        cont_reslist = mock.MagicMock()
        cont_reslist.run = mock.MagicMock()
        cont_reslist.run.return_value = resultlist
        # Passing result
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 1)
        self.assertEqual(testsuite._results[0].get_verdict(), "pass")
        self.assertTrue(self.args_tc.forceflash)

        # ResultList as result
        testsuite._testcases = []
        testsuite._testcases.append(cont_reslist)
        testsuite._results = []
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 1)
        self.assertEqual(testsuite._results[0].get_verdict(), "pass")

        # Failing result, no retry
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 1)
        self.assertEqual(testsuite._results[0].get_verdict(), "fail")

        # skipped result
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 1)
        self.assertEqual(testsuite._results[0].get_verdict(), "skip")

        # Interrupt
        cont2 = mock.MagicMock()
        cont2.run = mock.MagicMock()
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._testcases.append(cont2)
        testsuite._results = []
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 0)
        cont2.run.assert_not_called()

        # Failing result, retried
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        testsuite._default_configs["retryReason"] = "includeFailures"
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 2)
        self.assertEqual(testsuite._results[0].get_verdict(), "fail")
        self.assertEqual(testsuite._results[1].get_verdict(), "pass")

        self.args_tc.repeat = 2
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        cont1.run.side_effect = [pass_result, pass_result, pass_result, pass_result]
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 2)
        self.assertEqual(testsuite._results[0].get_verdict(), "pass")
        self.assertFalse(self.args_tc.forceflash)

        # Failing result, stop_on_failure
        self.args_tc.stop_on_failure = True
        self.args_tc.repeat = 1
        testsuite._default_configs["retryCount"] = 0
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        cont1.run.side_effect = [pass_result]
        cont2 = mock.MagicMock()
        cont2.run = mock.MagicMock()
        cont2.run.side_effect = [fail_result]
        cont3 = mock.MagicMock()
        cont3.run = mock.MagicMock()
        cont3.run.side_effect = [pass_result]
        testsuite._testcases.append(cont2)
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 2)
        self.assertEqual(testsuite._results[0].get_verdict(), "pass")
        self.assertEqual(testsuite._results[1].get_verdict(), "fail")

        # Skipped result, stop_on_failure
        self.args_tc.stop_on_failure = True
        self.args_tc.repeat = 0
        testsuite._testcases = []
        testsuite._testcases.append(cont1)
        testsuite._results = []
        cont1.run.side_effect = [skipped_result]
        cont2 = mock.MagicMock()
        cont2.run = mock.MagicMock()
        cont2.run.side_effect = [pass_result]
        testsuite._testcases.append(cont2)
        testsuite.run()
        self.assertEqual(testsuite.status, TestStatus.FINISHED)
        self.assertEqual(len(testsuite._results), 2)
        self.assertEqual(testsuite._results[0].get_verdict(), "skip")
        self.assertEqual(testsuite._results[1].get_verdict(), "pass")

    @mock.patch("icetea_lib.TestSuite.TestSuite.TestSuite._create_tc_list")
    @mock.patch("icetea_lib.TestSuite.TestSuite.os.path")
    def test_load_suite_file(self, mock_path, mock_tc):
        mock_path.join = mock.MagicMock()
        mock_path.join.return_value = "path"
        mock_path.exists = mock.MagicMock()
        mock_path.exists.return_value = False
        suit = TestSuite(args=self.args_suite)
        self.assertIsNone(suit._load_suite_file(1, "dir"))
        self.assertIsNone(suit._load_suite_file("name", "dir"))
        with mock.patch.object(suit, "cloud_module") as mock_cm:
            mock_cm.get_suite = mock.MagicMock()
            mock_cm.get_suite.return_value = None
            self.assertIsNone(suit._load_suite_file("name", "dir"))



if __name__ == '__main__':
    unittest.main()
