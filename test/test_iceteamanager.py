# pylint: disable=missing-docstring
# -*- coding: utf-8 -*-

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
import re
import subprocess
import unittest

import mock
from icetea_lib.IceteaManager import IceteaManager, ExitCodes
from icetea_lib.TestSuite.TestSuite import SuiteException
from icetea_lib.tools.tools import IS_PYTHON3


class MockResults(object):
    def __init__(self, fails=0, inconcs=0):
        self.fails = fails
        self.inconcs = inconcs

    def failure_count(self):
        return self.fails

    def inconclusive_count(self):
        return self.inconcs

    def __len__(self):
        return self.fails + self.inconcs


class IceteaManagerTestcase(unittest.TestCase):

    def setUp(self):
        self.args_noprint = argparse.Namespace(
            available=False, version=False, bin=None,
            binary=False, channel=None,
            clean=True, cloud=False, component=False,
            device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False,
            iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None,
            nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='all', tc_cfg=None,
            tcdir="test", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False,
            repeat=0, platform_name=None, json=False)
        self.args_tc_no_exist = argparse.Namespace(
            available=False, version=False, bin=None,
            binary=False, channel=None,
            clean=True, cloud=False, component=False,
            device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False,
            iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None,
            nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True,
            skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='does_not_exist',
            tc_cfg=None, tcdir="test", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False,
            repeat=0, platform_name=None, json=False)
        self.args_suite = argparse.Namespace(
            available=False, version=False, bin=None,
            binary=False, channel=None,
            clean=True, cloud=False, component=False,
            device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False,
            iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None,
            nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False,
            status=False, suite="dummy_suite.json", tc=None,
            tc_cfg=None, tcdir="examples", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False, repeat=2,
            suitedir="./test/suites", platform_name=None, json=False)
        self.args_tc = argparse.Namespace(
            available=False, version=False, bin=None,
            binary=False, channel=None,
            clean=True, cloud=False, component=False,
            device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False,
            iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None,
            nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False,
            status=False, suite=None, tc="test_cmdline",
            tc_cfg=None, tcdir="examples", testtype=False, type="process",
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False, repeat=2,
            suitedir="./test/suites", forceflash_once=False, forceflash=False,
            ignore_invalid_params=True, failure_return_value=False, stop_on_failure=False,
            branch="", platform_name=None, json=False)
        self.maxdiff = None

    def tearDown(self):
        if os.path.exists("test_suite.json"):
            os.remove("test_suite.json")

    def test_list_suites(self):
        table = IceteaManager.list_suites(suitedir="./test/suites")
        tab = u'+------------------------+\n' \
              u'|    Testcase suites     |\n' \
              u'+------------------------+\n' \
              u'|    dummy_suite.json    |\n' \
              u'| duplicates_suite.json  |\n' \
              u'|   failing_suite.json   |\n' \
              u'|  malformed_suite.json  |\n' \
              u'| suite_missing_one.json |\n' \
              u'|   working_suite.json   |\n' \
              u'+------------------------+'
        self.assertEqual(table.get_string(), tab)

    @mock.patch("icetea_lib.IceteaManager._cleanlogs")
    @mock.patch("icetea_lib.IceteaManager.TestSuite")
    def test_run(self, mock_suite, mock_clean):  # pylint: disable=unused-argument
        ctm = IceteaManager()

        # Testing different return codes
        with mock.patch.object(ctm, "runtestsuite") as mock_method:
            mock_method.return_value = MockResults()
            retval = ctm.run(args=self.args_tc)
            self.assertEqual(retval, 0)
            self.args_tc.failure_return_value = True
            retval = ctm.run(args=self.args_tc)
            self.assertEqual(retval, 0)
            mock_method.return_value = MockResults(fails=1)
            retval = ctm.run(args=self.args_tc)
            self.assertEqual(retval, 2)
            mock_method.return_value = MockResults(inconcs=1)
            retval = ctm.run(args=self.args_tc)
            self.assertEqual(retval, 3)

        self.args_tc.list = True
        self.args_tc.cloud = False
        mock_suite.list_testcases = mock.MagicMock()
        mock_suite.list_testcases.return_value = "test_list"
        # Test list branch
        retval = ctm.run(args=self.args_tc)
        self.assertEqual(retval, 0)
        self.args_tc.list = False

        self.args_tc.listsuites = True
        ctm.list_suites = mock.MagicMock()
        ctm.list_suites.return_value = "Test-list-item"
        retval = ctm.run(args=self.args_tc)
        self.assertEqual(retval, 0)

    @mock.patch("icetea_lib.IceteaManager.TestSuite")
    def test_run_exceptions(self, mock_suite):
        ctm = IceteaManager()
        mock_suite.side_effect = [SuiteException]
        self.assertEqual(ctm.run(args=self.args_tc), 3)
        with mock.patch.object(ctm, "list_suites") as mock_method:
            mock_method.return_value = None
            self.args_tc.listsuites = True
            self.assertEqual(ctm.run(args=self.args_tc), 2)

    def test_run_returncodes(self):

        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc test_run_retcodes_fail "
                                  "--tcdir test --type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc test_run_retcodes_success "
                                  "--tcdir test --type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc test_run_retcodes_fail "
                                  "--failure_return_value --tcdir test "
                                  "--type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)

        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--suite working_suite --suitedir test/suites "
                                  "--tcdir examples",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)
        retcode = subprocess.call("python icetea.py --tc test_run_retcodes_notfound -s "
                                  "--tcdir test --type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        # Run with --clean to clean up
        retcode = subprocess.call(  # pylint: disable=unused-variable
            "python icetea.py --clean ",
            shell=True)

    def test_run_many_cases_one_file(self):
        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc all "
                                  "--tcdir test/tests/multiple_in_one_file",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call(
            "python icetea.py --clean -s "
            "--tc passing_case --failure_return_value "
            "--tcdir test/tests/multiple_in_one_file",
            shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call(
            "python icetea.py --clean -s "
            "--tc all --failure_return_value "
            "--tcdir test/tests/multiple_in_one_file",
            shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)

        retcode = subprocess.call(
            "python icetea.py --clean -s "
            "--tc fail_case --failure_return_value "
            "--tcdir test/tests/multiple_in_one_file",
            shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)

        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icetea.py --clean -s",
            shell=True)

    @mock.patch("icetea_lib.IceteaManager.shutil")
    def test_clean(self, mock_shutil):  # pylint: disable=unused-argument
        ctm = IceteaManager()
        self.args_tc.tc = None
        self.args_tc.clean = True
        self.assertEqual(ctm.run(self.args_tc), ExitCodes.EXIT_SUCCESS)

    @mock.patch("icetea_lib.IceteaManager.get_fw_version")
    def test_version_print(self, mock_fw):
        mock_fw.return_value = "1.0.0"
        ctm = IceteaManager()
        self.args_tc.version = True
        self.assertEqual(ctm.run(self.args_tc), ExitCodes.EXIT_SUCCESS)

    def test_platform_name_inconc(self):
        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc test_run_retcodes_success "
                                  "--tcdir test --type process --platform_name TEST_PLAT2 "
                                  "--failure_return_value",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_INCONC, "Non-inconclusive returncode returned. "
                                                          "Allowed_platforms and platform_name "
                                                          "broken.")
        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icetea.py --clean ",
            shell=True)

    def test_platform_name_success(self):
        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc test_run_retcodes_success "
                                  "--tcdir test --type process --platform_name TEST_PLAT "
                                  "--failure_return_value",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS, "Non-success returncode returned. "
                                                           "Allowed_platforms and platform_name "
                                                           "broken.")
        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icetea.py --clean ",
            shell=True)

    def test_reportcmdfail(self):
        retcode = subprocess.call("python icetea.py --clean -s "
                                  "--tc cmdfailtestcase "
                                  "--tcdir test "
                                  "--failure_return_value",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS, "Non-success returncode returned. "
                                                           "ReportCmdFail functionality broken?")
        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icetea.py --clean ",
            shell=True)

    def test_fail_suite_out_regression(self):
        proc = subprocess.Popen(["python", "icetea.py", "--clean", "--suite",
                                 "failing_suite.json", "--suitedir", "test/suites", "--tcdir",
                                 "test/tests", "-s"], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = proc.communicate()
        self.assertTrue(re.search(b"This is a failing test case", output))

    def test_list_json_output(self):
        self.maxdiff = None
        expected_test_path = os.path.abspath(os.path.join(__file__, "..", "tests",
                                                          "json_output_test",
                                                          "json_output_test_case.py"))
        expected_output = [
            {u"status": u"development",
             u"requirements": {
                 u"duts": {
                     u"*": {
                         u"application": {u"bin": None}}
                 },
                 u"external": {
                     u"apps": []}
             },
             u"filepath": expected_test_path,
             u"name": u"json_output_test",
             u"title": u"Test list output as json",
             u"component": [u"Icetea_ut"],
             u"compatible": {
                 u"framework": {
                     u"version": u">=1.0.0",
                     u"name": u"Icetea"},
                 u"hw": {u"value": True},
                 u"automation": {u"value": True}
             },
             u"purpose": u"dummy",
             u"type": u"acceptance",
             u"sub_type": None}]

        proc = subprocess.Popen(["python", "icetea.py", "--list", "--tcdir",
                                 "test{}tests{}json_output_test".format(os.path.sep, os.path.sep),
                                 "-s", "--json"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        output, _ = proc.communicate()
        output = output.rstrip(b"\n")
        if IS_PYTHON3:
            output = output.decode("utf-8")
        self.assertDictEqual(expected_output[0], json.loads(output)[0])

    def test_list_export_to_suite(self):
        expected_call = json.dumps({"default": {}, "testcases": [{"name": "json_output_test"}]})
        proc = subprocess.Popen(["python", "icetea.py", "--list", "--tcdir",
                                 "test{}tests{}json_output_test".format(os.path.sep, os.path.sep),
                                 "-s", "--json", "--export", "test_suite.json"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        output, _ = proc.communicate()  # pylint: disable=unused-variable
        with open("test_suite.json", "r") as file_handle:
            read_data = file_handle.read()
        self.assertDictEqual(json.loads(expected_call), json.loads(read_data))


if __name__ == '__main__':
    unittest.main()
