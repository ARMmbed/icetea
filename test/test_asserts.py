# pylint: disable=missing-docstring,redundant-unittest-assert

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

import icetea_lib.tools.asserts as asserts
from icetea_lib.TestStepError import TestStepFail


class MockBench(object):
    def __init__(self):
        pass

    def command(self):
        pass

    def logger(self):
        pass


class AssertTestcase(unittest.TestCase):

    def setUp(self):
        self.asserts = asserts

    def test_assert_booleans(self):
        with self.assertRaises(TestStepFail):
            self.asserts.assertTrue(False, "False was not True!")
        with self.assertRaises(TestStepFail):
            self.asserts.assertFalse(True)

        try:
            self.asserts.assertTrue(True, "True was somehow False?!")
            self.asserts.assertTrue([1, 2])
            self.assertTrue(True, "No fail was raised.")
        except TestStepFail:
            self.assertTrue(False, "TestStepFail was raised! ")
        try:
            self.asserts.assertFalse(False)
            self.asserts.assertFalse([])
            self.asserts.assertFalse({})
            self.assertTrue(True, "No fail was raised.")
        except TestStepFail:
            self.assertTrue(False, "TestStepFail was raised! ")

    def test_assert_nones(self):
        with self.assertRaises(TestStepFail):
            self.asserts.assertNone(1)
        with self.assertRaises(TestStepFail):
            self.asserts.assertNotNone(None)

        try:
            self.asserts.assertNone(None)
            self.asserts.assertNotNone(1)
        except TestStepFail:
            self.assertTrue(False, "TestStepFail was raised!")

    def test_assert_equals(self):
        with self.assertRaises(TestStepFail):
            self.asserts.assertEqual(1, 2)
        with self.assertRaises(TestStepFail):
            self.asserts.assertNotEqual(1, 1)

        try:
            self.asserts.assertEqual(1, 1)
            self.asserts.assertNotEqual(1, 2)
        except TestStepFail:
            self.assertTrue(False, "TestStepFail was raised!")

    def test_assert_json_contains(self):
        with self.assertRaises(TestStepFail):
            self.asserts.assertJsonContains('{"test": "key"}', "test2")

        with self.assertRaises(TestStepFail):
            self.asserts.assertJsonContains("{'test': 'key'}", "test")

        with self.assertRaises(TestStepFail):
            self.asserts.assertJsonContains(None, "test")

        try:
            self.asserts.assertJsonContains('{"test": "key"}', 'test')
        except TestStepFail:
            self.assertTrue(False, 'Key test was not contained in {"test": "key"}?')

    def test_assert_dut_trace_contains(self):
        mock_bench = mock.MagicMock()
        mock_bench.verify_trace = mock.MagicMock(side_effect=[True, False])
        self.asserts.assertDutTraceContains(1, "message_found", mock_bench)
        with self.assertRaises(TestStepFail):
            self.asserts.assertDutTraceContains(1, "message_not_found", mock_bench)

    def test_assert_dut_trace_does_not_contain(self):  # pylint: disable=invalid-name
        mock_bench = mock.MagicMock()
        mock_bench.verify_trace = mock.MagicMock(side_effect=[True, False])
        with self.assertRaises(TestStepFail):
            self.asserts.assertDutTraceDoesNotContain(1, "message_found", mock_bench)
        self.asserts.assertDutTraceDoesNotContain(1, "message_not_found", mock_bench)


if __name__ == '__main__':
    unittest.main()
