# pylint: disable=missing-docstring
# -*- coding: utf-8 -*-

"""
Copyright 2019 ARM Limited
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

import signal
import subprocess
import sys
import unittest
import platform
import os
import mock

from icetea_lib.IceteaManager import ExitCodes
from icetea_lib.tools.GenericProcess import GenericProcess
from icetea_lib.TestStepError import TestStepError


class MockLogger(object):
    def __init__(self):
        pass

    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


class GenericProcessTestcase(unittest.TestCase):
    @unittest.skipIf(
        platform.system() == "Windows",
        "Launching process in Windows ends in icetea warning"
        "\"This OS is not supporting select.poll() or select.kqueue()\"")
    def test_quick_process(self):
        # Run testcase
        icetea_cmd = ["python", "icetea.py",
                      "--clean",
                      "--silent",
                      "--failure_return_value",
                      "--tc", "test_quick_process",
                      "--tcdir", '"{}"'.format(os.path.join("test", "tests"))]

        # Shouldn't need to join the argument array,
        # but it doesn't work for some reason without it (Python 2.7.12).
        retcode = subprocess.call(args=" ".join(icetea_cmd), shell=True)

        # Check success
        self.assertEqual(
            retcode, ExitCodes.EXIT_SUCCESS,
            "Non-success returncode {} returned.".format(retcode))

    def tearDown(self):
        # Run with --clean to clean up
        subprocess.call(
            "python icetea.py --clean ",
            shell=True)


@unittest.skipIf(sys.platform == 'win32', "process tests don't support Windows.")
class GenericProcessUnittests(unittest.TestCase):

    @mock.patch("icetea_lib.tools.GenericProcess.os")
    @mock.patch("icetea_lib.tools.GenericProcess.time")
    def test_stop_process(self, mocked_time, mocked_os):
        mocked_os.killpg = mock.MagicMock()
        mocked_time.sleep = mock.MagicMock(return_value=1)
        my_process = GenericProcess("test", logger=MockLogger())
        my_process.read_thread = mock.MagicMock()
        my_process.read_thread.stop = mock.MagicMock()
        my_process.stop_process()
        my_process.read_thread.stop.assert_called_once()
        mocked_proc = mock.MagicMock()
        pid = 11111111
        type(mocked_proc).pid = mock.PropertyMock(return_value=pid)
        mocked_proc.poll = mock.MagicMock()
        mocked_proc.poll.side_effect = [None, None, None, None, None,
                                        None, None, None, None, None,
                                        None, None, None, None, 0, 0, 0, 0, 0]
        type(my_process).proc = mock.PropertyMock(return_value=mocked_proc)
        my_process.stop_process()
        self.assertEqual(mocked_os.killpg.call_count, 3)
        mocked_os.killpg.assert_has_calls([mock.call(pid, signal.SIGINT),
                                           mock.call(pid, signal.SIGTERM),
                                           mock.call(pid, signal.SIGKILL)])

        my_process = GenericProcess("test", logger=MockLogger())
        my_process.read_thread = mock.MagicMock()
        my_process.read_thread.stop = mock.MagicMock()
        my_process.stop_process()
        my_process.read_thread.stop.assert_called_once()

        mocked_proc = mock.MagicMock()
        pid = 11111111
        type(mocked_proc).pid = mock.PropertyMock(return_value=pid)
        mocked_proc.poll = mock.MagicMock()
        mocked_proc.poll.side_effect = [None, None, None, None, None, None,
                                        None, None, None, 0, 0, 0]
        type(my_process).proc = mock.PropertyMock(return_value=mocked_proc)
        mocked_os.killpg.reset_mock()
        my_process.stop_process()
        self.assertEqual(mocked_os.killpg.call_count, 2)
        mocked_os.killpg.assert_has_calls([mock.call(pid, signal.SIGINT),
                                           mock.call(pid, signal.SIGTERM)])

    @mock.patch("icetea_lib.tools.GenericProcess.os", create=True)
    def test_stop_process_errors(self, mocked_os):
        mocked_os.killpg = mock.MagicMock(side_effect=OSError)
        my_process = GenericProcess("test", logger=MockLogger())

        mocked_proc = mock.MagicMock()
        pid = 11111111
        type(mocked_proc).pid = mock.PropertyMock(return_value=pid)
        type(my_process).proc = mock.PropertyMock(return_value=mocked_proc)
        my_process.stop_process()
        self.assertEqual(mocked_os.killpg.call_count, 3)

        mocked_os.killpg.reset_mock()

        mocked_os.killpg.side_effect = None
        mocked_os.killpg.return_value = 1
        mocked_proc.poll = mock.MagicMock()
        mocked_proc.poll.side_effect = [1, 1]
        with self.assertRaises(TestStepError):
            my_process.stop_process()

    def test_getters_and_setters(self):
        my_process = GenericProcess("test", logger=MockLogger())
        self.assertFalse(my_process.gdb)
        my_process.use_gdb()
        self.assertTrue(my_process.gdb)
        my_process.use_gdb(False)
        self.assertFalse(my_process.gdb)

        self.assertFalse(my_process.gdbs)
        my_process.use_gdbs()
        self.assertTrue(my_process.gdbs)
        self.assertEqual(my_process.gdbs_port, 2345)
        my_process.use_gdbs(False)
        self.assertFalse(my_process.gdbs)

        my_process.gdbs_port = 1234
        self.assertEqual(my_process.gdbs_port, 1234)

        self.assertFalse(my_process.vgdb)
        my_process.use_vgdb()
        self.assertTrue(my_process.vgdb)
        my_process.use_vgdb(False)
        self.assertFalse(my_process.vgdb)

        self.assertFalse(my_process.nobuf)
        my_process.no_std_buf()
        self.assertTrue(my_process.nobuf)
        my_process.no_std_buf(False)
        self.assertFalse(my_process.nobuf)

        self.assertIsNone(my_process.valgrind_xml)
        my_process.valgrind_xml = True
        self.assertTrue(my_process.valgrind_xml)

        self.assertFalse(my_process.valgrind_console)
        my_process.valgrind_console = True
        self.assertTrue(my_process.valgrind_console)

        self.assertFalse(my_process.valgrind_track_origins)
        my_process.valgrind_track_origins = True
        self.assertTrue(my_process.valgrind_track_origins)

        self.assertFalse(my_process.valgrind_extra_params)
        my_process.valgrind_extra_params = True
        self.assertTrue(my_process.valgrind_extra_params)

        self.assertFalse(my_process.ignore_return_code)
        my_process.ignore_return_code = True
        self.assertTrue(my_process.ignore_return_code)
        my_process.ignore_return_code = False
        self.assertFalse(my_process.ignore_return_code)

    def test_usevalgrind(self):
        my_process = GenericProcess("test", logger=MockLogger())
        with self.assertRaises(AttributeError):
            my_process.use_valgrind("test", True, True, True, True)
        my_process.use_valgrind("memcheck", 1, 2, 3, 4)
        self.assertEqual(my_process.valgrind, "memcheck")
        self.assertEqual(my_process.valgrind_xml, 1)
        self.assertEqual(my_process.valgrind_console, 2)
        self.assertEqual(my_process.valgrind_track_origins, 3)
        self.assertEqual(my_process.valgrind_extra_params, 4)


if __name__ == '__main__':
    unittest.main()
