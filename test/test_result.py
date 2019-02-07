# pylint: disable=missing-docstring,too-many-statements

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
import unittest
import os

from icetea_lib.build.build import Build
from icetea_lib.DeviceConnectors.DutInformation import DutInformation
from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList


class ResultListTestcase(unittest.TestCase):

    def setUp(self):
        self.args_tc = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False, platform=None,
            status=False, suite=None, tc="test_cmdline", tc_cfg=None,
            tcdir="examples", testtype=False, type="process",
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False, repeat=0, feature=None,
            suitedir="./test/suites", forceflash_once=True, forceflash=False,
            stop_on_failure=False, json=False)

    def test_append(self):
        # Test append for single Result
        rlist = ResultList()
        result1 = Result()
        rlist.append(result1)
        self.assertListEqual(rlist.data, [result1])

        # Test append for ResultList
        result2 = Result()
        rlist2 = ResultList()
        rlist2.append(result2)
        rlist.append(rlist2)
        self.assertListEqual(rlist.data, [result1, result2])

        # Test append TypeError
        with self.assertRaises(TypeError):
            rlist.append(["test"])

    def test_get_verdict(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        reslist = ResultList()
        reslist.append(res)
        self.assertEquals(reslist.get_verdict(), "pass")
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=10)
        reslist.append(res2)
        self.assertEquals(reslist.get_verdict(), "fail")
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 1)
        reslist = ResultList()
        reslist.append(res3)
        self.assertEquals(reslist.get_verdict(), "inconclusive")
        reslist.append(res2)
        self.assertEquals(reslist.get_verdict(), "fail")

    def test_get_summary(self):
        expected = {"count": 3,
                    "pass": 1,
                    "fail": 1,
                    "skip": 0,
                    "inconclusive": 1,
                    "retries": 1,
                    "duration": 10}
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertDictEqual(resultlist.get_summary(), expected)

    def test_inconc_count(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertEqual(resultlist.inconclusive_count(), 1)
        res4 = Result()
        res4.set_verdict("inconclusive", 4, 5)
        resultlist.append(res4)
        self.assertEqual(resultlist.inconclusive_count(), 2)

    def test_pass_count(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertEqual(resultlist.success_count(), 1)
        res4 = Result()
        res4.set_verdict("pass", 4, 5)
        resultlist.append(res4)
        self.assertEqual(resultlist.success_count(), 2)

    def test_fail_count(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertEqual(resultlist.failure_count(), 1)
        res4 = Result()
        res4.set_verdict("fail", 4, 5)
        resultlist.append(res4)
        self.assertEqual(resultlist.failure_count(), 2)

    def test_retries_count(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertEqual(resultlist.retry_count(), 1)
        res4 = Result()
        res4.set_verdict("inconclusive", 4, 5)
        resultlist.append(res4)
        self.assertEqual(resultlist.retry_count(), 1)

    def test_clean_fails(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        res4 = Result()
        res4.set_verdict("inconclusive", 4, 5)
        resultlist.append(res4)
        self.assertTrue(resultlist.clean_fails())

        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res2.retries_left = 1
        res3 = Result()
        res3.set_verdict("fail", 4, 5)
        res3.retries_left = 0
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        res4 = Result()
        res4.set_verdict("inconclusive", 4, 5)
        resultlist.append(res4)
        self.assertTrue(resultlist.clean_fails())

        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res2.retries_left = 1
        res3 = Result()
        res3.set_verdict("pass", 4, 5)
        res3.retries_left = 0
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        res4 = Result()
        res4.set_verdict("inconclusive", 4, 5)
        resultlist.append(res4)
        self.assertFalse(resultlist.clean_fails())

    def test_clean_inconcs(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertTrue(resultlist.clean_inconcs())

        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res2.retries_left = 1
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res3.retries_left = 1
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        res4 = Result()
        res4.set_verdict("inconclusive", 4, 5)
        resultlist.append(res4)
        self.assertTrue(resultlist.clean_inconcs())

        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="inconclusive", retcode=1, duration=5)
        res2.retries_left = 1
        res3 = Result()
        res3.set_verdict("pass", 4, 5)
        res3.retries_left = 0
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertFalse(resultlist.clean_inconcs())

    def test_pass_rate(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        res.set_verdict(verdict="pass", retcode=0, duration=0)
        dictionary = {"retcode": 1}
        res2 = Result(kwargs=dictionary)
        res2.set_verdict(verdict="fail", retcode=1, duration=5)
        res3 = Result()
        res3.set_verdict("inconclusive", 4, 5)
        res4 = Result(kwargs=dictionary)
        res4.set_verdict(verdict="skip", retcode=1, duration=5)
        resultlist = ResultList()
        resultlist.append(res)
        resultlist.append(res2)
        resultlist.append(res3)
        self.assertEquals(resultlist.pass_rate(), "50.00 %")
        self.assertEquals(resultlist.pass_rate(include_inconclusive=True), "33.33 %")
        self.assertEquals(resultlist.pass_rate(include_skips=True), "50.00 %")
        resultlist.append(res4)
        self.assertEquals(resultlist.pass_rate(include_skips=True, include_inconclusive=True),
                          "25.00 %")


class ResultTestcase(unittest.TestCase):

    def setUp(self):
        self.args_tc = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False,
            skip_rampdown=False, skip_rampup=False, platform=None,
            status=False, suite=None, tc="test_cmdline", tc_cfg=None,
            tcdir="examples", testtype=False, type="process",
            subtype=None, use_sniffer=False, valgrind=False,
            valgrind_tool=None, verbose=False, repeat=0, feature=None,
            suitedir="./test/suites", forceflash_once=True, forceflash=False,
            stop_on_failure=False, json=False)

    def test_init(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        self.assertEqual(res.get_verdict(), "pass")

        dictionary = {"retcode": 1}
        res = Result(kwargs=dictionary)
        self.assertEqual(res.get_verdict(), "fail")

    def test_set_verdict(self):
        result = Result()
        result.set_verdict("pass", 0, 10)
        self.assertEqual(result.get_verdict(), "pass")
        self.assertEqual(result.retcode, 0)
        self.assertEqual(result.get_duration(), '0:00:10')
        self.assertEqual(result.get_duration(True), '10')

        with self.assertRaises(ValueError):
            result.set_verdict("wat")

    def test_haslogs(self):
        result = Result()
        result.logpath = os.path.join(os.path.dirname(__file__), "test_logpath")
        files = result.has_logs()
        self.assertTrue(files)
        self.assertEqual(len(files), 2)

        result = Result()
        result.logpath = None
        files = result.has_logs()
        self.assertListEqual(files, [])

    def test_result_metainfo_generation(self):
        pass_result = Result()
        pass_result.set_verdict('pass', 0, 10)
        dinfo = DutInformation("Test_platform", "123456", "1")
        dinfo.build = Build(ref="test_file", type="file")
        pass_result.add_dutinformation(dinfo)
        self.args_tc.branch = "test_branch"
        self.args_tc.commitId = "123456"
        self.args_tc.gitUrl = "url"
        self.args_tc.buildUrl = "url2"
        self.args_tc.campaign = "campaign"
        self.args_tc.jobId = "test_job"
        self.args_tc.toolchain = "toolchain"
        self.args_tc.buildDate = "today"
        pass_result.build_result_metadata(args=self.args_tc)
        self.assertEqual(pass_result.build_branch, "test_branch")
        self.assertEqual(pass_result.buildcommit, "123456")
        self.assertEqual(pass_result.build_git_url, "url")
        self.assertEqual(pass_result.build_url, "url2")
        self.assertEqual(pass_result.campaign, "campaign")
        self.assertEqual(pass_result.job_id, "test_job")
        self.assertEqual(pass_result.toolchain, "toolchain")
        self.assertEqual(pass_result.build_date, "today")


if __name__ == '__main__':
    unittest.main()
