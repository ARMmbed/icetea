# pylint: disable=missing-docstring

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

from icetea_lib.DeviceConnectors.Dut import Dut
from icetea_lib.TestStepError import TestStepError, TestStepTimeout


class DutTestcase(unittest.TestCase):

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
    def test_executionready_wait_skip(self, mock_log):  # pylint: disable=unused-argument
        dut = Dut("test_dut")
        with mock.patch.object(dut, "response_received") as mock_r:
            mock_r.wait = mock.MagicMock()
            mock_r.wait.return_value = False
            dut.query_timeout = 0
            dut.response_coming_in = -1

            with self.assertRaises(TestStepError):
                dut._wait_for_exec_ready()  # pylint: disable=protected-access

            mock_r.wait.return_value = True
            dut.query_timeout = 1

            with self.assertRaises(TestStepError):
                dut._wait_for_exec_ready()  # pylint: disable=protected-access

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
    def test_execready_wait_timeout(self, mock_log):  # pylint: disable=unused-argument
        dut = Dut("test_dut")
        with mock.patch.object(dut, "response_received") as mock_r:
            with mock.patch.object(dut, "get_time", return_value=2):
                mock_r.wait = mock.MagicMock()
                mock_r.wait.return_value = False
                dut.response_coming_in = -1
                dut.query_timeout = 1
                with self.assertRaises(TestStepTimeout):
                    dut._wait_for_exec_ready()  # pylint: disable=protected-access

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
    def test_initclihuman(self, mock_log):  # pylint: disable=unused-argument
        dut = Dut("test_Dut")
        with mock.patch.object(dut, "execute_command") as m_com:
            dut.post_cli_cmds = None
            dut.init_cli_human()
            self.assertListEqual(dut.post_cli_cmds, dut.set_default_init_cli_human_cmds())
            self.assertEqual(len(m_com.mock_calls), len(dut.post_cli_cmds))

            m_com.reset_mock()
            dut.post_cli_cmds = ["com1", "com2"]
            dut.init_cli_human()
            self.assertListEqual(dut.post_cli_cmds, ["com1", "com2"])
            self.assertEqual(len(m_com.mock_calls), 2)

            m_com.reset_mock()
            dut.post_cli_cmds = [["com1", True, False]]
            dut.init_cli_human()
            self.assertListEqual(dut.post_cli_cmds, [["com1", True, False]])
            self.assertEqual(len(m_com.mock_calls), 1)
            m_com.assert_called_once_with("com1", wait=False, asynchronous=True)


if __name__ == '__main__':
    unittest.main()
