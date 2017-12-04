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
import subprocess
import argparse
import mock
import re
import sys
import os
import json

from icedtea_lib.IcedTeaManager import IcedTeaManager, ExitCodes
from icedtea_lib.TestSuite.TestSuite import SuiteException

class MockResults:
    def __init__(self, fails=0, inconcs=0):
        self.fails = fails
        self.inconcs = inconcs

    def failure_count(self):
        return self.fails

    def inconclusive_count(self):
        return self.inconcs

    def __len__(self):
        return self.fails + self.inconcs

class IcedTeaManagerTestcase(unittest.TestCase):

    def setUp(self):
        self.args_noprint = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=True, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='all', tc_cfg=None, tcdir="test", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None, verbose=False,
            repeat=0, platform_name=None, json=False)
        self.args_tc_no_exist = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=True, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='does_not_exist', tc_cfg=None, tcdir="test", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None, verbose=False,
            repeat=0, platform_name=None, json=False)
        self.args_suite = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=True, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite="dummy_suite.json", tc=None, tc_cfg=None, tcdir="examples", testtype=False, type=None,
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None, verbose=False, repeat=2,
            suitedir="./test/suites", platform_name=None, json=False)
        self.args_tc = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=True, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=None, tc="test_cmdline", tc_cfg=None, tcdir="examples", testtype=False, type="process",
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None, verbose=False, repeat=2,
            suitedir="./test/suites", forceflash_once=False, forceflash=False,
            ignore_invalid_params=True, failure_return_value=False, stop_on_failure=False,
            branch="", platform_name=None, json=False)

    def test_list_suites(self):
        table = IcedTeaManager.list_suites(suitedir="./test/suites")
        tab = "+------------------------+\n|    Testcase suites     " \
              "|\n+------------------------+\n" \
              "|    dummy_suite.json    |\n|   failing_suite.json   |\n|  malformed_suite.json  " \
              "|\n| suite_missing_one.json |\n|   working_suite.json   |\n" \
              "+------------------------+"
        self.assertEqual(table.get_string(), tab)

    @mock.patch("icedtea_lib.IcedTeaManager.TestSuite")
    def test_run(self, mock_suite):
        ctm = IcedTeaManager()

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

        # Test cleanlogs branch
        with mock.patch.object(ctm, "_cleanlogs") as mock_clean:
            self.args_tc.tc = None
            self.args_tc.suite = None
            self.args_tc.clean = True
            retval = ctm.run(args=self.args_tc)
            self.assertEqual(retval, 0)

    @mock.patch("icedtea_lib.IcedTeaManager.TestSuite")
    def test_run_exceptions(self, mock_suite):
        ctm = IcedTeaManager()
        mock_suite.side_effect = [SuiteException]
        self.assertEqual(ctm.run(args=self.args_tc), 3)
        with mock.patch.object(ctm, "list_suites") as mock_method:
            mock_method.return_value = None
            self.args_tc.listsuites = True
            self.assertEqual(ctm.run(args=self.args_tc), 2)

    def test_run_returnCodes(self):

        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc test_run_retcodes_fail "
                                  "--tcdir test --type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc test_run_retcodes_success "
                                  "--tcdir test --type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc test_run_retcodes_fail "
                                  "--failure_return_value --tcdir test "
                                  "--type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)

        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--suite working_suite --suitedir test/suites "
                                  "--tcdir examples",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)
        retcode = subprocess.call("python icedtea.py --tc test_run_retcodes_notfound -s "
                                  "--tcdir test --type process",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icedtea.py --clean ",
            shell=True)

    def test_run_multiple_cases_one_file(self):
        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc all "
                                  "--tcdir test/tests/multiple_in_one_file",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call(
            "python icedtea.py --clean -s "
            "--tc passing_case --failure_return_value "
            "--tcdir test/tests/multiple_in_one_file",
            shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call(
            "python icedtea.py --clean -s "
            "--tc all --failure_return_value "
            "--tcdir test/tests/multiple_in_one_file",
            shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)

        retcode = subprocess.call(
            "python icedtea.py --clean -s "
            "--tc fail_case --failure_return_value "
            "--tcdir test/tests/multiple_in_one_file",
            shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)

        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icedtea.py --clean -s",
            shell=True)

    @mock.patch("icedtea_lib.IcedTeaManager.shutil")
    def test_clean(self, mock_shutil):
        ctm = IcedTeaManager()
        self.args_tc.tc = None
        self.args_tc.clean = True
        self.assertEqual(ctm.run(self.args_tc), ExitCodes.EXIT_SUCCESS)

    @mock.patch("icedtea_lib.IcedTeaManager.get_fw_version")
    def test_version_print(self, mock_fw):
        mock_fw.return_value = "1.0.0"
        ctm = IcedTeaManager()
        self.args_tc.version = True
        self.assertEqual(ctm.run(self.args_tc), ExitCodes.EXIT_SUCCESS)

    def test_platform_name_inconc(self):
        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc test_run_retcodes_success "
                                  "--tcdir test --type process --platform_name TEST_PLAT2 "
                                  "--failure_return_value",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_INCONC, "Non-inconclusive returncode returned. "
                                                          "Allowed_platforms and platform_name "
                                                          "broken.")
        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icedtea.py --clean ",
            shell=True)

    def test_platform_name_success(self):
        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc test_run_retcodes_success "
                                  "--tcdir test --type process --platform_name TEST_PLAT "
                                  "--failure_return_value",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS, "Non-success returncode returned. "
                                                           "Allowed_platforms and platform_name "
                                                           "broken.")
        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icedtea.py --clean ",
            shell=True)

    def test_reportcmdfail(self):
        retcode = subprocess.call("python icedtea.py --clean -s "
                                  "--tc cmdfailtestcase "
                                  "--tcdir test "
                                  "--failure_return_value",
                                  shell=True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS, "Non-success returncode returned. "
                                                           "ReportCmdFail functionality broken?")
        # Run with --clean to clean up
        retcode = subprocess.call(
            "python icedtea.py --clean ",
            shell=True)

    def test_failing_suite_output_regression(self):
        proc = subprocess.Popen(["python", "icedtea.py", "--clean", "--suite",
                                 "failing_suite.json", "--suitedir", "test/suites", "--tcdir",
                                 "test/tests", "-s"], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = proc.communicate()
        self.assertTrue(re.search("This is a failing test case", output))

    def test_list_json_output(self):
        expected_output = [{u'status': u'development',
                            u'group': u'no group',
                            u'name': u'json_output_test',
                            u'comp': [u'IcedTea_ut'],
                            u'feature': u'',
                            u'subtype': u'',
                            u'file':
                                os.path.abspath(os.path.join(__file__,
                                                             "..")) + '{}tests{}'
                                                                      'json_output_test{}'
                                                                      'json_output_test_case.py'.format(os.path.sep, os.path.sep, os.path.sep),
                            u'fail': u'',
                            u'path': u'json_output_test.json_output_test_case.Testcase',
                            u'type': u'acceptance'}]

        proc = subprocess.Popen(["python", "icedtea.py", "--list", "--tcdir",
                                 "test{}tests{}json_output_test".format(os.path.sep, os.path.sep),
                                 "-s", "--json"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = proc.communicate()
        output = output.rstrip("\n")
        self.assertDictEqual(expected_output[0], json.loads(output)[0])


if __name__ == '__main__':
    unittest.main()
