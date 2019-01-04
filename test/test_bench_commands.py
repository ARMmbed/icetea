# pylint: disable=missing-docstring,invalid-name,protected-access,too-few-public-methods
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

import time
import unittest
import logging
import mock

from icetea_lib.TestBench.Commands import Commands
from icetea_lib.CliAsyncResponse import CliAsyncResponse
from icetea_lib.TestStepError import TestStepFail, TestStepTimeout, TestStepError


class MockLogger(object):
    def __init__(self):
        pass

    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


class MockResponse(object):
    def __init__(self, lines=None, retcode=0):
        self.lines = lines if lines else []
        self.retcode = retcode
        self.timeout = None


class MockReq(object):
    def __init__(self, response=None):
        self.response = response if response else None
        self.dut_index = 1
        self.cmd = "test_command"


class CommandMixerTestcase(unittest.TestCase):

    def test_command_fail_nameerror(self):
        cmixer = Commands(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(),
                          mock.MagicMock(), mock.MagicMock())
        cmixer._logger = MockLogger()
        with self.assertRaises(NameError):
            cmixer._command_fail(None, fail_reason="this_fail")

    def test_command_fail(self):
        response = MockResponse(["line1", "line2"], 1001)
        request = MockReq(response)
        cmixer = Commands(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(),
                          mock.MagicMock(), mock.MagicMock())
        cmixer._logger = MockLogger()

        with self.assertRaises(TestStepFail):
            cmixer._command_fail(request)
        with self.assertRaises(TestStepFail):
            request.response.retcode = -5
            cmixer._command_fail(request)
        with self.assertRaises(TestStepFail):
            request.response.retcode = -2
            cmixer._command_fail(request)
        with self.assertRaises(TestStepFail):
            request.response.retcode = -3
            cmixer._command_fail(request)
        with self.assertRaises(TestStepFail):
            request.response.retcode = -4
            cmixer._command_fail(request)
        with self.assertRaises(TestStepTimeout):
            request.response.timeout = True
            cmixer._command_fail(request)

        request.response = None
        with self.assertRaises(TestStepFail):
            cmixer._command_fail(request)

    def test_wait_for_async_response_attribute_error(self):
        cmixer = Commands(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(),
                          mock.MagicMock(), mock.MagicMock())
        cmixer._logger = MockLogger()
        with self.assertRaises(AttributeError):
            cmixer.wait_for_async_response("test_command", None)

    def test_wait_for_async_response(self):
        mocked_plugins = mock.MagicMock()
        cmixer = Commands(mock.MagicMock(), mocked_plugins, mock.MagicMock(),
                          mock.MagicMock(), mock.MagicMock())
        cmixer._logger = MockLogger()
        mocked_dut = mock.MagicMock()
        async_resp = CliAsyncResponse(mocked_dut)
        response = MockResponse(["line1", "line2"], 1001)
        async_resp.parsed = True
        async_resp.response = response
        self.assertEqual(response, cmixer.wait_for_async_response("test_cmd", async_resp))

        async_resp.parsed = False
        mocked_plugins.parse_response = mock.MagicMock(return_value={"parsed": "resp"})
        retval = cmixer.wait_for_async_response("test_command", async_resp)
        self.assertDictEqual(retval.parsed, {"parsed": "resp"})
        self.assertEqual(response, retval)

    def test_execute_command_execute_failures(self):
        cmixer = Commands(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(),
                          mock.MagicMock(), mock.MagicMock())
        cmixer._logger = MockLogger()
        cmixer.get_time = time.time
        mocked_dut = mock.MagicMock()
        mocked_dut.execute_command = mock.MagicMock()
        mocked_dut.execute_command.side_effect = [TestStepFail, TestStepError, TestStepTimeout]

        with self.assertRaises(TestStepFail):
            cmixer._execute_command(mocked_dut, "test_command")
        with self.assertRaises(TestStepError):
            cmixer._execute_command(mocked_dut, "test_command")
        with self.assertRaises(TestStepTimeout):
            cmixer._execute_command(mocked_dut, "test_command")

    def test_private_execute_command(self):
        cmixer = Commands(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(),
                          mock.MagicMock(), mock.MagicMock())
        cmixer._logger = MockLogger()
        cmixer.get_time = time.time
        mocked_dut = mock.MagicMock()
        mocked_dut.execute_command = mock.MagicMock()
        response = MockResponse(["line1"], retcode=0)
        mocked_dut.execute_command.return_value = response
        cmixer._parse_response = mock.MagicMock(return_value={"test": "parsed"})
        self.assertEqual(cmixer._execute_command(mocked_dut, "test_command"), response)

    def test_sync_cli(self):
        mock_gen = mock.MagicMock(return_value=("val1", "val2"))
        mocked_resources = mock.MagicMock()
        logger = logging.getLogger('unittest')
        logger.addHandler(logging.NullHandler())
        cmds = Commands(mock.MagicMock(), mock.MagicMock(), mocked_resources,
                        mock.MagicMock(), mock.MagicMock())
        cmds._logger = logger
        mocked_dut = mock.MagicMock()
        mocked_resources.get_dut = mock.MagicMock(return_value=mocked_dut)
        type(mocked_dut).config = mock.PropertyMock(return_value=dict())
        with self.assertRaises(TestStepError):
            with mock.patch.object(cmds, "execute_command"):
                cmds.sync_cli("1", mock_gen, retries=1)

    @mock.patch("icetea_lib.TestBench.Commands.uuid")
    def test_echo_uuid_generator(self, mock_uuid):
        mock_uuid.uuid1 = mock.MagicMock(return_value="uuid")
        tpl = Commands.get_echo_uuid()
        expected_cmd = "echo uuid"
        expected_retval = "uuid"
        self.assertEqual(tpl[0], expected_cmd)
        self.assertEqual(tpl[1], expected_retval)


if __name__ == '__main__':
    unittest.main()
