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

DutProcess module.
"""

from icetea_lib.DeviceConnectors.Dut import Dut, DutConnectionError
from icetea_lib.tools.GenericProcess import GenericProcess
from icetea_lib.DeviceConnectors.DutInformation import DutInformation
from icetea_lib.build.build import Build
# pylint: disable=redefined-builtin


class DutProcess(Dut, GenericProcess):  # pylint: disable=too-many-instance-attributes
    """
    DutProcess class, subclasses both Dut and GenericProcess. Implements an interface for
    communicating with a process as if it were a device under test.
    """
    def __init__(self, type='process', name='process', config=None, params=None):
        Dut.__init__(self, name=name, params=params)
        GenericProcess.__init__(self, self.name, logger=self.logger)
        self.disable_io_prints()  # because those are printed in Dut object
        self.proc = False
        self.type = type
        self.config = config if config else {}
        self.dutinformation = DutInformation(self.type,
                                             self.resource_id if self.resource_id else "",
                                             index=None, build=None)
        self.command = None

    def open_connection(self):
        """
        Open connection by starting the process.

        :raises: DutConnectionError
        """
        self.logger.debug("Open CLI Process '%s'",
                          (self.comport), extra={'type': '<->'})
        self.cmd = self.comport if isinstance(self.comport, list) else [self.comport]
        if not self.comport:
            raise DutConnectionError("Process not defined!")
        try:
            self.build = Build.init(self.cmd[0])
        except NotImplementedError as error:
            self.logger.error("Build initialization failed. Check your build location.")
            self.logger.debug(error)
            raise DutConnectionError(error)
        # Start process&reader thread. Call Dut.process_dut() when new data is coming
        app = self.config.get("application")
        if app and app.get("bin_args"):
            self.cmd = self.cmd + app.get("bin_args")
        try:
            self.start_process(self.cmd, processing_callback=lambda: Dut.process_dut(self))
        except KeyboardInterrupt:
            raise
        except Exception as error:
            raise DutConnectionError("Couldn't start DUT target process {}".format(error))

    def prepareConnectionClose(self):  # pylint: disable=C0103
        """
        Deprecated version of prepare_connection_close. Still present for backwards compatibility.

        :return: Nothing
        """
        self.logger.warning("prepareConnectionClose deprecated, use prepare_connection_close")
        self.prepare_connection_close()

    def prepare_connection_close(self):
        """
        exit the process if it is alive.

        :return: Nothing
        """
        pass

    def close_connection(self):
        """
        Stop the process.

        :return: Nothing
        """
        self.logger.debug("Close CLI Process '%s'" % self.cmd, extra={'type': '<->'})
        self.stop_process()

    def writeline(self, data, crlf="\n"):  # pylint: disable=arguments-differ
        """
        Write data to process.

        :param data: data to write
        :param crlf: line end character
        :return: Nothing
        """
        GenericProcess.writeline(self, data, crlf=crlf)

    def readline(self, timeout=1):
        """
        Read a line from the process.

        :param timeout: Timeout
        :return: read line
        """
        return GenericProcess.readline(self, timeout=timeout)

    def reset(self, method=None):
        """
        Not implemented
        """
        self.logger.info("Reset not implemented for process DUT")

    def print_info(self):
        """
        Print information of this dut.

        :return: Nothing.
        """
        info_string = "DutProcess {}, \n".format(self.name)
        if self.comport:
            info_string = info_string + "CMD {} \n".format(self.comport)
        if self.location:
            info_string = info_string + "Location: x = {}, y = {} \n".format(self.location.x_coord,
                                                                             self.location.y_coord)
        if self.config:
            info_string = info_string + "Configuration for this DUT:\n {} \n".format(self.config)
        self.logger.info(info_string)

    def get_info(self):
        """
        Get DutInformation object of this dut.

        :return: DutInformation
        """
        return self.dutinformation

    def get_config(self):
        """
        Get configuration of this dut.

        :return: dictionary
        """
        return self.config

    def _flash_needed(self, **kwargs):
        pass
