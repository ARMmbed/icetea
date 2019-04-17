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

# pylint: disable=missing-docstring,old-style-class,protected-access,no-self-use,invalid-name
# pylint: disable=attribute-defined-outside-init,too-few-public-methods,unused-argument
# pylint: disable=too-many-public-methods

import unittest
import logging
import mock

from icetea_lib.AllocationContext import AllocationContextList
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError
from icetea_lib.ResourceProvider.ResourceRequirements import ResourceRequirements
from icetea_lib.ResourceProvider.exceptions import ResourceInitError

from icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator import LocalAllocator, init_process_dut
from icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator import init_mbed_dut


@mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.DutDetection", create=False)
@mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.get_resourceprovider_logger",
            create=True)
class TestVerify(unittest.TestCase):

    def setUp(self):
        self.nulllogger = logging.getLogger("test")
        self.nulllogger.addHandler(logging.NullHandler())

    def test_init_with_no_logger(self, mock_logging, mock_dutdetection):
        dutdetect = mock.Mock()
        mock_dutdetection.return_value = dutdetect
        dutdetect.get_available_devices = mock.MagicMock(return_value=None)
        mock_logger = mock.Mock()
        mock_logging.get_logger = mock.MagicMock(return_value=mock_logger)
        mock_logging.NullHandler = mock.MagicMock()

        LocalAllocator()

        mock_dutdetection.assert_not_called()
        dutdetect.get_available_devices.assert_not_called()
        mock_logging.assert_called_once_with("LocalAllocator", "LAL")

    def test_can_allocate_success(self, mock_logging, mock_dutdetection):
        alloc = LocalAllocator()
        data1 = {"type" : "hardware"}
        self.assertTrue(alloc.can_allocate(data1))

    def test_can_allocate_unknown_type(self, mock_logging, mock_dutdetection):
        dutdetect = mock.Mock()
        mock_dutdetection.return_value = dutdetect
        dutdetect.get_available_devices = mock.MagicMock(return_value=None)

        alloc = LocalAllocator()
        data_unknown_type = {"type" : "unknown"}
        self.assertFalse(alloc.can_allocate(data_unknown_type))

        mock_dutdetection.assert_not_called()
        dutdetect.get_available_devices.assert_not_called()

        data_unknown_type = {"type" : None}
        self.assertFalse(alloc.can_allocate(data_unknown_type))

    def test_can_allocate_missing_type(self, mock_logging, mock_dutdetection):
        alloc = LocalAllocator()
        data_no_type = {"notype": None}
        self.assertFalse(alloc.can_allocate(data_no_type))

    def test_allocate_raises_on_invalid_dut_format(self, mock_logging, mock_dutdetection):
        alloc = LocalAllocator()
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = "Not a list"
        self.assertRaises(AllocationError, alloc.allocate, mfunc)

    def test_allocate_raises_devices_not_available(self, mock_logging, mock_dutdetection):
        detected = [1]
        mock_dutdetection.get_available_devices = mock.MagicMock(return_value=detected)
        alloc = LocalAllocator()
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [{"type": "hardware"}, {"type": "hardware"}]
        with self.assertRaises(AllocationError):
            alloc.allocate(mfunc)

    def test_internal_allocate_no_type_raises(self, mock_logging, mock_dutdetection):
        alloc = LocalAllocator()
        data = {"notype": None}
        self.assertRaises(KeyError, alloc._allocate, data)

    def test_internal_allocate_non_hardware_types_success(self, mock_logging, mock_dutdetection):
        dutdetect = mock.Mock()
        mock_dutdetection.return_value = dutdetect
        dutdetect.get_available_devices = mock.MagicMock(return_value=None)

        alloc = LocalAllocator()
        dut = ResourceRequirements({"type": "process"})
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [dut]
        self.assertTrue(alloc.allocate(mfunc))

        mock_dutdetection.assert_not_called()
        dutdetect.get_available_devices.assert_not_called()

    def test_internal_allocate_non_hardware_types_success_without_dutfactory(self, mock_logging,
                                                                             mock_dutdetection):
        alloc = LocalAllocator()
        dut = ResourceRequirements({"type": "process"})
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [dut]
        self.assertTrue(alloc.allocate(mfunc))

    def test_internal_allocate_hardware_platform_no_devices_raises_error(self, mock_logging,
                                                                         mock_dutdetection):
        dutdetect = mock.Mock()
        mock_dutdetection.return_value = dutdetect
        dutdetect.get_available_devices = mock.MagicMock(return_value=None)

        alloc = LocalAllocator()
        self.assertRaises(AllocationError, alloc._allocate,
                          ResourceRequirements({"type": "hardware"}))

    def test_inter_alloc_suc_one_hardware_device_with_undef_allowed_platf(self, mock_logging,
                                                                          mock_dutdetection):
        # Allocation should succeed if no allowed_platform defined in dut configuration,
        # and devices are available
        dutdetect = mock.Mock()  # DutDetection instance mock
        mock_dutdetection.return_value = dutdetect
        mock_dutdetection.is_port_usable = mock.MagicMock(return_value=True)

        device = {"state": "unknown", "platform_name": "K64F",
                  "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"}
        dutdetect.get_available_devices = mock.MagicMock(return_value=[device])

        alloc = LocalAllocator()
        dut = ResourceRequirements({"type": "hardware"})
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [dut]
        self.assertEqual(len(alloc.allocate(mfunc)), 1)

        dutdetect.get_available_devices.assert_called_once_with()

        # Test correct format of resulting dut configuration
        mock_dutdetection.is_port_usable.assert_called_once_with(device["serial_port"])

    def test_inter_alloc_suc_w_two_hw_allocatable_dev_one_has_unusable_serial(self, mock_logging,
                                                                              mock_dutdetection):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        mock_dutdetection.return_value = dutdetect
        mock_dutdetection.is_port_usable = mock.MagicMock(side_effect=iter([False, True]))

        devices = [{"state": "unknown", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"},
                   {"state": "unknown", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        dut = ResourceRequirements({"type": "hardware"})
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [dut]
        self.assertEqual(len(alloc.allocate(mfunc)), 1)
        self.assertEqual(mock_dutdetection.is_port_usable.call_count, 2)

    def test_inter_alloc_suc_w_two_hw_allocatable_dev_one_has_nonmatch_platf(self, mock_logging,
                                                                             mock_dutdetection):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        mock_dutdetection.return_value = dutdetect
        mock_dutdetection.is_port_usable = mock.MagicMock(return_value=True)

        dut = ResourceRequirements({"type": "hardware", "allowed_platforms": ["K64F"]})
        devices = [{"state": "unknown", "platform_name": "unknown",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial1"},
                   {"state": "unknown", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial2"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        # Test correct format of resulting dut configuration
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [dut]
        self.assertEqual(len(alloc.allocate(mfunc)), 1)

        resultingdut = dut
        resultingdevice = devices[1]
        resultingdevice["state"] = "allocated"
        resultingdut.set("allocated", resultingdevice)

        mock_dutdetection.is_port_usable.assert_called_once_with(resultingdevice["serial_port"])

    def test_inter_alloc_suc_w_two_hw_allocatabl_dev_w_match_platf_one_alloc(self, mock_logging,
                                                                             mock_dutdetection):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        mock_dutdetection.return_value = dutdetect
        mock_dutdetection.is_port_usable = mock.MagicMock(return_value=True)

        dut = ResourceRequirements({"type": "hardware", "allowed_platforms": ["K64F"]})
        devices = [{"state": "allocated", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial1"},
                   {"state": "unknown", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial2"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        # Test correct format of resulting dut configuration
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [dut]
        self.assertEqual(len(alloc.allocate(mfunc)), 1)

        resultingdut = dut
        resultingdevice = devices[1]
        resultingdevice["state"] = "allocated"
        resultingdut.set("allocated", resultingdevice)

        mock_dutdetection.is_port_usable.assert_called_once_with(resultingdevice["serial_port"])

    def test_alloc_twice_suc_when_two_dev_available(self, mock_logging, mock_dutdetection):
        # Test with two devices, both are allocatable, but the serial port for first is unusable
        dutdetect = mock.Mock()  # DutDetection instance mock
        mock_dutdetection.return_value = dutdetect
        mock_dutdetection.is_port_usable = mock.MagicMock(return_value=True)

        devices = [{"state": "unknown",
                    "platform_name": "K64F", "target_id": "1234", "serial_port": "/dev/serial1"},
                   {"state": "unknown",
                    "platform_name": "K64F", "target_id": "5678", "serial_port": "/dev/serial2"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        duts = [ResourceRequirements({"type": "hardware", "allowed_platforms": ["K64F"]}),
                ResourceRequirements({"type": "hardware", "allowed_platforms": ["K64F"]})]
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = duts
        self.assertEqual(len(alloc.allocate(mfunc)), 2)

        # Result of first dut allocation
        resultingdut1 = duts[0]
        resultingdevice1 = devices[0]
        resultingdevice1["state"] = "allocated"
        resultingdut1.set("allocated", resultingdevice1)
        # Result of second dut allocation
        resultingdut2 = duts[1]
        resultingdevice2 = devices[1]
        resultingdevice2["state"] = "allocated"
        resultingdut2.set("allocated", resultingdevice2)
        mock_dutdetection.is_port_usable.assert_has_calls(
            [mock.call(resultingdevice1["serial_port"]),
             mock.call(resultingdevice2["serial_port"])])

    def test_alloc_fail_w_two_hw_allocatable_dev_both_already_allocated(self, mock_logging,
                                                                        mock_dutdetection):
        # Allocation should raise AllocationError if no unallocated devices
        dutdetect = mock.Mock()  # DutDetection instance mock
        mock_dutdetection.return_value = dutdetect
        mfunc = mock.MagicMock()
        mfunc.get_dut_configuration = mock.MagicMock()
        mfunc.get_dut_configuration.return_value = [ResourceRequirements({"type": "hardware"})]
        devices = [{"state": "allocated", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"},
                   {"state": "allocated", "platform_name": "K64F",
                    "target_id": "ABCDEFG12345", "serial_port": "/dev/serial"}]
        dutdetect.get_available_devices = mock.MagicMock(return_value=devices)

        alloc = LocalAllocator()
        self.assertRaises(AllocationError, alloc.allocate, mfunc)

    def test_local_allocator_release(self, mock_logging, mock_dutdetection):
        alloc = LocalAllocator()
        alloc.release()

    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.DutConsole")
    def test_init_console_dut(self, mock_dc, mock_logging, mock_dutdetection):
        conf = {}
        conf["subtype"] = "console"
        conf["application"] = "stuff"
        con_list = AllocationContextList(self.nulllogger)
        init_process_dut(con_list, conf, 1, mock.MagicMock())

        conf["subtype"] = "other"
        con_list = AllocationContextList(self.nulllogger)
        with self.assertRaises(ResourceInitError):
            self.assertIsNone(init_process_dut(con_list, conf, 1, mock.MagicMock()))

    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.DutMbed")
    def test_init_mbed_dut(self, mock_ds, mock_logging, mock_dutdetection):
        conf = {"allocated": {"serial_port": "port", "baud_rate": 115200,
                              "platform_name": "test", "target_id": "id"},
                "application": {"bin": "binary"}}
        args = mock.MagicMock()
        rtscts = mock.PropertyMock(return_value=True)
        s_xonxoff = mock.PropertyMock(return_value=True)
        s_timeout = mock.PropertyMock(return_value=True)
        s_ch_size = mock.PropertyMock(return_value=1)
        s_ch_delay = mock.PropertyMock(return_value=True)
        skip_flash = mock.PropertyMock(return_value=False)
        type(args).skip_flash = skip_flash
        type(args).serial_xonxoff = s_xonxoff
        type(args).serial_rtscts = rtscts
        type(args).serial_timeout = s_timeout
        type(args).serial_ch_size = s_ch_size
        type(args).ch_mode_ch_delay = s_ch_delay

        # Setup mocked dut
        dut1 = mock.MagicMock()
        dut1.close_dut = mock.MagicMock()
        dut1.close_connection = mock.MagicMock()
        dut1.flash = mock.MagicMock()
        dut1.flash.side_effect = [True, False]
        dut1.getInfo = mock.MagicMock(return_value="test")
        type(dut1).index = mock.PropertyMock()

        con_list = AllocationContextList(self.nulllogger)
        with mock.patch.object(con_list, "check_flashing_need") as mock_cfn:
            mock_cfn = mock.MagicMock()
            mock_cfn.return_value = True
            mock_ds.return_value = dut1
            init_mbed_dut(con_list, conf, 1, args)

            with self.assertRaises(ResourceInitError):
                init_mbed_dut(con_list, conf, 1, args)
            dut1.close_dut.assert_called()
            dut1.close_connection.assert_called()

    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.DutMbed")
    def test_init_mbed_dut_skip_flash(self, mock_ds, mock_logging, mock_dutdetection):
        conf = {"allocated": {"serial_port": "port", "baud_rate": 115200,
                              "platform_name": "test", "target_id": "id"},
                "application": {"bin": "binary"}}
        args = mock.MagicMock()
        rtscts = mock.PropertyMock(return_value=True)
        s_xonxoff = mock.PropertyMock(return_value=True)
        s_timeout = mock.PropertyMock(return_value=True)
        s_ch_size = mock.PropertyMock(return_value=1)
        s_ch_delay = mock.PropertyMock(return_value=True)
        skip_flash = mock.PropertyMock(return_value=True)
        type(args).skip_flash = skip_flash
        type(args).serial_xonxoff = s_xonxoff
        type(args).serial_rtscts = rtscts
        type(args).serial_timeout = s_timeout
        type(args).serial_ch_size = s_ch_size
        type(args).ch_mode_ch_delay = s_ch_delay

        # Setup mocked dut
        dut1 = mock.MagicMock()
        dut1.close_dut = mock.MagicMock()
        dut1.close_connection = mock.MagicMock()
        dut1.flash = mock.MagicMock()
        dut1.flash.side_effect = [True, False]
        dut1.getInfo = mock.MagicMock(return_value="test")
        type(dut1).index = mock.PropertyMock()

        con_list = AllocationContextList(self.nulllogger)
        with mock.patch.object(con_list, "check_flashing_need") as mock_cfn:
            mock_cfn = mock.MagicMock()
            mock_cfn.return_value = True
            mock_ds.return_value = dut1
            init_mbed_dut(con_list, conf, 1, args)
            dut1.flash.assert_not_called()

    @mock.patch("icetea_lib.Plugin.plugins.LocalAllocator.LocalAllocator.DutMbed")
    def test_init_mbed_dut_nondefault_baud_rate(self, mock_ds, mock_logging, mock_dutdetection):
        conf = {"allocated": {"serial_port": "port", "baud_rate": 115200,
                              "platform_name": "test", "target_id": "id"},
                "application": {"bin": "binary", "baudrate": 9600}}
        args = mock.MagicMock()

        rtscts = mock.PropertyMock(return_value=True)
        s_xonxoff = mock.PropertyMock(return_value=True)
        s_timeout = mock.PropertyMock(return_value=True)
        s_ch_size = mock.PropertyMock(return_value=1)
        s_ch_delay = mock.PropertyMock(return_value=True)
        skip_flash = mock.PropertyMock(return_value=False)
        type(args).skip_flash = skip_flash
        type(args).baudrate = mock.PropertyMock(return_value=False)
        type(args).serial_xonxoff = s_xonxoff
        type(args).serial_rtscts = rtscts
        type(args).serial_timeout = s_timeout
        type(args).serial_ch_size = s_ch_size
        type(args).ch_mode_ch_delay = s_ch_delay

        # Setup mocked dut
        dut1 = mock.MagicMock()
        dut1.close_dut = mock.MagicMock()
        dut1.closeConnection = mock.MagicMock()
        dut1.flash = mock.MagicMock()
        dut1.flash.side_effect = [True, False]
        dut1.getInfo = mock.MagicMock(return_value="test")
        type(dut1).index = mock.PropertyMock()

        con_list = AllocationContextList(self.nulllogger)
        with mock.patch.object(con_list, "check_flashing_need") as mock_cfn:
            mock_cfn = mock.MagicMock()
            mock_cfn.return_value = True
            mock_ds.return_value = dut1
            init_mbed_dut(con_list, conf, 1, args)
            mock_ds.assert_called_once_with(baudrate=9600,
                                            ch_mode_config={'ch_mode_ch_delay': True,
                                                            'ch_mode': True,
                                                            'ch_mode_chunk_size': 1},
                                            config={'application':
                                                        {'bin': 'binary', 'baudrate': 9600},
                                                    'allocated': {'baud_rate': 115200,
                                                                  'platform_name': 'test',
                                                                  'target_id': 'id',
                                                                  'serial_port': 'port'}},
                                            name='D1',
                                            port='port',
                                            serial_config={'serial_timeout': True,
                                                           'serial_rtscts': True},
                                            params=args)


if __name__ == '__main__':
    unittest.main()
