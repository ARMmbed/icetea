# pylint: disable=no-member,too-many-instance-attributes,too-many-public-methods,protected-access
# pylint: disable=too-many-nested-blocks
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

Helpers for handling resources. Handles initialization of Duts,
releasing Duts, handling resource configuration etc.
"""

import time

from six import string_types

from icetea_lib.ResourceProvider.ResourceProvider import ResourceProvider
from icetea_lib.ResourceProvider.ResourceConfig import ResourceConfig
from icetea_lib.ResourceProvider.exceptions import ResourceInitError
from icetea_lib.DeviceConnectors.DutInformation import DutInformation
from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError
from icetea_lib.TestStepError import TestStepError
from icetea_lib.build import Build
from icetea_lib.tools.NodeEndPoint import NodeEndPoint


class ResourceFunctions(object):
    """
    ResourceFunctions manage test required resources, like DUT's.
    It provide public API's to get individual DUT's object or iterator over all DUT's.
    """
    def __init__(self, args, logger, configuration, **kwargs):
        super(ResourceFunctions, self).__init__(**kwargs)
        self._allocation_context = None
        self._resource_configuration = ResourceConfig()
        self._resource_provider = None
        self._starttime = None
        self._dutinformations = None
        self._commands = None
        self._duts = []
        self._args = args
        self._logger = logger
        self._configuration = configuration

    def init(self, commands, logger=None):
        """
        Initialize ResourceConfig and ResourceProvider

        :return: Nothing
        """
        if logger:
            self._logger = logger
        # Create ResourceProvider object and resolve the resource requirements from configuration
        self._resource_provider = ResourceProvider(self._args)
        # @todo need better way to handle forceflash_once option
        # because provider is singleton instance.
        self._resource_provider.args.forceflash = self._args.forceflash
        self._resource_configuration = ResourceConfig(logger=self._logger)
        self._resource_provider.resolve_configuration(self._configuration.config,
                                                      self._resource_configuration)
        self._commands = commands

    def init_duts(self, benchapi):
        """
        Initialize Duts, and the network sniffer.

        :return: Nothing
        """
        # Validate dut configurations
        self.validate_dut_configs(self.resource_configuration.get_dut_configuration(),
                                  self._logger)
        # Initialize duts
        if self.resource_configuration.count_duts() > 0:
            self._initialize_duts()
            benchapi._nwsniffer.init_sniffer()
        else:
            self._logger.debug("This TC doesn't use DUT's")
        self._starttime = time.time()

    def duts_release(self):
        """
        Release Duts.

        :return: Nothing
        """
        try:
            # try to close node's by nicely by `exit` command
            # if it didn't work, kill it by OS process kill command
            # also close reading threads if any
            self._logger.debug("Close dut connections")
            # pylint: disable=unused-variable
            for i, dut in self.duts_iterator():
                try:
                    dut.close_dut()
                    dut.close_connection()
                except Exception:  # pylint: disable=broad-except
                    # We want to catch all uncaught Exceptions here.
                    self._logger.error("Exception while closing dut %s!",
                                       dut.dut_name,
                                       exc_info=True if not self._args.silent else False)
                finally:
                    if hasattr(self._resource_provider.allocator, "share_allocations"):
                        if getattr(self._resource_provider.allocator, "share_allocations"):
                            pass
                        else:
                            self._logger.debug("Releasing dut {}".format(dut.index))
                            self.resource_provider.allocator.release(dut=dut)
                    else:
                        self._logger.debug("Releasing dut {}".format(dut.index))
                        self.resource_provider.allocator.release(dut=dut)

            self._logger.debug("Close dut threads")

            # finalize dut thread
            for ind, dut in self.duts_iterator():
                while not dut.finished():
                    time.sleep(0.5)
                    self._logger.debug("Dut #%i is not finished yet..", ind)
        except KeyboardInterrupt:
            self._logger.debug("key interrupt")
            for ind, dut in self.duts_iterator():
                dut.kill_received = True
            self._duts_delete()

    def get_start_time(self):
        """
        Get start time.

        :return: None if test has not started, start time stamp fetched with time.time() otherwise.
        """
        return self._starttime

    @property
    def resource_configuration(self):
        """
        Getter for __resource_configuration.

        :return: ResourceConfig
        """
        return self._resource_configuration

    @resource_configuration.setter
    def resource_configuration(self, value):
        """
        Setter for __resource_configuration.

        :param value: ResourceConfig
        :return: Nothing
        """
        self._resource_configuration = value

    def dut_count(self):
        """
        Getter for dut count from resource configuration.

        :return: int
        """
        if self.resource_configuration:
            return self.resource_configuration.count_duts()
        return 0

    def get_dut_count(self):
        """
        Get dut count.

        :return: int
        """
        return self.dut_count()

    @property
    def resource_provider(self):
        """
        Getter for __resource_provider

        :return: ResourceProvider
        """
        return self._resource_provider

    @property
    def duts(self):
        """
        Get _duts.

        :return: list
        """
        return self._duts

    @duts.setter
    def duts(self, value):
        """
        set a list as _duts.

        :param value: list
        :return: Nothing
        """
        self._duts = value

    @property
    def dut_indexes(self):
        """
        Get a list with dut indexes.

        :return: list
        """
        return range(1, self._resource_configuration.count_duts() + 1)

    def _duts_delete(self):
        """
        Reset internal __duts list to empty list.

        :return: Nothing
        """
        self._logger.debug("delete duts")
        self._duts = []

    def duts_iterator_all(self):
        """
        Yield indexes and related duts.
        """
        for ind, dut in enumerate(self.duts):
            yield ind, dut

    def duts_iterator(self):
        """
        Yield indexes and related duts that are for this test case.
        """
        for ind, dut in enumerate(self.duts):
            if self.is_my_dut_index(ind):
                yield ind, dut

    def is_allowed_dut_index(self, dut_index):
        """
        Check if dut_index is one of the duts for this test case.

        :param dut_index: int
        :return: Boolean
        """
        return dut_index in self.dut_indexes

    def get_dut(self, k):
        """
        Get dut object.

        :param k: index or nickname of dut.
        :return: Dut
        """
        dut_index = k
        if isinstance(k, str):
            dut_index = self.get_dut_index(k)

        if dut_index > len(self.duts) or dut_index < 1:
            self._logger.error("Invalid DUT number")
            raise ValueError("Invalid DUT number when calling get_dut(%i)" % dut_index)
        return self.duts[dut_index - 1]

    def get_node_endpoint(self, endpoint_id, bench):
        """
        get NodeEndPoint object for dut endpoint_id.

        :param endpoint_id: nickname of dut
        :return: NodeEndPoint
        """
        if isinstance(endpoint_id, string_types):
            endpoint_id = self.get_dut_index(endpoint_id)
        return NodeEndPoint(bench, endpoint_id)

    def is_my_dut_index(self, dut_index):
        """
        :return: Boolean
        """
        if self._args.my_duts:
            myduts = self._args.my_duts.split(',')
            if str(dut_index) in myduts:
                return True
            return False
        else:
            return True

    @property
    def dutinformations(self):
        """
        Getter for DutInformation list.

        :return: list
        """
        if self._allocation_context:
            return self._allocation_context.get_dutinformations()
        return list()

    @dutinformations.setter
    def dutinformations(self, value):
        if self._allocation_context:
            self._allocation_context.dutinformations = value

    def reset_dut(self, dut_index='*'):
        """
        Reset dut k.

        :param dut_index: index of dut to reset. Default is *, which causes all duts to be reset.
        :return: Nothing
        """
        if dut_index == '*':
            for ind in self.resource_configuration.get_dut_range():
                if self.is_my_dut_index(ind):
                    self.reset_dut(ind)
            return
        method = None
        if self._args.reset == "hard" or self._args.reset == "soft":
            self._logger.debug("Sending reset %s to dut %d", self._args.reset, dut_index - 1)
            method = self._args.reset
        self.duts[dut_index - 1].init_wait_register()
        self.duts[dut_index - 1].reset(method)
        self._logger.debug("Waiting for dut %d to initialize", dut_index)
        result = self.duts[dut_index - 1].wait_init()
        if not result:
            self._logger.warning("Cli initialization trigger not found. Maybe your application"
                                 " started before we started reading? Try adding --reset"
                                 " to your run command.")
            raise DutConnectionError("Dut cli failed to initialize within set timeout!")
        if self._args.sync_start:
            self._commands.sync_cli(dut_index)
        self._logger.debug("CLI initialized")
        self.duts[dut_index - 1].init_cli()

    def _open_dut_connections(self, allocations):
        """
        Internal helper. Registers waiting for cli initialization and handles the wait
        as well as opens connections.
        """
        for dut in self._duts:
            dut.init_wait_register()

        try:
            allocations.open_dut_connections()
        except DutConnectionError:
            self._logger.exception("Error while opening DUT connections!")
            for dut in self._duts:
                dut.close_dut()
                dut.close_connection()
            raise

        for ind, dut in self.duts_iterator():
            self._logger.info("Waiting for dut %d to initialize.", ind + 1)
            res = dut.wait_init()
            if not res:
                self._logger.warning("Cli initialization trigger not found. Maybe your application"
                                     " started before we started reading? Try adding --reset"
                                     " to your run command.")
                raise DutConnectionError("Dut cli failed to initialize within set timeout!")
            if self._args.sync_start:
                self._logger.info("Synchronizing the command line interface.")
                try:
                    self._commands.sync_cli(dut.index)
                except TestStepError:
                    raise DutConnectionError("Synchronized start for dut {} failed!".format(
                        dut.index))

    def _alloc_error_helper(self):
        """
        Helper for exception handling in the __init_duts method.
        """
        d_info_list = []
        for i, resource in enumerate(self.resource_configuration.get_dut_configuration()):
            dutinfo = DutInformation(resource.get("platform_name"), None, i)
            d_info_list.append(dutinfo)
        self._dutinformations = d_info_list

    def get_platforms(self):
        """
        Get list of dut platforms.

        :return: list
        """
        plat_list = []
        for info in self.dutinformations:
            plat_list.append(info.platform)
        return plat_list

    def get_serialnumbers(self):
        """
        Get list of dut serial numbers.

        :return: list
        """
        serial_number_list = []
        for info in self.dutinformations:
            serial_number_list.append(info.resource_id)
        return serial_number_list

    # Internal function to Initialize cli dut's
    def _initialize_duts(self):
        """
        Internal function to initialize duts

        :return: Nothing
        :raises: DutConnectionError if correct amount of duts were not initialized or if reset
        failed or if cli initialization wait loop timed out.
        """

        # Initialize command line interface
        self._logger.info("Initialize DUT's connections")

        try:
            allocations = self.resource_provider.allocate_duts(self.resource_configuration)
        except (AllocationError, ResourceInitError):
            self._alloc_error_helper()
            raise
        self._allocation_context = allocations
        allocations.set_logger(self._logger)
        allocations.set_resconf(self.resource_configuration)

        try:
            self._duts = allocations.init_duts(args=self._args)

            if len(self._duts) != self.resource_configuration.count_duts():
                raise AllocationError("Unable to initialize required amount of duts.")
        except AllocationError:
            self._alloc_error_helper()
            raise

        self._open_dut_connections(allocations)

        for ind, dut in self.duts_iterator():
            dut.Testcase = self._configuration.name
            dut.init_cli()
            self._logger.debug("DUT[%i]: Cli initialized.", ind)

        for ind, dut in self.duts_iterator():
            self._logger.debug("DUT[%i]: %s", ind, dut.comport)

        self._logger.debug("Initialized %d %s "
                           "for this testcase.", len(self._duts),
                           "dut" if len(self._duts) == 1 else "duts")

    def validate_dut_configs(self, dut_configuration_list, logger):
        """
        Validate dut configurations.

        :param dut_configuration_list: dictionary with dut configurations
        :param logger: logger to be used
        :raises EnvironmentError if something is wrong
        """
        # for now we validate only binaries - if it exists or not.
        if not self._args.skip_flash:
            for conf in dut_configuration_list:
                try:
                    binar = conf.get("application").get("bin")
                    if binar:
                        build = Build.init(binar)
                        if not build.is_exists():
                            logger.warning("Binary '{}' not found".format(binar))
                            raise EnvironmentError("Binary not found")
                except(KeyError, AttributeError):
                    pass

        if logger is not None:
            logger.debug("Configurations seems to be ok")

    def get_dut_versions(self, commands):
        """
        Get nname results and set them to duts.

        :return: Nothing
        """
        resps = commands.command('*', "nname")
        for i, resp in enumerate(resps):
            self.duts[i].version = resp.parsed

    def get_dut_nick(self, dut_index):
        """
        Get nick of dut index k.

        :param dut_index: index of dut
        :return: string
        """
        nick = str(dut_index)
        int_index_in_duts = dut_index in self._configuration.config["requirements"]["duts"]
        str_index_in_duts = False
        if not int_index_in_duts:
            str_index_in_duts = nick in self._configuration.config["requirements"]["duts"]
        if str_index_in_duts:
            nick_in_indexed_reqs = "nick" in self._configuration.config[
                "requirements"]["duts"][nick]
        elif int_index_in_duts:
            nick_in_indexed_reqs = "nick" in self._configuration.config[
                "requirements"]["duts"][dut_index]
        else:
            nick_in_indexed_reqs = False
        if int_index_in_duts and nick_in_indexed_reqs:
            return self._configuration.config["requirements"]["duts"][dut_index]['nick']
        elif str_index_in_duts and nick_in_indexed_reqs:
            return self._configuration.config["requirements"]["duts"][nick]['nick']
        return nick

    def get_dut_index(self, nick):
        """
        Get index of dut with nickname nick.

        :param nick: string
        :return: integer > 1
        """
        for dut_index, dut in enumerate(self.resource_configuration.get_dut_configuration()):
            nickname = dut.get("nick")
            if nickname and nickname == nick:
                return dut_index + 1
        raise ValueError("Cannot find DUT by nick '%s'" % nick)

    def is_my_dut(self, k):
        """
        :return: Boolean
        """
        if self._args.my_duts:
            myduts = self._args.my_duts.split(',')
            if str(k) in myduts:
                return True
            return False
        else:
            return True
