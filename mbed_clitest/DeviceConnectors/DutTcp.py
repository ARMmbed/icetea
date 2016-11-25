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

import socket
from ..tools import strip_escape
from ..tools import num
from Dut import Dut

class DutTcp(Dut):
    ''' Draft version of TCP -dut type
    '''
    def __init__(self, name='tcp'):
        Dut.__init__(self, name=name)
        self.port = False
        self.type = 'socket'

    def openConnection(self):
        self.logger.debug("Open COM %s"%(self.comport))
        self.port = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        (ip, port) = self.comport.split(':')
        self.port.connect( ip, num(port) )

    def closeConnection(self):
        if self.port:
            self.port.close()
            self.logger.debug("Close TCP port")

    def writeline(self, data):
        self.port.send(data)

    def readline(self, timeout=1):
        f = self.port.makefile()
        line = f.readline(timeout=timeout)
        return strip_escape(line.strip())

    def printInfo(self):
        pass

