# pylint: disable=no-member,too-many-instance-attributes,too-many-arguments
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

Helpers for network sniffer.
"""

from pkg_resources import parse_version
from pydash import get

import icetea_lib.LogManager as LogManager
from icetea_lib.TestStepError import TestStepError


class NetworkSniffer(object):
    """
    This Mixer provide public wshark related API's for Bench.
    """
    def __init__(self, resources, configurations, args, logger=None, **kwargs):
        super(NetworkSniffer, self).__init__(**kwargs)
        self.__sniffing = False
        self.__wshark = None
        self.__capture_file = None
        self.__tshark_arguments = {}
        self._logger = logger if logger else LogManager.get_dummy_logger()
        self._resources = resources
        self._configurations = configurations
        self._args = args

    def init(self, logger=None):
        """
        Set logger.
        """
        self._logger = logger if logger else self._logger

    @property
    def wshark(self):
        """
        Return wireshark object.

        :return: Wireshark
        """
        return self.__wshark

    @property
    def tshark_arguments(self):
        """
        Get tshark arguments.

        :return: dict
        """
        return self.__tshark_arguments

    @property
    def sniffer_required(self):
        """
        Check if sniffer was requested for this run.

        :return: Boolean
        """
        return self._args.use_sniffer

    def init_sniffer(self):
        """
        Initialize and start sniffer if it is required.

        :return: Nothing
        """
        if self.sniffer_required:
            self.__start_sniffer()

    def clear_sniffer(self):
        """
        Clear sniffer

        :return: Nothing
        """
        if self.__sniffing:
            import psutil
            self._logger.debug("Close wshark pipes")

            # Note: the psutil has changed the API at around version 3.0 but user likely has
            # the older version installed unless it has specifically installed via pip.
            if parse_version(psutil.__version__) < parse_version('3.0.0'):
                self._logger.warning("NOTE: your psutil version %s is likely too old,"
                                     " please update!", psutil.__version__)

            dumpcaps = []
            for process in self.wshark.liveLoggingCapture.running_processes:
                children = psutil.Process(process.pid).children(recursive=True)
                for child in children:
                    if child.name() in ('dumpcap', 'tshark-bin', 'dumpcap-bin'):
                        dumpcaps.append(child)
            self.__stop_sniffer()
            for child in dumpcaps:
                try:
                    child.kill()
                    child.wait(timeout=2)
                except (OSError, psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass

    def __create_wshark_object(self):
        """
        Internal creator for Wireshark object.

        :return: Nothing
        """
        from icetea_lib.wireshark import Wireshark
        if not self.wshark:
            self.__wshark = Wireshark()

    def __start_sniffer(self):
        """
        Start network sniffer capturing pcap to a file.

        :return: Nothing
        """

        iface = self.__get_nw_interface()
        if not iface:
            raise TestStepError("Cannot capture wireshark log")

        self.__create_wshark_object()
        self.__capture_file = LogManager.get_testcase_logfilename("network.nw.pcap")
        self._logger.debug('Start wireshark capture: %s', self.capture_file)
        # Add self.tshark_preferences to parameters
        # when pyshark starts supporting the -o tshark argument
        self.wshark.startCapture(iface,
                                 self.__capture_file,
                                 self.__tshark_arguments)
        self.__sniffing = True

    @property
    def capture_file(self):
        """
        Return capture file path.

        :return: file path of capture file.
        """
        return self.__capture_file

    def __stop_sniffer(self):
        """
        Stop the network sniffer.
        :return: Nothing
        """
        if self.__sniffing:
            self._logger.debug('Stop wireshark capture: %s', self.capture_file)
            packet_count = self.__wshark.stopCapture()
            self._logger.debug("Got total %i NW packets", packet_count)

    def __get_nw_interface(self):
        """
        Get the capture pipe or sniffer interface.
        :return:
        """
        return get(self._configurations.env, 'sniffer.iface')

    def get_nw_log_filename(self):  # pylint: disable=no-self-use
        """
        Get nw data log file name.

        :return: string
        """
        return LogManager.get_testcase_logfilename("network.nw.pcap")
