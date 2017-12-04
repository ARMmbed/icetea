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
import sys
from lxml import html

try:
    # python2
    from StringIO import StringIO
except ImportError:
    # python3
    from io import StringIO

from icedtea_lib.Result import Result
from icedtea_lib.ResultList import ResultList
from icedtea_lib.Reports import ReportConsole, ReportHtml, ReportJunit
from icedtea_lib.tools.tools import hex_escape_str

class ReportCase(unittest.TestCase):

    """
        One unittest TestCase for all report types.
    """

    """
        ReportConsole unit tests
    """
    def test_reportConsole_no_results(self):
        saved_stdout = sys.stdout
        results = ResultList()
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 12)
        finally:
            sys.stdout = saved_stdout

    def test_reportConsole_one_results(self):
        saved_stdout = sys.stdout
        results = ResultList()
        results.append(Result())
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 14)
            self.assertRegexpMatches(lines[8], "Final Verdict.*INCONCLUSIVE", lines[8])
            self.assertRegexpMatches(lines[9], "count.*1", lines[9])
            self.assertRegexpMatches(lines[10], "passrate.*0.00 \%", lines[10])
        finally:
            sys.stdout = saved_stdout

    def test_reportConsole_multiple_results(self):
        saved_stdout = sys.stdout
        results = ResultList()
        results.append(Result())
        results.append(Result())
        results.append(Result())
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 16)
            self.assertRegexpMatches(lines[10], "Final Verdict.*INCONCLUSIVE", lines[10])
            self.assertRegexpMatches(lines[11], "count.*3", lines[11])
            self.assertRegexpMatches(lines[12], "passrate.*0.00 \%", lines[12])

        finally:
            sys.stdout = saved_stdout

    def test_reportConsole_skip(self):
        saved_stdout = sys.stdout
        results = ResultList()
        r = Result()
        r.skip_reason = "Skip_reason"
        r.set_verdict("skip", -1, -1)
        results.append(r)
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 14)
            self.assertRegexpMatches(lines[3], "skip.*Skip_reason")
            self.assertRegexpMatches(lines[8], "Final Verdict.*PASS", lines[8])
            self.assertRegexpMatches(lines[9], "count.*1", lines[9])
            self.assertRegexpMatches(lines[10], "passrate.*0.00 \%", lines[10])
            self.assertRegexpMatches(lines[11], "skip.*1", lines[10])
        finally:
            sys.stdout = saved_stdout

    def test_reportConsole_decodefail(self):
        saved_stdout = sys.stdout
        failing_message = "\x00\x00\x00\x00\x00\x00\x01\xc8"
        results = ResultList()
        r = Result()
        r.set_verdict("fail", 1001, 0)
        r.fail_reason = failing_message
        results.append(r)
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")

            self.assertEqual(len(lines), 14)
            self.assertRegexpMatches(lines[8], "Final Verdict.*FAIL", lines[8])
            self.assertRegexpMatches(lines[9], "count.*1", lines[9])
            self.assertRegexpMatches(lines[10], "passrate.*0.00 \%", lines[10])
        finally:
            sys.stdout = saved_stdout

    """
        ReportJunit tests
    """

    def test_junit_default(self):
        strShouldBe = '<testsuite failures="0" tests="1" errors="0" skipped="0">\n\
    <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
</testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        junit = ReportJunit(results)
        str = junit.to_string()
        self.assertEqual(str, strShouldBe)

    def test_junit_multiple(self):
        strShouldBe = '<testsuite failures="2" tests="7" errors="1" skipped="1">\n\
    <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
    <testcase classname="test-case-A2" name="unknown" time="50"></testcase>\n\
    <testcase classname="test-case-A3" name="unknown" time="120"></testcase>\n\
    <testcase classname="test-case-A4" name="unknown" time="120">\n\
        <failure message="unknown"></failure>\n\
    </testcase>\n\
    <testcase classname="test-case-A5" name="unknown" time="1">\n\
        <skipped></skipped>\n\
    </testcase>\n\
    <testcase classname="test-case-A6" name="unknown" time="2">\n\
        <error message="unknown"></error>\n\
    </testcase>\n\
    <testcase classname="test-case-A4" name="unknown" time="1220">\n\
        <failure message="WIN blue screen"></failure>\n\
    </testcase>\n\
</testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        results.append(Result({"testcase": "test-case-A2", "verdict": "PASS", "duration": 50}))
        results.append(Result({"testcase": "test-case-A3", "verdict": "PASS", "duration": 120}))
        results.append(Result({"testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "duration": 120}))
        results.append(Result({"testcase": "test-case-A5", "verdict": "SKIP", "reason": "unknown", "duration": 1}))
        results.append(Result({"testcase": "test-case-A6", "verdict": "INCONCLUSIVE", "reason": "unknown", "duration": 2}))
        results.append(
            Result({"testcase": "test-case-A4", "verdict": "FAIL", "reason": "WIN blue screen", "duration": 1220}))
        junit = ReportJunit(results)
        str = junit.to_string()
        self.assertEqual(str, strShouldBe)

    def test_junit_hex_escape_support(self):
        reprstring = hex_escape_str(b'\x00\x00\x00\x00\x00\x00\x01\xc8')
        strShouldBe = '<testsuite failures="1" tests="1" errors="0" skipped="0">\n\
    <testcase classname="test-case-A1" name="unknown" time="20">\n\
        <failure message="' + reprstring + '"></failure>\n\
    </testcase>\n\
</testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "FAIL", "reason":
            b'\x00\x00\x00\x00\x00\x00\x01\xc8', "duration": 20}))
        junit = ReportJunit(results)
        str = junit.to_string()
        self.assertEqual(str, strShouldBe)

    def test_junit_hides(self):
        strShouldBe1 = '<testsuite failures="0" tests="3" errors="0" skipped="0">\n\
    <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
    <testcase classname="test-case-A4" name="unknown" time="120"></testcase>\n\
    <testcase classname="test-case-A6" name="unknown" time="2"></testcase>\n\
</testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        failres =  Result({"testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "duration": 120})
        failres.retries_left=1
        results.append(failres)
        results.append(
            Result({"testcase": "test-case-A4", "verdict": "PASS", "duration": 120}))
        incres = Result({"testcase": "test-case-A6", "verdict": "INCONCLUSIVE", "reason": "unknown", "duration": 2})
        incres.retries_left = 1
        results.append(incres)
        results.append(Result({"testcase": "test-case-A6", "verdict": "PASS", "duration": 2}))

        junit = ReportJunit(results)
        str = junit.to_string()
        self.assertEqual(str, strShouldBe1)

        strShouldBe2 = '<testsuite failures="0" tests="3" errors="1" skipped="0">\n\
    <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
    <testcase classname="test-case-A4" name="unknown" time="12"></testcase>\n\
    <testcase classname="test-case-A6" name="unknown" time="2">\n\
        <error message="unknown"></error>\n\
    </testcase>\n\
</testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        failres = Result({"testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "duration": 120})
        failres.retries_left = 1
        results.append(failres)
        results.append(Result({"testcase": "test-case-A4", "verdict": "PASS", "duration": 12}))
        results.append(
            Result({"testcase": "test-case-A6", "verdict": "INCONCLUSIVE", "reason": "unknown", "duration": 2}))
        junit = ReportJunit(results)
        str = junit.to_string()
        self.assertEqual(str, strShouldBe2)

    """
    ReportHtml tests
    """

    def test_html_report(self):
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        failres = Result({"testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "duration": 120})
        results.append(failres)
        r = ReportHtml(results)
        hotml = r._create(title='Test Results', heads={'Build': '', 'Branch': ""}, refresh=None)
        doc = html.document_fromstring(hotml)
        body = doc.get_element_by_id("body")
        passes = body.find_class("item_pass")
        fails = body.find_class("item_fail")
        self.assertEqual(len(passes), len(fails))
