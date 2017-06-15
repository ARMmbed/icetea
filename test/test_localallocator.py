"""
Copyright 2016 ARM Limited

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
import logging
from mbed_test.ResourceProvider.Allocators.LocalAllocator import LocalAllocator
from mbed_test.ResourceProvider.Allocators.exceptions import AllocationError

@mock.patch("mbed_test.ResourceProvider.Allocators.LocalAllocator.DutDetection", create=False)
class TestVerify(unittest.TestCase):

    @mock.patch("mbed_test.ResourceProvider.Allocators.LocalAllocator.logging", create=True)
    def test_init_with_no_logger(self, mock_logging, mock_dutdetection):
        dutdetect = mock.Mock()
        mock_dutdetection.return_value = dutdetect
        dutdetect.get_available_devices = mock.MagicMock(return_value=None)
        mock_logger = mock.Mock()
        mock_logging.get_logger = mock.MagicMock(return_value=mock_logger)
        mock_logging.NullHandler = mock.MagicMock()

        alloc = LocalAllocator()

        mock_dutdetection.assert_called_once_with()
        dutdetect.get_available_devices.assert_called_once_with()
        mock_logging.getLogger.assert_called_once_with("dummy")
        mock_logging.NullHandler.assert_called_once_with()

    def test_init_with_no_logger_results_in_null_logger(self, md):
        alloc = LocalAllocator()
        self.assertEqual(type(alloc.logger), logging.Logger)
        self.assertEqual(type(alloc.logger.handlers[0]), logging.NullHandler)
        try:
            alloc.logger.info("test")
        except NameError as e:
            if "logging" in e or "info" in e:
                self.fail("Logging broken if no logger given")

    def test_init_with_no_logger_results_in_null_logger(self, md):
        alloc = LocalAllocator()
        self.assertEqual(type(alloc.logger), logging.Logger)
        self.assertEqual(type(alloc.logger.handlers[0]), logging.NullHandler)
        try:
            alloc.logger.info("test")
        except NameError as e:
            if "logging" in e or "info" in e:
                self.fail("Logging broken if no logger given")

    def test_can_allocate_success(self, md):
        alloc = LocalAllocator()
        data1 = {"type" : "hardware"}
        self.assertTrue(alloc.can_allocate(data1))

    def test_can_allocate_unknown_type(self, md):
        alloc = LocalAllocator()
        data_unknown_type = {"type" : "unknown"}
        self.assertFalse(alloc.can_allocate(data_unknown_type))

        data_unknown_type = {"type" : None}
        self.assertFalse(alloc.can_allocate(data_unknown_type))

    def test_can_allocate_missing_type(self, md):
        alloc = LocalAllocator()
        data_no_type = {"notype": None}
        self.assertFalse(alloc.can_allocate(data_no_type))

    def test_allocate_raises_on_invalid_dut_format(self, md):
        alloc = LocalAllocator()
        data = "not a list"
        self.assertRaises(AllocationError, alloc.allocate, data)

    def test_internal_allocate_no_type_raises(self, md):
        alloc = LocalAllocator()
        data = {"notype": None}
        self.assertRaises(KeyError, alloc._allocate, data)

    def test_internal_allocate_non_hardware_types_success(self, md):
        alloc = LocalAllocator()
        data = {"type": "process"}
        self.assertTrue(alloc._allocate(data))


    def test_internal_allocate_non_hardware_types_success_with_dutfactory(self, md):
        alloc = LocalAllocator()
        data = {"type": "process"}
        self.assertTrue(alloc._allocate(data))


    def test_internal_allocate_hardware_platform_no_devices_raises_error(self, md):
        dutdetect = mock.Mock()
        md.return_value = dutdetect
        dutdetect.get_available_devices = mock.MagicMock(return_value=None)

        alloc = LocalAllocator()
        self.assertRaises(AllocationError, alloc._allocate, {"type": "hardware"})

    def test_internal_allocate_success_one_hardware_device_with_undefined_allowed_platforms(self, md):
        # Allocation should succeed if no allowed_platform defined in dut configuration, and devices are available
        dutdetect = mock.Mock()  # DutDetection instance mock
        md.return_value = dutdetect
        md.is_port_usable = mock.MagicMock(return_value=True)

        device = {"state": "unknown", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"}
        dutdetect.get_available_devices = mock.MagicMock(return_value=[device])

        alloc = LocalAllocator()
        dut = {"type": "hardware"}
        self.assertEqual(alloc._allocate(dut), True)

        # Test correct format of resulting dut configuration
        md.is_port_usable.assert_called_once_with(device["serial_port"])

    def test_internal_allocate_success_with_two_hardware_allocatable_devices_first_has_unusable_serial(self, md):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        md.return_value = dutdetect
        md.is_port_usable = mock.MagicMock(side_effect=[False, True])

        devices = [{"state": "unknown", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"},
                   {"state": "unknown", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        dut = {"type": "hardware"}
        self.assertEqual(alloc._allocate(dut), True)
        self.assertEqual(md.is_port_usable.call_count, 2)

    def test_internal_allocate_success_with_two_hardware_allocatable_devices_first_has_nonmatching_platform(self, md):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        md.return_value = dutdetect
        md.is_port_usable = mock.MagicMock(return_value=True)

        dut = {"type": "hardware", "allowed_platforms": ["K64F"]}
        devices = [{"state": "unknown", "platform_name": "unknown", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial1"},
                   {"state": "unknown", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial2"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        # Test correct format of resulting dut configuration
        self.assertEqual(alloc._allocate(dut), True)

        resultingdut = dut
        resultingdevice = devices[1]
        resultingdevice["state"] = "allocated"
        resultingdut["allocated"] = resultingdevice

        md.is_port_usable.assert_called_once_with(resultingdevice["serial_port"])

    def test_internal_allocate_success_with_two_hardware_allocatable_devices_with_matching_platforms_first_already_allocated(self, md):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        md.return_value = dutdetect
        md.is_port_usable = mock.MagicMock(return_value=True)

        dut = {"type": "hardware", "allowed_platforms": ["K64F"]}
        devices = [{"state": "allocated", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial1"},
                   {"state": "unknown", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial2"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        # Test correct format of resulting dut configuration
        self.assertEqual(alloc._allocate(dut), True)

        resultingdut = dut
        resultingdevice = devices[1]
        resultingdevice["state"] = "allocated"
        resultingdut["allocated"] = resultingdevice

        md.is_port_usable.assert_called_once_with(resultingdevice["serial_port"])

    def test_allocate_twice_success_when_two_devices_available(self, md):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        mdf = mock.MagicMock()  # DutFactory mock

        dutdetect = mock.Mock()  # DutDetection instance mock
        md.return_value = dutdetect
        md.is_port_usable = mock.MagicMock(return_value=True)

        devices = [{"state": "unknown", "platform_name": "K64F", "target_id": "1234", "serial_port": "/dev/serial1"},
                   {"state": "unknown", "platform_name": "K64F", "target_id": "5678", "serial_port": "/dev/serial2"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        duts = [{"type": "hardware", "allowed_platforms": ["K64F"]},
                {"type": "hardware", "allowed_platforms": ["K64F"]}]
        self.assertEqual(alloc.allocate(duts, mdf), True)

        # Result of first dut allocation
        resultingdut1 = duts[0]
        resultingdevice1 = devices[0]
        resultingdevice1["state"] = "allocated"
        resultingdut1["allocated"] = resultingdevice1
        # Result of second dut allocation
        resultingdut2 = duts[1]
        resultingdevice2 = devices[1]
        resultingdevice2["state"] = "allocated"
        resultingdut2["allocated"] = resultingdevice2
        self.assertEqual(mdf.call_count, 2)
        md.is_port_usable.assert_has_calls([mock.call(resultingdevice1["serial_port"]), mock.call(resultingdevice2["serial_port"])])

    def test_allocate_fail_with_two_hardware_allocatable_devices_both_already_allocated(self, md):
        # Allocation should raise AllocationError if no unallocated devices
        dutdetect = mock.Mock()  # DutDetection instance mock
        md.return_value = dutdetect

        devices = [{"state": "allocated", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"},
                   {"state": "allocated", "platform_name": "K64F", "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        dut = {"type": "hardware"}
        self.assertRaises(AllocationError, alloc.allocate, {"type": "hardware"})

if __name__ == '__main__':
    unittest.main()