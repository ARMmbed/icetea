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

from pkgutil import iter_modules
from serial.tools import list_ports
import serial

class DutDetection:

    def __init__(self):
        self.mbeds = None
        if( self.module_exists('mbed_lstools')):
            from mbed_lstools.main import create
            self.mbeds = create()

    @staticmethod
    def is_port_usable(portName):
        try:
           ser = serial.Serial(port=portName)
           return True
        except:
           return False

    def module_exists(self, module_name):
        return module_name in (name for loader, name, ispkg in iter_modules())

    def get_available_devices(self):
        connected_devices = self.mbeds.list_mbeds() if self.mbeds else []
        # Check non mbedOS supported devices.
        # Just for backward compatible reason - is obsolete..
        EDBG_ports = self.available_edbg_ports()
        for port in EDBG_ports:
            connected_devices.append( {
                "platform_name": "SAM4E",
                "serial_port": port,
                "mount_point": None,
                "target_id": None,
                "baud_rate": 460800
            })
        for dev in connected_devices:
            dev['state'] = "unknown"

        return connected_devices

    # Find available EDBG COM ports
    def available_edbg_ports(self):
        ports_available = sorted(list(list_ports.comports()))
        edbg_ports = []
        for iPort in ports_available:
            port = iPort[0]
            desc = iPort[1]
            hwid = iPort[2]
            if str(desc).startswith("EDBG Virtual COM Port") or "VID:PID=03EB:2111" in str(hwid).upper():
                # print("%-10s: %s (%s)\n" % (port, desc, hwid))
                try:
                    edbg_ports.index(port, 0)
                    print("There is multiple %s ports with same number!" % port )
                except:
                    edbg_ports.append(port)
        # print("Detected %i DUT's" % len(edbg_ports))
        return edbg_ports
