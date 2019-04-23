# pylint: disable=missing-docstring,protected-access,unused-argument,no-self-use
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

from icetea_lib.TestBench.Resources import ResourceFunctions
from icetea_lib.ResourceProvider.ResourceConfig import ResourceConfig

TEST_REQS = {
    "requirements": {
        "duts": {
            "*": {"count": 2, "type": "process", "expires": 2000},
            "1": {"nick": "dut1"},
            "2": {"nick": "test_device"}
        }
    }
}


class MockArgs(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.silent = True


class MockLogger(object):
    def __init__(self):
        pass

    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


class ResourceMixerTests(unittest.TestCase):

    def _create_dut(self):
        mocked_dut = mock.MagicMock()
        mocked_dut.close_dut = mock.MagicMock(side_effect=[True, KeyboardInterrupt])
        mocked_dut.close_connection = mock.MagicMock()
        mocked_dut.finished = mock.MagicMock(side_effect=[False, True])
        return mocked_dut

    @mock.patch("icetea_lib.TestBench.Resources.time")
    def test_dut_release(self, mock_time):
        mocked_dut = self._create_dut()
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        resmixer.duts = [mocked_dut]
        resmixer._args = MockArgs()
        resmixer._logger = MockLogger()
        resmixer._resource_provider = mock.MagicMock()
        resmixer._call_exception = mock.MagicMock()
        resmixer.is_my_dut_index = mock.MagicMock(return_value=True)
        resmixer.duts_release()
        mocked_dut.close_dut.assert_called_once()
        mocked_dut.close_connection.assert_called_once()
        resmixer.duts_release()
        self.assertEqual(len(resmixer.duts), 0)

    @mock.patch("icetea_lib.TestBench.Resources.time")
    def test_dut_release_exception(self, mock_time):
        mocked_dut = self._create_dut()
        mocked_dut.close_connection = mock.MagicMock(side_effect=[Exception])
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        resmixer.duts = [mocked_dut]
        resmixer._args = MockArgs()
        resmixer._logger = MockLogger()
        resmixer._resource_provider = mock.MagicMock()
        resmixer._resource_provider.allocator = mock.MagicMock()
        type(resmixer._resource_provider.allocator).share_allocations = mock.PropertyMock(
            return_value=False)
        resmixer._resource_provider.allocator.release = mock.MagicMock()
        resmixer._call_exception = mock.MagicMock()
        resmixer.is_my_dut_index = mock.MagicMock(return_value=True)
        resmixer.duts_release()
        mocked_dut.close_dut.assert_called_once()
        mocked_dut.close_connection.assert_called_once()
        resmixer._resource_provider.allocator.release.assert_called_once()

    def test_dut_count(self):
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        resmixer.resource_configuration.count_duts = mock.MagicMock(return_value=1)
        self.assertEqual(resmixer.dut_count(), 1)
        resmixer.resource_configuration = None
        self.assertEqual(resmixer.dut_count(), 0)
        self.assertEqual(resmixer.get_dut_count(), 0)
        resmixer.resource_configuration = ResourceConfig()
        resmixer.resource_configuration.count_duts = mock.MagicMock(return_value=1)
        self.assertEqual(resmixer.get_dut_count(), 1)

    def test_is_allowed_dut_index(self):
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        resmixer.resource_configuration = ResourceConfig()
        resmixer.resource_configuration.count_duts = mock.MagicMock(return_value=4)
        self.assertTrue(resmixer.is_allowed_dut_index(2))
        self.assertTrue(resmixer.is_allowed_dut_index(4))
        self.assertFalse(resmixer.is_allowed_dut_index(5))

    def test_get_dut(self):
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        resmixer._logger = MockLogger()
        mocked_dut = self._create_dut()
        resmixer.duts = [mocked_dut]
        self.assertEqual(resmixer.get_dut(1), mocked_dut)
        with self.assertRaises(ValueError):
            resmixer.get_dut(2)

    def test_get_dut_nick(self):
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        type(resmixer._configuration).config = mock.PropertyMock(return_value=TEST_REQS)
        resmixer.resource_configuration = ResourceConfig(TEST_REQS)
        resmixer.resource_configuration.resolve_configuration(None)
        self.assertEqual(resmixer.get_dut_nick(1), "dut1")
        self.assertEqual(resmixer.get_dut_nick(2), "test_device")
        self.assertEqual(resmixer.get_dut_nick("1"), "dut1")
        self.assertEqual(resmixer.get_dut_nick("2"), "test_device")
        self.assertEqual(resmixer.get_dut_nick("3"), "3")

    def test_get_dut_index(self):
        resmixer = ResourceFunctions(mock.MagicMock(), mock.MagicMock(), mock.PropertyMock(
            return_value=TEST_REQS))
        resmixer.resource_configuration = ResourceConfig(TEST_REQS)
        resmixer.resource_configuration.resolve_configuration(None)
        self.assertEqual(resmixer.get_dut_index("dut1"), 1)
        self.assertEqual(resmixer.get_dut_index("test_device"), 2)
        with self.assertRaises(ValueError):
            resmixer.get_dut_index("3")

    def test_config_validation_bin_not_defined(self):  # pylint: disable=invalid-name
        duts_cfg = [{}]
        mocked_args = mock.MagicMock()
        type(mocked_args).skip_flash = mock.PropertyMock(return_value=False)
        resources = ResourceFunctions(mocked_args,
                                      mock.MagicMock(), mock.PropertyMock(return_value=TEST_REQS))
        self.assertEqual(resources.validate_dut_configs(duts_cfg, MockLogger()), None)

    def test_config_validation_no_bin(self):
        duts_cfg = [{"application": {"bin": "not.exist"}}]
        mocked_args = mock.MagicMock()
        type(mocked_args).skip_flash = mock.PropertyMock(return_value=False)
        resources = ResourceFunctions(mocked_args, mock.MagicMock(), mock.PropertyMock(
            return_value=TEST_REQS))
        with self.assertRaises(EnvironmentError):
            resources.validate_dut_configs(duts_cfg, MockLogger())

    def test_config_validation_bin_defined(self):  # pylint: disable=invalid-name
        duts_cfg = [{"application": {"bin": __file__}}]
        mocked_args = mock.MagicMock()
        type(mocked_args).skip_flash = mock.PropertyMock(return_value=False)
        resources = ResourceFunctions(mocked_args,
                                      mock.MagicMock(), mock.PropertyMock(return_value=TEST_REQS))
        self.assertEqual(resources.validate_dut_configs(duts_cfg, MockLogger()), None)

    def test_config_validation_no_bin_skip_flash(self):  # pylint: disable=invalid-name
        duts_cfg = [{"application": {"bin": "not.exist"}}]
        mocked_args = mock.MagicMock()
        type(mocked_args).skip_flash = mock.PropertyMock(return_value=True)
        resources = ResourceFunctions(mocked_args,
                                      mock.MagicMock(), mock.PropertyMock(return_value=TEST_REQS))
        self.assertEqual(resources.validate_dut_configs(duts_cfg, MockLogger()), None)


if __name__ == '__main__':
    unittest.main()
