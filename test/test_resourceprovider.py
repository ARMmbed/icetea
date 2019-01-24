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

# pylint: disable=missing-docstring,old-style-class,protected-access
# pylint: disable=attribute-defined-outside-init,too-few-public-methods,unused-argument

import json
import os
import unittest
import mock

from icetea_lib.ResourceProvider.ResourceProvider import ResourceProvider
from icetea_lib.ResourceProvider.exceptions import ResourceInitError
from icetea_lib import LogManager
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError


class MockLogger:
    def __init__(self):
        pass

    def info(self, message):
        pass

    def error(self, message):
        pass

    def debug(self, message, content=None):
        pass

    def exception(self, message):
        pass


class MockAllocator:
    def __init__(self, thing1, thing2, thing3):
        self.allocate_calls = 0

    def reset_logging(self):
        pass

    def allocate(self, *args, **kwargs):
        self.allocate_calls = self.allocate_calls+1
        if self.allocate_calls == 1:
            raise AllocationError
        else:
            pass

    def cleanup(self):
        pass

    def release(self, dut=None):
        pass


class MockDut:
    def __init__(self):
        pass

    def close_dut(self):
        pass

    def close_connection(self):
        pass

    def release(self):
        pass

    def print_info(self):
        pass


class MockArgs:
    def __init__(self):
        self.parallel_flash = True
        self.allocator = "TestAllocator"
        self.list = False
        self.listsuites = False
        self.allocator_cfg = None


@mock.patch("icetea_lib.ResourceProvider.ResourceProvider.LogManager", spec=LogManager)
@mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.get_resourceprovider_logger")
class RPTestcase(unittest.TestCase):

    def test_init(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        self.res_pro = ResourceProvider(MockArgs())
        mock_logman.get_resourceprovider_logger.assert_called_once_with("ResourceProvider",
                                                                        "RSP", True)

    def test_init_with_no_file_logging(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        mock_arguments = MockArgs()
        mock_arguments.list = True
        self.res_pro = ResourceProvider(mock_arguments)
        mock_logman.get_resourceprovider_logger.assert_called_once_with("ResourceProvider",
                                                                        "RSP", False)

    def test_init_with_list(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        args = MockArgs()
        args.list = True
        self.res_pro = ResourceProvider(args)
        mock_logman.get_resourceprovider_logger.assert_called_once_with("ResourceProvider",
                                                                        "RSP", False)

    def test_allocate_duts_errors(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        self.res_pro = ResourceProvider(MockArgs())

        mock_resconf = mock.MagicMock()
        mock_pluginmanager = mock.MagicMock()
        mock_pluginmanager.get_allocator = mock.MagicMock(return_value=MockAllocator)
        self.res_pro.set_pluginmanager(mock_pluginmanager)

        mock_resconf.count_hardware = mock.MagicMock(return_value=0)
        mock_resconf.get_dut_configuration = mock.MagicMock(return_value=[])
        mock_resconf.count_duts = mock.MagicMock(return_value=0)
        self.res_pro._duts = [MockDut()]
        self.res_pro._resource_configuration = mock_resconf
        # Test raise when allocation fails
        with self.assertRaises(ResourceInitError):
            self.res_pro.allocate_duts(mock_resconf)

    def test_allocate_duts_success(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())

        self.res_pro = ResourceProvider(MockArgs())

        mock_resconf = mock.MagicMock()
        mock_resconf.count_hardware = mock.MagicMock(return_value=1)
        mock_resconf.get_dut_configuration = mock.MagicMock(return_value=[mock.MagicMock()])
        mock_resconf.count_duts = mock.MagicMock(return_value=1)
        self.res_pro._duts = [MockDut()]
        self.res_pro._resource_configuration = mock_resconf
        self.res_pro.allocator = mock.MagicMock()
        self.res_pro.allocator.allocate = mock.MagicMock()
        self.res_pro.allocate_duts(mock_resconf)
        self.res_pro.allocator.allocate.assert_called_once_with(mock_resconf,
                                                                args=self.res_pro.args)

    def test_allocator_get(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        m_args = MockArgs()
        mock_resconf = mock.MagicMock()
        mock_resconf.count_hardware = mock.MagicMock(return_value=1)
        mock_resconf.get_dut_configuration = mock.MagicMock(return_value=[mock.MagicMock()])
        mock_resconf.count_duts = mock.MagicMock(return_value=1)
        self.res_pro = ResourceProvider(m_args)
        self.res_pro._resource_configuration = mock_resconf
        mock_pluginmanager = mock.MagicMock()
        self.res_pro.set_pluginmanager(mock_pluginmanager)
        mock_allocator = mock.MagicMock()
        mock_pluginmanager.get_allocator = mock.MagicMock(side_effect=[mock_allocator, None])
        self.res_pro.allocate_duts(mock_resconf)
        mock_allocator.assert_called_once_with(m_args, None, dict())

        self.res_pro.allocator = None
        with self.assertRaises(ResourceInitError):
            self.res_pro.allocate_duts(mock_resconf)

    def test_config_file_reading(self, mock_rplogger_get, mock_logman):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                "allocator_config.json"))
        self.res_pro = ResourceProvider(MockArgs())

        with open(filepath, "r") as cfg_file:
            test_data = json.load(cfg_file)

        self.res_pro = ResourceProvider(MockArgs())
        retval = self.res_pro._read_allocator_config("testallocator", filepath)
        self.assertEquals(retval, test_data.get("testallocator"))

    @mock.patch("icetea_lib.ResourceProvider.ResourceProvider.json")
    def test_config_file_errors(self, mock_rplogger_get, mock_logman, mocked_json):
        mock_logman.get_resourceprovider_logger = mock.MagicMock(return_value=MockLogger())
        self.res_pro = ResourceProvider(MockArgs())
        with self.assertRaises(ResourceInitError):
            self.res_pro._read_allocator_config("generic", "does_not_exist")
        with self.assertRaises(ResourceInitError):
            not_a_file = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests"))
            self.res_pro._read_allocator_config("generic", not_a_file)
        with self.assertRaises(ResourceInitError):
            no_config_here = os.path.abspath(os.path.join(__file__, os.path.pardir, "suites",
                                                          "dummy_suite.json"))
            self.res_pro._read_allocator_config("generic", no_config_here)

        with self.assertRaises(ResourceInitError):
            mocked_json.load = mock.MagicMock()
            mocked_json.load.side_effect = [ValueError]
            filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                    "allocator_config.json"))
            self.res_pro._read_allocator_config("testallocator", filepath)

    def tearDown(self):
        self.res_pro.cleanup()
        self.res_pro.__metaclass__._instances.clear()


if __name__ == '__main__':
    unittest.main()
