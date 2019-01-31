# pylint: disable=unused-argument,invalid-name,missing-docstring,no-self-use

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

# pylint: disable=unused-argument,invalid-name,missing-docstring,no-self-use

import unittest
import mock
from serial import SerialException

from icetea_lib.Plugin.plugins.LocalAllocator.DutSerial import DutSerial
from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.DeviceConnectors.DutInformation import DutInformation


@mock.patch("icetea_lib.DeviceConnectors.Dut.LogManager")
class DutSerialTestcase(unittest.TestCase):

    def test_properties(self, mock_logger):
        ds = DutSerial()
        self.assertFalse(ds.ch_mode)
        ds.ch_mode = True
        self.assertTrue(ds.ch_mode)

        self.assertEqual(ds.ch_mode_chunk_size, 1)
        ds.ch_mode_chunk_size = 2
        self.assertEqual(ds.ch_mode_chunk_size, 2)

        self.assertEqual(ds.ch_mode_ch_delay, 0.01)
        ds.ch_mode_ch_delay = 0.02
        self.assertEqual(ds.ch_mode_ch_delay, 0.02)

        self.assertEqual(ds.ch_mode_start_delay, 0)
        ds.ch_mode_start_delay = 1
        self.assertEqual(ds.ch_mode_start_delay, 1)

        self.assertEqual(ds.serial_baudrate, 460800)
        ds.serial_baudrate = 9600
        self.assertEqual(ds.serial_baudrate, 9600)

        self.assertEqual(ds.serial_timeout, 0.01)
        ds.serial_timeout = 0.02
        self.assertEqual(ds.serial_timeout, 0.02)

        self.assertFalse(ds.serial_xonxoff)
        ds.serial_xonxoff = True
        self.assertTrue(ds.serial_xonxoff)

        self.assertFalse(ds.serial_rtscts)
        ds.serial_rtscts = True
        self.assertTrue(ds.serial_rtscts)

    def test_get_resource_id(self, mock_logger):
        ds = DutSerial(config={"allocated": {"target_id": "test"}, "application": {}})
        self.assertEqual(ds.get_resource_id(), "test")

    def test_get_info(self, mock_logger):
        ds = DutSerial()
        info = ds.get_info()
        self.assertTrue(isinstance(info, DutInformation))

    def test_flash(self, mock_logger):
        ds = DutSerial()
        self.assertTrue(ds.flash())

    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.EnhancedSerial")
    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.Thread")
    def test_open_connection(self, mock_thread, mock_es, mock_logger):
        ds = DutSerial()
        ds.readthread = 1
        ds.params = mock.MagicMock()
        type(ds.params).reset = mock.PropertyMock(return_value=False)
        with self.assertRaises(DutConnectionError):
            ds.open_connection()
        ds.readthread = None
        mock_es_2 = mock.MagicMock()
        mock_es_2.flushInput = mock.MagicMock(side_effect=[SerialException, ValueError, 1])
        mock_es.return_value = mock_es_2
        with self.assertRaises(DutConnectionError):
            ds.open_connection()
        with self.assertRaises(ValueError):
            ds.open_connection()
        ds.open_connection()
        mock_thread.assert_called_once()

    def test_prepare_connection_close(self, mock_logger):
        ds = DutSerial()
        with mock.patch.object(ds, "init_cli_human") as mock_init_cli_human:
            with mock.patch.object(ds, "stop") as mock_stop:
                ds.prepare_connection_close()
                mock_init_cli_human.assert_called_once()
                mock_stop.assert_called_once()

    def test_close_connection(self, mock_logger):
        ds = DutSerial()
        mocked_port = mock.MagicMock()
        mocked_port.close = mock.MagicMock()
        ds.port = mocked_port
        with mock.patch.object(ds, "stop") as mock_stop:
            ds.close_connection()
            mock_stop.assert_called_once()
            mocked_port.close.assert_called_once()
            self.assertFalse(ds.port)

    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.DutSerial.time")
    def test_reset(self, mocked_time, mock_logger):
        ds = DutSerial()
        mock_port = mock.MagicMock()
        mock_port.safe_sendBreak = mock.MagicMock(return_value=True)
        mocked_time.sleep = mock.MagicMock()
        ds.port = mock_port
        self.assertIsNone(ds.reset())

    def test_writeline(self, mock_logger):
        ds = DutSerial()
        mock_port = mock.MagicMock()
        mock_port.write = mock.MagicMock(side_effect=[1, 1, 1, 1, SerialException])
        ds.port = mock_port
        ds.ch_mode = False
        ds.writeline("data")
        mock_port.write.assert_called_once_with("data\n".encode())
        mock_port.reset_mock()
        ds.ch_mode = True
        ds.ch_mode_chunk_size = 2
        ds.writeline("data")
        mock_port.write.assert_has_calls([mock.call("da".encode()), mock.call("ta".encode()),
                                          mock.call("\n".encode())])
        with self.assertRaises(RuntimeError):
            ds.writeline("data")

    def test_readline(self, mock_logger):
        ds = DutSerial()
        ds.input_queue.append("test1")
        read = ds.readline()
        self.assertEqual(read, "test1")
        self.assertIsNone(ds.readline())

    def test_peek(self, mock_logger):
        ds = DutSerial()
        mocked_port = mock.MagicMock()
        mocked_port.peek = mock.MagicMock(return_value="test")
        ds.port = mocked_port
        self.assertEqual(ds.peek(), "test")
        mocked_port.peek.assert_called_once()
        ds.port = None
        self.assertEqual(ds.peek(), "")
