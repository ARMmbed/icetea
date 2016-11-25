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
from mbed_clitest.Result import Result
from mbed_clitest.junit import Junit

class TestVerify(unittest.TestCase):
    def test_default(self):

        strShouldBe = '<testsuite failures="0" tests="1" skipped="0">\n\
    <testcase classname="" name="test-case-A1" time="20"></testcase>\n\
</testsuite>'
        results = [ Result({ "testcase": "test-case-A1", "verdict": "PASS", "duration":20}) ]
        junit = Junit(results)
        str = junit.get_xmlstr()
        self.assertEqual(str, strShouldBe)

    def test_multiple(self):
        strShouldBe = '<testsuite failures="2" tests="5" skipped="0">\n\
    <testcase classname="" name="test-case-A1" time="20"></testcase>\n\
    <testcase classname="" name="test-case-A2" time="50"></testcase>\n\
    <testcase classname="" name="test-case-A3" time="120"></testcase>\n\
    <testcase classname="" name="test-case-A4" time="120">\n\
        <failure message="unknown"></failure>\n\
    </testcase>\n\
    <testcase classname="" name="test-case-A4" time="1220">\n\
        <failure message="WIN blue screen"></failure>\n\
    </testcase>\n\
</testsuite>'
        results = [
                Result({ "testcase": "test-case-A1", "verdict": "PASS", "duration":20}),
                Result({ "testcase": "test-case-A2", "verdict": "PASS", "duration":50}),
                Result({ "testcase": "test-case-A3", "verdict": "PASS", "duration":120}),
                Result({ "testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "duration":120}),
                Result({ "testcase": "test-case-A4", "verdict": "FAIL", "reason": "WIN blue screen", "duration":1220}),
              ]
        junit = Junit(results)
        str = junit.get_xmlstr()
        self.assertEqual(str, strShouldBe)
