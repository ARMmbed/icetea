# pylint: disable=missing-docstring,no-self-use,protected-access
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

from icetea_lib.TestBench.BenchFunctions import BenchFunctions


class MockedDut(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.traces = ["test1", "test2"]


class BenchFunctionsTests(unittest.TestCase):

    @mock.patch("icetea_lib.TestBench.BenchFunctions.time")
    def test_delay(self, mocked_time):
        benchfunctions = BenchFunctions(mock.MagicMock(),
                                        mock.MagicMock(), mock.MagicMock())
        mocked_time.sleep = mock.MagicMock()
        benchfunctions._logger = mock.MagicMock()
        benchfunctions.delay(1)
        benchfunctions.delay(40)

    @mock.patch("icetea_lib.TestBench.BenchFunctions.sys")
    def test_input_from_user(self, mocked_sys):
        benchfunctions = BenchFunctions(mock.MagicMock(), mock.MagicMock(),
                                        mock.MagicMock())
        mocked_sys.stdin = mock.MagicMock()
        mocked_sys.stdin.readline = mock.MagicMock(side_effect=["string\n", ''])
        data = benchfunctions.input_from_user("Test")
        self.assertEqual(data, "string")
        data = benchfunctions.input_from_user("Test")
        self.assertEqual(data, "")

    @mock.patch("icetea_lib.TestBench.BenchFunctions.verify_message")
    def test_verify_trace(self, mocked_verify_message):
        benchfunctions = BenchFunctions(mock.MagicMock(), mock.MagicMock(),
                                        mock.MagicMock())
        mocked_verify_message.side_effect = [True, TypeError, False, False, True]
        benchfunctions.duts = [MockedDut()]
        self.assertTrue(benchfunctions.verify_trace(0, "test1"))
        with self.assertRaises(TypeError):
            benchfunctions.verify_trace(0, "test1")
        self.assertFalse(benchfunctions.verify_trace(0, "test3", False))
        with self.assertRaises(LookupError):
            benchfunctions.verify_trace(0, "test4")
        benchfunctions.get_dut_index = mock.MagicMock(return_value=0)
        self.assertTrue(benchfunctions.verify_trace("0", "test1"))
