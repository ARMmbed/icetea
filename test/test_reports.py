# pylint: disable=missing-docstring,pointless-string-statement,invalid-name

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

import xml.etree.ElementTree as ET

from lxml import html

try:
    # python2
    from StringIO import StringIO
except ImportError:
    # python3
    from io import StringIO

from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList
from icetea_lib.Reports import ReportConsole, ReportHtml, ReportJunit
from icetea_lib.tools.tools import hex_escape_str


class ReportCase(unittest.TestCase):

    """
        One unittest TestCase for all report types.
    """

    """
        ReportConsole unit tests
    """
    def test_reportconsole_no_results(self):
        saved_stdout = sys.stdout
        results = ResultList()
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 13)
        finally:
            sys.stdout = saved_stdout

    def test_reportconsole_one_results(self):
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
            self.assertEqual(len(lines), 15)
            self.assertRegexpMatches(lines[8], r"Final Verdict.*INCONCLUSIVE", lines[8])
            self.assertRegexpMatches(lines[9], r"count.*1", lines[9])
            self.assertRegexpMatches(lines[10], r"passrate.*0.00 \%", lines[10])
        finally:
            sys.stdout = saved_stdout

    def test_reportconsole_multiple_results(self):  # pylint: disable=invalid-name
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
            self.assertEqual(len(lines), 17)
            self.assertRegexpMatches(lines[10], r"Final Verdict.*INCONCLUSIVE", lines[10])
            self.assertRegexpMatches(lines[11], r"count.*3", lines[11])
            self.assertRegexpMatches(lines[12], r"passrate.*0.00 \%", lines[12])

        finally:
            sys.stdout = saved_stdout

    def test_console_multiple_results_with_retries(self):
        saved_stdout = sys.stdout
        results = ResultList()
        res1 = Result()
        res1.set_verdict("fail", 1001, 1)
        res1.retries_left = 1
        res2 = Result()
        res2.set_verdict("pass", 0, 1)
        res2.retries_left = 0
        results.append(res1)
        results.append(res2)
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
            self.assertEqual(len(lines), 21)
            self.assertRegexpMatches(lines[3], "Yes", lines[4])
            self.assertRegexpMatches(lines[4], "No", lines[5])
            self.assertRegexpMatches(lines[12], "Final Verdict.*INCONCLUSIVE", lines[12])
            self.assertRegexpMatches(lines[13], "count.*5", lines[13])
            self.assertRegexpMatches(lines[14], r"passrate.*50.00 \%", lines[14])
        finally:
            sys.stdout = saved_stdout

    def test_console_pass_with_retries(self):
        saved_stdout = sys.stdout
        results = ResultList()
        res1 = Result()
        res1.set_verdict("fail", 1001, 1)
        res1.retries_left = 1
        res2 = Result()
        res2.set_verdict("pass", 0, 1)
        res2.retries_left = 0
        results.append(res1)
        results.append(res2)
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 17)
            self.assertRegexpMatches(lines[3], "Yes", lines[4])
            self.assertRegexpMatches(lines[4], "No", lines[5])
            self.assertRegexpMatches(lines[9], "Final Verdict.*PASS", lines[9])
            self.assertRegexpMatches(lines[10], "count.*2", lines[10])
            self.assertRegexpMatches(lines[11], r"passrate.*50.00 \%", lines[11])
            self.assertRegexpMatches(lines[12], r"passrate excluding retries.*100.00 \%", lines[12])
        finally:
            sys.stdout = saved_stdout

    def test_reportconsole_skip(self):
        saved_stdout = sys.stdout
        results = ResultList()
        res = Result()
        res.skip_reason = "Skip_reason"
        res.set_verdict("skip", -1, -1)
        results.append(res)
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")
            self.assertEqual(len(lines), 15)
            self.assertRegexpMatches(lines[3], r"skip.*Skip_reason")
            self.assertRegexpMatches(lines[8], r"Final Verdict.*PASS", lines[8])
            self.assertRegexpMatches(lines[9], r"count.*1", lines[9])
            self.assertRegexpMatches(lines[11], r"passrate.*0.00 \%", lines[10])
            self.assertRegexpMatches(lines[12], r"skip.*1", lines[10])
        finally:
            sys.stdout = saved_stdout

    def test_reportconsole_decodefail(self):
        saved_stdout = sys.stdout
        failing_message = "\x00\x00\x00\x00\x00\x00\x01\xc8"
        results = ResultList()
        res = Result()
        res.set_verdict("fail", 1001, 0)
        res.fail_reason = failing_message
        results.append(res)
        try:
            out = StringIO()
            sys.stdout = out
            report = ReportConsole(results)
            report.generate()
            output = out.getvalue().strip()
            lines = output.split("\n")

            self.assertEqual(len(lines), 15)
            self.assertRegexpMatches(lines[8], r"Final Verdict.*FAIL", lines[8])
            self.assertRegexpMatches(lines[9], r"count.*1", lines[9])
            self.assertRegexpMatches(lines[10], r"passrate.*0.00 \%", lines[10])
        finally:
            sys.stdout = saved_stdout

    """
        ReportJunit tests
    """

    def test_junit_default(self):
        str_should_be = '<testsuite failures="0" tests="1" errors="0" skipped="0">\n\
            <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
        </testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        junit = ReportJunit(results)
        str_report = junit.to_string()
        xml_shouldbe = ET.fromstring(str_should_be)
        report_xml = ET.fromstring(str_report)
        self.assertDictEqual(xml_shouldbe.attrib, report_xml.attrib)
        self.assertDictEqual(xml_shouldbe.find("testcase").attrib, report_xml.find(
            "testcase").attrib)
        self.assertEqual(len(xml_shouldbe.findall("testcase")), len(report_xml.findall(
            "testcase")))

    def test_junit_multiple(self):
        str_should_be = '<testsuite failures="2" tests="7" errors="1" skipped="1">\n\
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
        shouldbe_xml = ET.fromstring(str_should_be)
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        results.append(Result({"testcase": "test-case-A2", "verdict": "PASS", "duration": 50}))
        results.append(Result({"testcase": "test-case-A3", "verdict": "PASS", "duration": 120}))
        results.append(Result({"testcase": "test-case-A4",
                               "verdict": "FAIL", "reason": "unknown", "duration": 120}))
        results.append(Result({"testcase": "test-case-A5",
                               "verdict": "SKIP", "reason": "unknown", "duration": 1}))
        results.append(Result({"testcase": "test-case-A6",
                               "verdict": "INCONCLUSIVE", "reason": "unknown", "duration": 2}))
        results.append(
            Result({"testcase": "test-case-A4",
                    "verdict": "FAIL", "reason": "WIN blue screen", "duration": 1220}))
        junit = ReportJunit(results)
        str_report = junit.to_string()
        is_xml = ET.fromstring(str_report)
        self.assertDictEqual(is_xml.attrib, {"failures": "2", "tests": "7", "errors": "1",
                                             "skipped": "1"})
        self.assertEqual(len(is_xml.findall("testcase")), len(shouldbe_xml.findall("testcase")))
        self.assertEqual(len(is_xml.findall("failure")), len(shouldbe_xml.findall("failure")))
        self.assertEqual(len(is_xml.findall("skipped")), len(shouldbe_xml.findall("skipped")))
        self.assertEqual(len(is_xml.findall("error")), len(shouldbe_xml.findall("error")))

    def test_junit_hex_escape_support(self):
        reprstring = hex_escape_str(b'\x00\x00\x00\x00\x00\x00\x01\xc8')
        str_should_be = '<testsuite failures="1" tests="1" errors="0" skipped="0">\n\
            <testcase classname="test-case-A1" name="unknown" time="20">\n\
                <failure message="' + reprstring + '"></failure>\n\
            </testcase>\n\
        </testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "FAIL",
                               "reason": b'\x00\x00\x00\x00\x00\x00\x01\xc8', "duration": 20}))
        junit = ReportJunit(results)
        str_report = junit.to_string()
        xml_report = ET.fromstring(str_report)
        shouldbe_report = ET.fromstring(str_should_be)
        self.assertDictEqual(xml_report.attrib, shouldbe_report.attrib)
        reported_tc = xml_report.find("testcase")
        failure_reason = reported_tc.find("failure")
        required_tc = shouldbe_report.find("testcase")
        required_reason = required_tc.find("failure")
        self.assertTrue(required_reason.attrib["message"] == failure_reason.attrib["message"])

    def test_junit_hides(self):
        str_should_be1 = '<testsuite failures="0" tests="3" errors="0" skipped="0">\n\
            <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
            <testcase classname="test-case-A4" name="unknown" time="120"></testcase>\n\
            <testcase classname="test-case-A6" name="unknown" time="2"></testcase>\n\
        </testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        failres = Result({"testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown",
                          "duration": 120})
        failres.retries_left = 1
        results.append(failres)
        results.append(
            Result({"testcase": "test-case-A4", "verdict": "PASS", "duration": 120}))
        incres = Result({"testcase": "test-case-A6",
                         "verdict": "INCONCLUSIVE",
                         "reason": "unknown", "duration": 2})
        incres.retries_left = 1
        results.append(incres)
        results.append(Result({"testcase": "test-case-A6", "verdict": "PASS", "duration": 2}))

        junit = ReportJunit(results)
        str_report = junit.to_string()
        report_xml = ET.fromstring(str_report)
        shouldbe_xml = ET.fromstring(str_should_be1)
        self.assertDictEqual(report_xml.attrib, shouldbe_xml.attrib)
        self.assertEqual(len(report_xml.findall("testcase")), len(shouldbe_xml.findall("testcase")))

        str_should_be2 = '<testsuite failures="0" tests="3" errors="1" skipped="0">\n\
            <testcase classname="test-case-A1" name="unknown" time="20"></testcase>\n\
            <testcase classname="test-case-A4" name="unknown" time="12"></testcase>\n\
            <testcase classname="test-case-A6" name="unknown" time="2">\n\
                <error message="unknown"></error>\n\
            </testcase>\n\
        </testsuite>'
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        failres = Result({"testcase": "test-case-A4",
                          "verdict": "FAIL", "reason": "unknown", "duration": 120})
        failres.retries_left = 1
        results.append(failres)
        results.append(Result({"testcase": "test-case-A4", "verdict": "PASS", "duration": 12}))
        results.append(
            Result({"testcase": "test-case-A6",
                    "verdict": "INCONCLUSIVE", "reason": "unknown", "duration": 2}))
        junit = ReportJunit(results)
        str_report = junit.to_string()
        report_xml = ET.fromstring(str_report)
        shouldbe_xml = ET.fromstring(str_should_be2)
        self.assertDictEqual(report_xml.attrib, shouldbe_xml.attrib)
        self.assertEqual(len(report_xml.findall("testcase")), len(shouldbe_xml.findall("testcase")))
        errors = []
        for elem in report_xml.findall("testcase"):
            if elem.find("error") is not None:
                errors.append(elem)
        self.assertEqual(len(errors), 1)

    """
    ReportHtml tests
    """

    def test_html_report(self):
        results = ResultList()
        results.append(Result({"testcase": "test-case-A1", "verdict": "PASS", "duration": 20}))
        failres = Result({"testcase": "test-case-A4", "verdict": "FAIL",
                          "reason": "unknown", "duration": 120})
        results.append(failres)
        html_report = ReportHtml(results)
        # pylint: disable=protected-access
        hotml = html_report._create(title='Test Results', heads={'Build': '', 'Branch': ""},
                                    refresh=None)
        doc = html.document_fromstring(hotml)
        body = doc.get_element_by_id("body")
        passes = body.find_class("item_pass")
        fails = body.find_class("item_fail")
        self.assertEqual(len(passes), len(fails))
