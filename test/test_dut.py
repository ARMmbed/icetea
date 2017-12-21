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

import mock
import unittest


from icetea_lib.DeviceConnectors.Dut import Dut
from icetea_lib.TestStepError import TestStepError, TestStepTimeout


class DutTestcase(unittest.TestCase):

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
    def test_executionready_wait_skip(self, mock_log):
        d = Dut("test_dut")
        with mock.patch.object(d, "response_received") as mock_r:
            mock_r.wait = mock.MagicMock()
            mock_r.wait.return_value = False
            d.query_timeout = 0
            d.response_coming_in = -1
            self.q_async_response = mock.MagicMock()

            with self.assertRaises(TestStepError):
                d._wait_for_exec_ready()

            mock_r.wait.return_value = True
            d.query_timeout = 1

            with self.assertRaises(TestStepError):
                d._wait_for_exec_ready()

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
    def test_executionready_wait_timeout(self, mock_log):
        d = Dut("test_dut")
        with mock.patch.object(d, "response_received") as mock_r:
            with mock.patch.object(d, "get_time", return_value=2):
                mock_r.wait = mock.MagicMock()
                mock_r.wait.return_value = False
                d.response_coming_in = -1
                d.query_timeout = 1
                with self.assertRaises(TestStepTimeout):
                    d._wait_for_exec_ready()

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
    def test_initclihuman(self, mock_log):
        d = Dut("test_Dut")
        with mock.patch.object(d, "execute_command") as m_com:
            d.post_cli_cmds = None
            d.init_cli_human()
            self.assertListEqual(d.post_cli_cmds, d.set_default_init_cli_human_cmds())
            self.assertEqual(len(m_com.mock_calls), len(d.post_cli_cmds))

            m_com.reset_mock()
            d.post_cli_cmds = ["com1", "com2"]
            d.init_cli_human()
            self.assertListEqual(d.post_cli_cmds, ["com1", "com2"])
            self.assertEqual(len(m_com.mock_calls), 2)

            m_com.reset_mock()
            d.post_cli_cmds = [["com1", True, False]]
            d.init_cli_human()
            self.assertListEqual(d.post_cli_cmds, [["com1", True, False]])
            self.assertEqual(len(m_com.mock_calls), 1)
            m_com.assert_called_once_with("com1", wait=False, async=True)


if __name__ == '__main__':
    unittest.main()
