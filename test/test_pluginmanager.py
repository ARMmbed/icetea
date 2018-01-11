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

import os
import sys

from icetea_lib.Plugin.PluginManager import PluginManager, PluginException
from icetea_lib.Plugin.plugins.default_plugins import default_plugins


class PMTestcase(unittest.TestCase):

    def test_load_defaults(self):
        bench = mock.MagicMock(spec=[])
        bench.logger = mock.MagicMock(return_value=mock.MagicMock())
        rp = mock.MagicMock()
        rp.append = mock.MagicMock()
        rp.has_parser = mock.MagicMock(return_value=False)
        pm = PluginManager(bench=bench, responseparser=rp)
        pm.load_default_tc_plugins()
        pm.load_default_run_plugins()
        length = len(default_plugins)
        self.assertEqual(len(pm.registered_plugins), length)

    def test_register_all_tc_types(self):
        # Set up mocks
        plugin_class = mock.MagicMock()
        plugin_class.init = mock.MagicMock()
        plugin_class.get_bench_api = mock.MagicMock()
        plugin_class.get_parsers = mock.MagicMock()
        plugin_class.get_external_services = mock.MagicMock()
        mock_bench = mock.MagicMock(spec=[])
        mock_bench.logger = mock.MagicMock(return_value=mock.MagicMock())
        mock_bench_function = mock.MagicMock()
        mock_parser = mock.MagicMock()
        plugin_class.get_bench_api.return_value = {"mock_func": mock_bench_function}
        plugin_class.get_external_services.return_value = {"mock_class": mock.MagicMock}
        plugin_class.get_parsers.return_value = {"mock_parser": mock_parser}
        mock_parsermanager = mock.MagicMock()
        mock_parsermanager.add_parser = mock.MagicMock()
        mock_parsermanager.has_parser = mock.MagicMock(return_value=False)

        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        pm.register_tc_plugins("test_plugin", plugin_class)

        # Asserts
        self.assertEqual(len(pm.registered_plugins), 1)
        self.assertEqual(pm.registered_plugins[0], "test_plugin")
        self.assertEqual(len(pm._external_services), 1)
        mock_parsermanager.has_parser.assert_called_once_with("mock_parser")
        mock_parsermanager.add_parser.assert_called_once_with("mock_parser", mock_parser)

    def test_register_and_start_service(self):
        # Set up mocks
        plugin_class = mock.MagicMock()
        plugin_class.init = mock.MagicMock()
        plugin_class.get_bench_api = mock.MagicMock()
        plugin_class.get_parsers = mock.MagicMock()
        plugin_class.get_external_services = mock.MagicMock()

        mock_bench = mock.MagicMock(spec=[])
        mock_bench.logger = mock.MagicMock(return_value=mock.MagicMock())

        plugin_class.get_bench_api.return_value = None
        mock_class = mock.MagicMock()
        plugin_class.get_external_services.return_value = {"mock_class": mock_class}
        plugin_class.get_parsers.return_value = None

        mock_parsermanager = mock.MagicMock()

        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        pm.register_tc_plugins("test_plugin", plugin_class)
        pm.start_external_service("mock_class")
        self.assertEqual(len(pm._started_services), 1)
        pm.stop_external_services()

        self.assertEqual(len(pm._started_services), 0)
        self.assertEqual(len(pm._external_services), 1)
        mock_class.assert_called_once()

    def test_start_service_raises_exception(self):
        # Set up mocks
        plugin_class = mock.MagicMock()
        plugin_class.init = mock.MagicMock()
        plugin_class.get_bench_api = mock.MagicMock()
        plugin_class.get_parsers = mock.MagicMock()
        plugin_class.get_external_services = mock.MagicMock()

        mock_bench = mock.MagicMock(spec=[])
        mock_bench.logger = mock.MagicMock(return_value=mock.MagicMock())

        plugin_class.get_bench_api.return_value = None
        mocked_service = mock.MagicMock()
        mock_class = mock.MagicMock(return_value=mocked_service)
        mocked_service.start = mock.MagicMock()
        mocked_service.start.side_effect = [PluginException]
        plugin_class.get_external_services.return_value = {"mock_class": mock_class}
        plugin_class.get_parsers.return_value = None

        mock_parsermanager = mock.MagicMock()

        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        pm.register_tc_plugins("test_plugin", plugin_class)
        with self.assertRaises(PluginException):
            pm.start_external_service("mock_class")
            mocked_service.start.assert_called_once()

    def test_register_start_stop_service(self):
        plugin_class = mock.MagicMock()
        plugin_class.init = mock.MagicMock()
        plugin_class.get_bench_api = mock.MagicMock()
        plugin_class.get_parsers = mock.MagicMock()
        plugin_class.get_external_services = mock.MagicMock()

        mock_bench = mock.MagicMock(spec=[])
        mock_bench.logger = mock.MagicMock(return_value=mock.MagicMock())

        plugin_class.get_bench_api.return_value = None
        mocked_service = mock.MagicMock()
        mocked_service.start = mock.MagicMock()
        mocked_service.stop = mock.MagicMock(side_effect=[PluginException])
        mock_class = mock.MagicMock(return_value=mocked_service)
        plugin_class.get_external_services.return_value = {"mock_class": mock_class}
        plugin_class.get_parsers.return_value = None

        mock_parsermanager = mock.MagicMock()

        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        pm.register_tc_plugins("test_plugin", plugin_class)
        pm.start_external_service("mock_class")
        self.assertEqual(len(pm._started_services), 1)
        pm.stop_external_services()

        self.assertEqual(len(pm._started_services), 0)
        self.assertEqual(len(pm._external_services), 1)
        mock_class.assert_called_once()

    def test_register_raises_pluginexception(self):
        plugin_class = mock.MagicMock()
        plugin_class.init = mock.MagicMock()
        plugin_class.get_bench_api = mock.MagicMock()

        mock_bench = mock.MagicMock(spec=[])
        mock_bench.logger = mock.MagicMock(return_value=mock.MagicMock())
        mock_bench_function = mock.MagicMock()
        mock_parser = mock.MagicMock()
        plugin_class.get_bench_api.return_value = {"mock_func": mock_bench_function}
        mock_parsermanager = mock.MagicMock()
        mock_parsermanager.add_parser = mock.MagicMock()
        mock_parsermanager.has_parser = mock.MagicMock(return_value=False)

        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        pm.registered_plugins = ["test_plugin"]
        with self.assertRaises(PluginException):
            pm.register_tc_plugins("test_plugin", plugin_class)

    def test_load_custom_plugins(self):
        modules = sys.modules
        mock_bench = mock.MagicMock(spec=[])
        mock_parsermanager = mock.MagicMock()
        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        pm.register_tc_plugins = mock.MagicMock()
        pm.load_custom_tc_plugins(os.path.join(os.path.dirname(os.path.abspath(
            __file__)), "test_plugin/load_test_plugins.py"))
        sys.modules = modules
        pm.register_tc_plugins.assert_called_once()

    @mock.patch("icetea_lib.Plugin.PluginManager.importlib")
    def test_load_custom_plugin_exception(self, mock_importer):
        mock_bench = mock.MagicMock(spec=[])
        mock_parsermanager = mock.MagicMock()
        mock_importer.import_module = mock.MagicMock(side_effect=[ImportError])
        pm = PluginManager(bench=mock_bench, responseparser=mock_parsermanager)
        with self.assertRaises(PluginException):
            pm.load_custom_tc_plugins(os.path.join(os.path.dirname(os.path.abspath(
                __file__)), "test_plugin/load_test_plugins.py"))


if __name__ == '__main__':
    unittest.main()
