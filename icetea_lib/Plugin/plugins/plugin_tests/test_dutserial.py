# pylint: disable=unused-argument,missing-docstring,too-many-arguments,too-few-public-methods
# pylint: disable=no-self-use

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

from icetea_lib.Plugin.plugins.LocalAllocator.DutSerial import DutSerial
from icetea_lib.DeviceConnectors.Dut import DutConnectionError

try:
    from mbed_flasher.common import FlashError
except ImportError:
    FlashError = None


class MockArgspec(object):
    def __init__(self, lst):
        self.args = lst


class DutSerialTestcase(unittest.TestCase):

    # Mock base class
    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_flasher_logger_insert(self, mock_build, mock_flasher, mocked_logger, mock_inspect,
                                   mock_bench_logger):
        mock_inspect.return_value = MockArgspec(["logger"])
        mocked_logger_for_flasher = mock.MagicMock()
        mocked_logger.return_value = mocked_logger_for_flasher
        dut = DutSerial(port="test",
                        config={"allocated": {"target_id": "thing"}, "application": "thing"})
        dut.flash("this_is_not_a_binary")
        mock_flasher.assert_called_with(logger=mocked_logger_for_flasher)

        mock_flasher.reset_mock()
        mock_inspect.return_value = MockArgspec([])
        dut = DutSerial(port="test",
                        config={"allocated": {"target_id": "thing"}, "application": "thing"})
        dut.flash("this_is_not_a_binary")
        mock_flasher.assert_called_with()

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_flash_build_init_not_implemented(self, mock_build, mock_flasher, mocked_logger,
                                              mock_inspect, mock_bench_logger):
        mock_build.init = mock.MagicMock(side_effect=[NotImplementedError])
        mock_inspect.return_value = MockArgspec(["logger"])
        mocked_logger_for_flasher = mock.MagicMock()
        mocked_logger.return_value = mocked_logger_for_flasher
        dut = DutSerial(port="test",
                        config={"allocated": {"target_id": "thing"}, "application": "thing"})
        with self.assertRaises(DutConnectionError):
            dut.flash("try")

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_flash_build_get_file_fail(self, mock_build, mock_flasher, mocked_logger, mock_inspect,
                                       mock_bench_logger):
        mock_build_object = mock.MagicMock()
        mock_build_object.get_file = mock.MagicMock(side_effect=[False, "Thisbin"])
        mock_build.init = mock.MagicMock(return_value=mock_build_object)
        mock_inspect.return_value = MockArgspec(["logger"])
        mocked_logger_for_flasher = mock.MagicMock()
        mocked_logger.return_value = mocked_logger_for_flasher
        dut = DutSerial(port="test",
                        config={"allocated": {"target_id": "thing"}, "application": "thing"})
        with self.assertRaises(DutConnectionError):
            dut.flash("try")

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_flash_fails(self, mock_build, mock_flasher, mocked_logger, mock_inspect,
                         mock_bench_logger):
        mock_build_object = mock.MagicMock()
        mock_build_object.get_file = mock.MagicMock(return_value="Thisbin")
        mock_build.init = mock.MagicMock(return_value=mock_build_object)
        mock_inspect.return_value = MockArgspec(["logger"])
        mocked_logger_for_flasher = mock.MagicMock()
        mocked_logger.return_value = mocked_logger_for_flasher
        mock_flasher_object = mock.MagicMock()
        mock_flasher.return_value = mock_flasher_object
        mock_flasher_object.flash = mock.MagicMock()
        mock_flasher_object.flash.side_effect = [NotImplementedError, SyntaxError, 1]
        if FlashError is not None:
            mock_flasher_object.flash.side_effect = [NotImplementedError, SyntaxError, 1,
                                                     FlashError("Error", 10)]
        dut = DutSerial(port="test",
                        config={"allocated": {"target_id": "thing"}, "application": "thing"})
        with self.assertRaises(DutConnectionError):
            dut.flash("try")
        with self.assertRaises(DutConnectionError):
            dut.flash("try2")
        self.assertFalse(dut.flash("try3"))
        if FlashError is not None:
            with self.assertRaises(DutConnectionError):
                dut.flash("try4")

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_flash_skip_flash(self, mock_build, mock_flasher, mocked_logger, mock_inspect,
                              mock_bench_logger):
        mock_build_object = mock.MagicMock()
        mock_build_object.get_file = mock.MagicMock(return_value="Thisbin")
        mock_build.init = mock.MagicMock(return_value=mock_build_object)
        mock_inspect.return_value = MockArgspec(["logger"])
        mock_logger_for_flasher = mock.MagicMock()
        mocked_logger.return_value = mock_logger_for_flasher
        mock_flasher_object = mock.MagicMock()
        mock_flasher.return_value = mock_flasher_object
        mock_flasher_object.flash = mock.MagicMock()
        mock_flasher_object.flash.return_value = 0
        dut = DutSerial(port="test", config={
            "allocated": {"target_id": "thing"},
            "application": "thing"
        })
        self.assertTrue(dut.flash("try"))
        self.assertTrue(dut.flash("try"))
        self.assertTrue(dut.flash("try"))
        self.assertEqual(mock_flasher_object.flash.call_count, 1)
        self.assertTrue(dut.flash("try", forceflash=True))
        self.assertEqual(mock_flasher_object.flash.call_count, 2)

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_peek(self, mock_build, mock_flasher, mocked_logger, mock_inspect,
                  mock_bench_logger):
        dut = DutSerial(port="test", config={
            "allocated": {"target_id": "thing"},
            "application": "thing"
        })
        dut.port = mock.MagicMock()
        dut.port.peek = mock.MagicMock(return_value="test")
        self.assertEqual(dut.peek(), "test")

    @mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager.get_bench_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.getargspec")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.get_resourceprovider_logger")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Flash")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Build")
    def test_readline(self, mock_build, mock_flasher, mocked_logger, mock_inspect,
                  mock_bench_logger):
        dut = DutSerial(port="test", config={
            "allocated": {"target_id": "thing"},
            "application": "thing"
        })
        dut.port = mock.MagicMock()
        dut.port.readline = mock.MagicMock(side_effect=["test\n", None])
        self.assertEqual(dut._readline(), "test")
        self.assertIsNone(dut._readline())


if __name__ == '__main__':
    unittest.main()