# pylint: disable=protected-access,missing-docstring,unused-argument,no-self-use
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

from icetea_lib.TestBench.RunnerSM import RunnerSM


class MockLogger(object):
    def __init__(self):
        pass

    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


def template_function(*args):
    pass


class MockArgs(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.pre_cmds = []
        self.post_cmds = []
        self.kill_putty = False


class RunnerSMTestcase(unittest.TestCase):

    def test_run(self):
        mocked_bench = mock.MagicMock()
        runner = RunnerSM(mocked_bench)
        runner.args = MockArgs()
        runner._load_plugins = template_function
        runner._init_duts = template_function
        runner._start_external_services = template_function
        runner._send_pre_commands = template_function
        runner._send_post_commands = template_function
        runner._duts_release = template_function
        runner._clear_sniffer = template_function
        runner._stop_external_services = template_function
        runner.kill_putty = template_function
        runner.logger = MockLogger()
        runner.run()
        runner.args.kill_putty = True
        runner.run()

    def test_benchteardown_errors(self):
        mocked_bench = mock.MagicMock()
        runner = RunnerSM(mocked_bench)
        mocked_bench.send_post_commands = mock.MagicMock(side_effect=[Exception, 0, 0, 0, 0])
        mocked_bench.duts_release = mock.MagicMock(side_effect=[0, 0, Exception, 0, 0])
        mocked_bench.clear_sniffer = mock.MagicMock(side_effect=[0, 0, 0, Exception, 0])
        mocked_bench.stop_external_services = mock.MagicMock(side_effect=[0, 0, 0, 0, Exception])
        runner._teardown_bench()
        mocked_bench.duts_release.assert_called_once()
        mocked_bench.clear_sniffer.assert_called_once()
        mocked_bench.stop_external_services.assert_called_once()
        runner._teardown_bench()
        self.assertEqual(mocked_bench.send_post_commands.call_count, 2)
        self.assertEqual(mocked_bench.duts_release.call_count, 2)
        self.assertEqual(mocked_bench.clear_sniffer.call_count, 2)
        self.assertEqual(mocked_bench.stop_external_services.call_count, 2)
        runner._teardown_bench()
        self.assertEqual(mocked_bench.send_post_commands.call_count, 3)
        self.assertEqual(mocked_bench.duts_release.call_count, 3)
        self.assertEqual(mocked_bench.clear_sniffer.call_count, 3)
        self.assertEqual(mocked_bench.stop_external_services.call_count, 3)
        runner._teardown_bench()
        self.assertEqual(mocked_bench.send_post_commands.call_count, 4)
        self.assertEqual(mocked_bench.duts_release.call_count, 4)
        self.assertEqual(mocked_bench.clear_sniffer.call_count, 4)
        self.assertEqual(mocked_bench.stop_external_services.call_count, 4)
        runner._teardown_bench()
        self.assertEqual(mocked_bench.send_post_commands.call_count, 5)
        self.assertEqual(mocked_bench.duts_release.call_count, 5)
        self.assertEqual(mocked_bench.clear_sniffer.call_count, 5)
        self.assertEqual(mocked_bench.stop_external_services.call_count, 5)


if __name__ == '__main__':
    unittest.main()
