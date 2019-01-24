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

DutDetection module. Uses mbedls to detect available devices for LocalAllocator.
"""

# Disable "Method could be function" warning
# pylint: disable=R0201

from serial.tools import list_ports
from serial import SerialException, Serial

from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError


class DutDetection(object):
    """
    DutDetection class. Contains methods to detect usable ports and available devices using
    mbedls and serial module.
    """

    def __init__(self):
        self.mbeds = None
        try:
            from mbed_lstools.main import create
            self.mbeds = create()
        except ImportError:
            raise AllocationError("mbedls is missing")

    @staticmethod
    def is_port_usable(port_name):
        """
        Static is_port_usable method. Tries to create instance of Serial object. to confirm that
        the port is usable.

        :param port_name: Name of port
        :return: True or False
        """
        try:
            #Disable "unused variable" warning
            #pylint: disable=W0612
            ser = Serial(port=port_name)
            return True
        except SerialException:
            return False

    def get_available_devices(self):
        """
        Gets available devices using mbedls and self.available_edbg_ports.

        :return: List of connected devices as dictionaries.
        """
        connected_devices = self.mbeds.list_mbeds() if self.mbeds else []
        # Check non mbedOS supported devices.
        # Just for backward compatible reason - is obsolete..
        edbg_ports = self.available_edbg_ports()
        for port in edbg_ports:
            connected_devices.append({
                "platform_name": "SAM4E",
                "serial_port": port,
                "mount_point": None,
                "target_id": None,
                "baud_rate": 460800
            })
        for dev in connected_devices:
            dev['state'] = "unknown"

        return connected_devices

    def available_edbg_ports(self):
        """
        Finds available EDBG COM ports.

        :return: list of available ports
        """
        ports_available = sorted(list(list_ports.comports()))
        edbg_ports = []
        for iport in ports_available:
            port = iport[0]
            desc = iport[1]
            hwid = iport[2]
            if str(desc).startswith("EDBG Virtual COM Port") or \
                            "VID:PID=03EB:2111" in str(hwid).upper():
                # print("%-10s: %s (%s)\n" % (port, desc, hwid))
                try:
                    edbg_ports.index(port, 0)
                    print("There is multiple %s ports with same number!" % port)
                except ValueError:
                    edbg_ports.append(port)
        # print("Detected %i DUT's" % len(edbg_ports))
        return edbg_ports
