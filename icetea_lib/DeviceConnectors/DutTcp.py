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

DutTcp module. This is a prototype of a Dut-over-tcp implementation and is not used.
"""

import socket
from icetea_lib.tools import strip_escape
from icetea_lib.tools import num
from icetea_lib.DeviceConnectors.Dut import Dut

class DutTcp(Dut):
    '''
    Draft version of TCP -dut type
    '''
    def __init__(self, name='tcp'):
        Dut.__init__(self, name=name)
        self.port = None
        self.type = 'socket'

    def open_connection(self):
        """
        Open connection over TCP socket.
        :return: Nothing
        """
        self.logger.debug("Open COM %s", self.comport)
        self.port = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        (ip_addr, port) = self.comport.split(':')
        self.port.connect(ip_addr, num(port))

    def close_connection(self):
        """
        Close TCP port
        :return: Nothing
        """
        if self.port:
            self.port.close()
            self.logger.debug("Close TCP port")

    def writeline(self, data):
        """
        Write data to port
        :param data: data to write
        :return: Nothing
        """
        self.port.send(data)

    def readline(self, timeout=None):  # timeout is not in use
        """
        Read data from port and strip escape characters
        :param timeout:
        :return: Stripped line.
        """
        fil = self.port.makefile()
        line = fil.readline()
        return strip_escape(line.strip())

    def print_info(self):
        pass

    def _flash_needed(self):
        pass

    def get_info(self):
        pass
