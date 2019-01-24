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

from icetea_lib.TestBench.Plugins import Plugins, PluginException


class MockArgs(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.silent = True


class MockLogger(object):
    def __init__(self):
        pass

    def warning(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


class PluginMixerTests(unittest.TestCase):

    def test_start_external_services(self):
        mocked_config = {
            "requirements": {
                "external": {
                    "apps": [
                        {
                            "name": "test_app"
                        }
                    ]

                }
            }
        }
        mixer = Plugins(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(), mocked_config)
        mixer.init(mock.MagicMock())
        mixer._env = {}
        mixer._args = MockArgs()
        mixer._logger = MockLogger()
        mixer._pluginmanager = mock.MagicMock()
        mixer._pluginmanager.start_external_service = mock.MagicMock(
            side_effect=[PluginException, True])
        with self.assertRaises(EnvironmentError):
            mixer.start_external_services()
        mixer._pluginmanager.start_external_service.assert_called_once_with(
            "test_app", conf={"name": "test_app"})

    @mock.patch("icetea_lib.TestBench.Plugins.GenericProcess")
    def test_start_generic_app(self, mock_gp):
        mocked_config = {
            "requirements": {
                "external": {
                    "apps": [
                        {
                            "cmd": [
                                "echo",
                                "1"
                            ],
                            "path": "test_path"
                        }
                    ]
                }
            }
        }
        mixer = Plugins(mock.MagicMock(), mock.MagicMock(), mock.MagicMock(), mocked_config)
        mixer._env = dict()
        mixer._logger = MockLogger()
        mixer._args = MockArgs()
        mocked_app = mock.MagicMock()
        mocked_app.start_process = mock.MagicMock()
        mock_gp.return_value = mocked_app
        mixer.start_external_services()
        mocked_app.start_process.assert_called_once()
        mock_gp.assert_called_with(cmd=["echo", "1"], name="generic", path="test_path")
