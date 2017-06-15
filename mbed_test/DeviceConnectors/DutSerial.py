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

import time
from serial import SerialException
from collections import deque
from threading import Thread
from Dut import Dut
from ..enhancedserial import EnhancedSerial
from ..tools import strip_escape
from prettytable import PrettyTable

class DutSerial(Dut, Thread):
    def __init__(self, name='serial', port=None, baudrate = 460800):
        Thread.__init__(self, name=name)
        Dut.__init__(self, name=name)
        self.port = False
        self.comport = port
        self.type = 'serial'
        self.name = port
        self.serialBaudrate = baudrate
        self.serial_timeout = 0.01
        self.serial_xonxoff = False
        self.serial_rtscts = False

        # chunk mode. When enabled: default: single character is the chunk.
        self.ch_mode = False
        self.ch_mode_chunk_size = 1
        self.ch_mode_ch_delay = 0.01
        self.ch_mode_start_delay = 0

        self.rq = deque() # Input queue
        self.daemon = True # Allow Python to stop us
        self.keep_reading = False

    # open serial port connection
    def openConnection(self):
        self.logger.info("Open Connection for '%s' using '%s' baudrate: %d" % (self.dutName, self.comport, self.serialBaudrate), extra={'type': '<->'})
        if self.serial_xonxoff:
            self.logger.debug("Use software flow control for dut: %s" % self.dutName)
        if self.serial_rtscts:
            self.logger.debug("Use hardware flow control for dut: %s" % self.dutName)
        try:
            self.port = EnhancedSerial(self.comport)
            self.port.baudrate = self.serialBaudrate
            self.port.timeout = self.serial_timeout
            self.port.xonxoff = self.serial_xonxoff
            self.port.rtscts = self.serial_rtscts
            self.port.flushInput()
            self.port.flushOutput()
        except SerialException as err:
            self.logger.warning(err)
            raise ValueError(str(err))
        except ValueError as err:
            self.logger.warning(err)
            raise ValueError(str(err))

        if self.ch_mode:
            self.logger.info("Use chunk-mode with size %d, delay: %.3f when write data" % (self.ch_mode_chunk_size, self.ch_mode_ch_delay), extra={'type': '<->'})
            time.sleep(self.ch_mode_start_delay)
        else:
            self.logger.info("Use normal serial write mode", extra={'type': '<->'})
        self.start() # Start reader thread.


    def prepareConnectionClose(self):
        self.initCLIhuman()
        self.stop()

    # close serial port connection
    def closeConnection(self):
        if self.port:
            self.stop()
            self.logger.debug("Close port '%s'" % self.comport,
                extra={'type': '<->'})
            self.port.close()

    def reset(self, method=None):
        self.logger.info('Reset serial device %s' % self.name)
        self.__sendBreak()

    def __sendBreak(self):
        if self.port:
            self.logger.debug("sendBreak to device to reboot", extra={'type': '<->'})
            result = self.port.safe_sendBreak()
            time.sleep(1)
            if result:
                self.logger.debug("reset completed", extra={'type': '<->'})
            else:
                self.logger.warning("reset failed", extra={'type': '<->'})
            return result

    def split_by_n(self, seq, n ):
        """A generator to divide a sequence into chunks of n units."""
        while seq:
            yield seq[:n]
            seq = seq[n:]

    # transfer data to the serial port
    def writeline(self, data):
        try:
            if self.ch_mode:
                data += "\n"
                parts = self.split_by_n(data, self.ch_mode_chunk_size)
                for s in parts:
                    self.port.write(s.encode())
                    time.sleep(self.ch_mode_ch_delay)
            else:
                self.port.write((data + "\n").encode())
        except SerialException as err:
            raise IOError(str(err))

    # read line from serial port
    def _readline(self, timeout=1):
        line = self.port.readline(timeout=timeout)
        return strip_escape(line.strip())

    def run(self):
        self.keep_reading = True
        while self.keep_reading:
            line = self._readline()
            if line:
                self.rq.appendleft(line)
                Dut.process_dut(self)

    def stop(self):
        self.keep_reading = False
        self.join()

    def readline(self):
        try:
            return self.rq.pop()
        except IndexError:
            pass
        return None

    def printInfo(self):
        table = PrettyTable()
        start_string = "DutSerial {} \n".format(self.name)
        row = []
        info_string = ""
        if self.config:
            info_string = info_string + "Configuration for this DUT:\n\n {} \n".format(self.config)
        if self.comport:
            table.add_column("COM port", [])
            row.append(self.comport)
        if self.port:
            if hasattr(self.port, "baudrate"):
                table.add_column("Baudrate", [])
                row.append(self.port.baudrate)
            if hasattr(self.port, "xonxoff"):
                table.add_column("XON/XOFF", [])
                row.append(self.port.xonxoff)
            if hasattr(self.port, "timeout"):
                table.add_column("Timeout", [])
                row.append(self.port.timeout)
            if hasattr(self.port, "rtscts"):
                table.add_column("RTSCTS", [])
                row.append(self.port.rtscts)
        if self.location:
            table.add_column("Location", [])
            row.append("X = {}, Y = {}".format(self.location.x, self.location.y))
        self.logger.info(start_string)
        self.logger.debug(info_string)
        table.add_row(row)
        print(table)
