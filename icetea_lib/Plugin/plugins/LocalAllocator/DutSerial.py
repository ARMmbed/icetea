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

DutSerial module contains the DutSerial Dut subclass and two parameter objects, which contain
serial and chunk mode parameters.
"""

# Disable too many arguments warning and string statement has no effect warning
# Disable Too few public methods warning, too many public methods warning
# pylint: disable=R0913,W0105,R0903,R0904
# pylint: disable=too-many-instance-attributes,unused-argument

import time
from collections import deque
from threading import Thread
from serial import SerialException
from prettytable import PrettyTable

from icetea_lib.DeviceConnectors.Dut import Dut, DutConnectionError
from icetea_lib.enhancedserial import EnhancedSerial
from icetea_lib.tools.tools import strip_escape, split_by_n
from icetea_lib.DeviceConnectors.DutInformation import DutInformation


class SerialParams(object):
    """
    SerialParams object for storing serial connection parameters.
    """
    def __init__(self, timeout=0.01, xonxoff=False, rtscts=False, baudrate=460800):
        self.timeout = timeout
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.baudrate = baudrate

    def get_params(self):
        """
        Get parameters as a tuple.

        :return: timeout, xonxoff, rtscts, baudrate
        """
        return self.timeout, self.xonxoff, self.rtscts, self.baudrate


class ChunkModeParams(object):
    """
    ChunkModeParams object for storing chunk mode parameters
    """
    def __init__(self, on=False, size=1, chunk_delay=0.01, start_delay=0):
        self.enabled = on
        self.size = size
        self.chunk_delay = chunk_delay
        self.start_delay = start_delay

    def get_params(self):
        """
        Get parameters.

        :return: enabled, size, chunk_delay, start_delay
        """
        return self.enabled, self.size, self.chunk_delay, self.start_delay


class DutSerial(Dut):
    """
    DutSerial Object. Inherits from Dut object. Represents a local hardware device connected to USB
    """
    def __init__(self, name='serial', port=None, baudrate=460800, config=None,
                 ch_mode_config=None, serial_config=None, params=None):
        Dut.__init__(self, name=name, params=params)
        ch_mode_config = ch_mode_config if ch_mode_config is not None else {}
        serial_config = serial_config if serial_config is not None else {}
        self.readthread = None
        self.port = False
        self.comport = port
        self.type = 'serial'
        self.name = port
        self.platform = ''
        self.serialparams = SerialParams(timeout=serial_config.get("serial_timeout", 0.01),
                                         xonxoff=serial_config.get("serial_xonxoff", False),
                                         rtscts=serial_config.get("serial_rtscts", False),
                                         baudrate=baudrate)

        self.chunkmodeparams = ChunkModeParams(on=ch_mode_config.get("ch_mode", False),
                                               size=ch_mode_config.get("ch_mode_chunk_size", 1),
                                               chunk_delay=ch_mode_config.get("ch_mode_ch_delay",
                                                                              0.01),
                                               start_delay=ch_mode_config.get("ch_mode_start_delay",
                                                                              0))
        self.input_queue = deque()  # Input queue
        self.daemon = True  # Allow Python to stop us
        self.keep_reading = False

        if config:
            self.config.update(config)
            self.device = config.get("allocated", None)
            init_cli_cmds = None
            if "init_cli_cmds" in config["application"]:
                init_cli_cmds = config["application"]["init_cli_cmds"]
            if init_cli_cmds is not None:
                self.set_init_cli_cmds(init_cli_cmds)
            post_cli_cmds = None
            if "post_cli_cmds" in config["application"]:
                post_cli_cmds = config["application"]["post_cli_cmds"]
            if post_cli_cmds is not None:
                self.set_post_cli_cmds(post_cli_cmds)
        tid = self.config.get('allocated', {}).get('target_id', "unknown")
        self.dutinformation = DutInformation("serial",
                                             tid,
                                             index=self.index, build=self.build)

    """Properties"""

    @property
    def ch_mode(self):
        """
        :return: True if chunk mode enabled, False otherwise
        """
        return self.chunkmodeparams.enabled

    @ch_mode.setter
    def ch_mode(self, value):
        self.chunkmodeparams.enabled = value

    @property
    def ch_mode_chunk_size(self):
        """
        :return: Chunk size
        """
        return self.chunkmodeparams.size

    @ch_mode_chunk_size.setter
    def ch_mode_chunk_size(self, value):
        self.chunkmodeparams.size = value

    @property
    def ch_mode_ch_delay(self):
        """
        :return: Chunk delay
        """
        return self.chunkmodeparams.chunk_delay

    @ch_mode_ch_delay.setter
    def ch_mode_ch_delay(self, value):
        self.chunkmodeparams.chunk_delay = value

    @property
    def ch_mode_start_delay(self):
        """
        :return: Chunk start delay
        """
        return self.chunkmodeparams.start_delay

    @ch_mode_start_delay.setter
    def ch_mode_start_delay(self, value):
        self.chunkmodeparams.start_delay = value

    @property
    def serial_baudrate(self):
        """
        Getter for serial baudrate.

        :return: int
        """
        return self.serialparams.baudrate

    @serial_baudrate.setter
    def serial_baudrate(self, value):
        self.serialparams.baudrate = value

    @property
    def serial_timeout(self):
        """
        :return: Serial timeout
        """
        return self.serialparams.timeout

    @serial_timeout.setter
    def serial_timeout(self, value):
        """
        Setter for serial connection timeout.

        :param value: Value to set
        :return: Nothing
        """
        self.serialparams.timeout = value

    @property
    def serial_xonxoff(self):
        """
        :return: xonxoff value as as Boolean
        """
        return self.serialparams.xonxoff

    @serial_xonxoff.setter
    def serial_xonxoff(self, value):
        self.serialparams.xonxoff = value

    @property
    def serial_rtscts(self):
        """
        :return: Rtscts as boolean
        """
        return self.serialparams.rtscts

    @serial_rtscts.setter
    def serial_rtscts(self, value):
        self.serialparams.rtscts = value

    """Methods"""

    def get_resource_id(self):
        """
        Get resource id (target id) from config dictionary.

        :return: target_id or None if not found
        """
        return self.config.get('allocated').get('target_id')

    def flash(self, binary_location=None, forceflash=None):  # pylint: disable=too-many-branches
        """
        Nothing, not implemented.
        """
        self.logger.warning("Flashing is not supported for this dut type.")
        return True

    def get_info(self):
        """
        Get DutInformation object from this Dut.

        :return: DutInformation object
        """
        return self.dutinformation

    # open serial port connection
    def open_connection(self):
        """
        Open serial port connection.

        :return: Nothing
        :raises: DutConnectionError if serial port was already open or a SerialException occurs.
        ValueError if EnhancedSerial __init__ or value setters raise ValueError
        """
        if self.readthread is not None:
            raise DutConnectionError("Trying to open serial port which was already open")

        self.logger.info("Open Connection "
                         "for '%s' using '%s' baudrate: %d" % (self.dut_name,
                                                               self.comport,
                                                               self.serial_baudrate),
                         extra={'type': '<->'})
        if self.serial_xonxoff:
            self.logger.debug("Use software flow control for dut: %s" % self.dut_name)
        if self.serial_rtscts:
            self.logger.debug("Use hardware flow control for dut: %s" % self.dut_name)
        try:
            self.port = EnhancedSerial(self.comport)
            self.port.baudrate = self.serial_baudrate
            self.port.timeout = self.serial_timeout
            self.port.xonxoff = self.serial_xonxoff
            self.port.rtscts = self.serial_rtscts
            self.port.flushInput()
            self.port.flushOutput()
        except SerialException as err:
            self.logger.warning(err)
            raise DutConnectionError(str(err))
        except ValueError as err:
            self.logger.warning(err)
            raise ValueError(str(err))

        if self.ch_mode:
            self.logger.info("Use chunk-mode with size %d, delay: %.3f when write data" %
                             (self.ch_mode_chunk_size, self.ch_mode_ch_delay),
                             extra={'type': '<->'})
            time.sleep(self.ch_mode_start_delay)
        else:
            self.logger.info("Use normal serial write mode", extra={'type': '<->'})
        if self.params.reset:
            self.reset()
        # Start the serial reading thread
        self.readthread = Thread(name=self.name, target=self.run)
        self.readthread.start()

    def prepareConnectionClose(self):  # pylint: disable=C0103
        """
        Deprecated version of prepare_connection_close. Still present for backwards compatibility.

        :return: Nothing
        """
        self.logger.warning("prepareConnectionClose deprecated, use prepare_connection_close")
        self.prepare_connection_close()

    def prepare_connection_close(self):
        """
        Sends post-cli-cmds and stops the read thread.

        :return: Nothing
        """
        try:
            self.init_cli_human()
        except KeyboardInterrupt:
            pass
        self.stop()

    # close serial port connection
    def close_connection(self):  # pylint: disable=C0103
        """
        Closes serial port connection.

        :return: Nothing
        """
        if self.port:
            self.stop()
            self.logger.debug("Close port '%s'" % self.comport,
                              extra={'type': '<->'})
            self.port.close()
            self.port = False

    def reset(self, method=None):
        """
        Resets the serial device. Internally calls __send_break().

        :param method: Not used for DutSerial
        :return: Nothing
        """
        self.logger.info('Reset serial device %s' % self.name)
        self.__send_break()

    def __sendBreak(self):  # pylint: disable=C0103
        """
        Deprecated, present for backwards compatibility.

        :return: result of EnhancedSerial safe_sendBreak()
        """
        self.logger.warning("__send_Break deprecated, use __send_break")
        return self.__send_break()

    def __send_break(self):
        """
        Sends break to device.

        :return: result of EnhancedSerial safe_sendBreak()
        """
        if self.port:
            self.logger.debug("sendBreak to device to reboot", extra={'type': '<->'})
            result = self.port.safe_sendBreak()
            time.sleep(1)
            if result:
                self.logger.debug("reset completed", extra={'type': '<->'})
            else:
                self.logger.warning("reset failed", extra={'type': '<->'})
            return result
        return None

    # transfer data to the serial port
    def writeline(self, data):
        """
        Writes data to serial port.

        :param data: Data to write
        :return: Nothing
        :raises: IOError if SerialException occurs.
        """
        try:
            if self.ch_mode:
                data += "\n"
                parts = split_by_n(data, self.ch_mode_chunk_size)
                for split_str in parts:
                    self.port.write(split_str.encode())
                    time.sleep(self.ch_mode_ch_delay)
            else:
                self.port.write((data + "\n").encode())
        except SerialException as err:
            self.logger.exception("SerialError occured while trying to write data {}.".format(data))
            raise RuntimeError(str(err))

    # read line from serial port
    def _readline(self, timeout=1):
        """
        Read line from serial port.

        :param timeout: timeout, default is 1
        :return: stripped line or None
        """
        line = self.port.readline(timeout=timeout)
        return strip_escape(line.strip()) if line is not None else line

    def peek(self):
        """
        Peek into the port line buffer to see if there are incomplete lines.

        :return: str
        """
        if self.port:
            return self.port.peek()
        return ""

    def run(self):
        """
        Read lines while keep_reading is True. Calls process_dut for each received line.

        :return: Nothing
        """
        self.keep_reading = True
        while self.keep_reading:
            line = self._readline()
            if line:
                self.input_queue.appendleft(line)
                Dut.process_dut(self)

    def stop(self):
        """
        Stops and joins readthread.

        :return: Nothing
        """
        self.keep_reading = False
        if self.readthread is not None:
            self.readthread.join()
            self.readthread = None

    def readline(self, timeout=1):
        """
        Pops from input_queue.

        :param timeout: Not used
        :return: first item in input_queue or None
        """
        try:
            return self.input_queue.pop()
        except IndexError:
            pass
        return None

    def print_info(self):
        """
        Prints Dut information nicely formatted into a table.
        """
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
            row.append("X = {}, Y = {}".format(self.location.x_coord, self.location.y_coord))
        self.logger.info(start_string)
        self.logger.debug(info_string)
        table.add_row(row)
        print(table)

    def get_config(self):
        """
        Gets configuration dictionary.

        :return: configuration as a dictionary
        """
        return self.config

    def _flash_needed(self, **kwargs):
        """
        Check if flashing is needed. Flashing can be skipped if resource binary_sha1 attribute
        matches build sha 1 and forceflash is not True.

        :param kwargs: Keyword arguments (forceflash: Boolean)
        :return: Boolean
        """
        return False
