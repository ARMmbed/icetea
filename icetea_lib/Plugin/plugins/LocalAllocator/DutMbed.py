"""
Copyright 2019 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

DutMbed module contains the DutMbed Dut subclass.
"""
# pylint: disable=too-many-branches,too-many-arguments
from prettytable import PrettyTable

from icetea_lib.LogManager import get_external_logger
from icetea_lib.Plugin.plugins.LocalAllocator.DutSerial import DutSerial
from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.build import Build

try:
    from mbed_flasher.flash import Flash
except ImportError:
    Flash = None

try:
    from mbed_flasher.common import FlashError

    FLASHER_ERRORS = (FlashError, SyntaxError, NotImplementedError)
except ImportError:
    FlashError = None
    FLASHER_ERRORS = (SyntaxError, NotImplementedError)


class DutMbed(DutSerial):
    """
    DutMbed, child of DutSerial. Mbed device over serial connection.
    """
    def __init__(self, name='mbed', port=None, baudrate=115200, config=None,
                 ch_mode_config=None, serial_config=None, params=None):
        """
        Mbed device over serial connection.

        :param name: Dut name
        :param port: Serial port name
        :param baudrate: Baudrate, int
        :param config: configuration dict
        :param ch_mode_config: dict
        :param serial_config: dict
        :param params: dict
        """
        super(DutMbed, self).__init__(name, port, baudrate, config, ch_mode_config,
                                      serial_config, params)

    def flash(self, binary_location=None, forceflash=None):
        """
        Flash a binary to the target device using mbed-flasher.

        :param binary_location: Binary to flash to device.
        :param forceflash: Not used.
        :return: False if an unknown error was encountered during flashing.
        True if flasher retcode == 0
        :raises: ImportError if mbed-flasher not installed.
        :raises: DutConnectionError if flashing fails.
        """
        if not Flash:
            self.logger.error("Mbed-flasher not installed!")
            raise ImportError("Mbed-flasher not installed!")

        try:
            # create build object
            self.build = Build.init(binary_location)
        except NotImplementedError as error:
            self.logger.error("Build initialization failed. "
                              "Check your build location.")
            self.logger.debug(error)
            raise DutConnectionError(error)

        # check if need to flash - depend on forceflash -option
        if not self._flash_needed(forceflash=forceflash):
            self.logger.info("Skipping flash, not needed.")
            return True
        # initialize mbed-flasher with proper logger
        logger = get_external_logger("mbed-flasher", "FLS")
        flasher = Flash(logger=logger)

        if not self.device:
            self.logger.error("Trying to flash device but device is not there?")
            return False

        try:
            buildfile = self.build.get_file()
            if not buildfile:
                raise DutConnectionError("Binary {} not found".format(buildfile))
            self.logger.info('Flashing dev: %s', self.device['target_id'])
            target_id = self.device.get("target_id")
            retcode = flasher.flash(build=buildfile, target_id=target_id,
                                    device_mapping_table=[self.device])
        except FLASHER_ERRORS as error:
            if error.__class__ == NotImplementedError:
                self.logger.error("Flashing not supported for this platform!")
            elif error.__class__ == SyntaxError:
                self.logger.error("target_id required by mbed-flasher!")
            if FlashError is not None:
                if error.__class__ == FlashError:
                    self.logger.error("Flasher raised the following error: %s Error code: %i",
                                      error.message, error.return_code)
            raise DutConnectionError(error)
        if retcode == 0:
            self.dutinformation.build_binary_sha1 = self.build.sha1
            return True
        self.dutinformation.build_binary_sha1 = None
        return False

    def _flash_needed(self, **kwargs):
        """
        Check if flashing is needed. Flashing can be skipped if resource binary_sha1 attribute
        matches build sha1 and forceflash is not True.

        :param kwargs: Keyword arguments (forceflash: Boolean)
        :return: Boolean
        """
        forceflash = kwargs.get("forceflash", False)
        cur_binary_sha1 = self.dutinformation.build_binary_sha1
        if not forceflash and self.build.sha1 == cur_binary_sha1:
            return False
        return True

    def print_info(self):
        """
        Prints Dut information nicely formatted into a table.

        :return: Nothing
        """
        table = PrettyTable()
        start_string = "DutMbed {} \n".format(self.name)
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
