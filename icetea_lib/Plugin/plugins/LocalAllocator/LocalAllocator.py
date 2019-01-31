# pylint: disable=unused-argument

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

LocalAllocator module. Implements allocating local resources using mbedls
"""

import logging

from icetea_lib.LogManager import get_resourceprovider_logger, set_level
from icetea_lib.AllocationContext import AllocationContext, AllocationContextList
from icetea_lib.ResourceProvider.Allocators.BaseAllocator import BaseAllocator
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError
from icetea_lib.ResourceProvider.exceptions import ResourceInitError

from icetea_lib.Plugin.plugins.LocalAllocator.DutDetection import DutDetection
from icetea_lib.Plugin.plugins.LocalAllocator.DutConsole import DutConsole
from icetea_lib.Plugin.plugins.LocalAllocator.DutProcess import DutProcess
from icetea_lib.Plugin.plugins.LocalAllocator.DutSerial import DutSerial
from icetea_lib.Plugin.plugins.LocalAllocator.DutMbed import DutMbed


def init_generic_serial_dut(contextlist, conf, index, args):
    """
    Initializes a local hardware dut
    """
    port = conf['serial_port']
    baudrate = (args.baudrate if args.baudrate else conf.get(
        "application", {}).get("baudrate", 115200))
    serial_config = {}
    if args.serial_rtscts:
        serial_config["serial_rtscts"] = args.serial_rtscts
    elif args.serial_xonxoff:
        serial_config["serial_xonxoff"] = args.serial_xonxoff

    if args.serial_timeout:
        serial_config["serial_timeout"] = args.serial_timeout

    ch_mode_config = {}
    if args.serial_ch_size > 0:
        ch_mode_config["ch_mode"] = True
        ch_mode_config["ch_mode_chunk_size"] = args.serial_ch_size
    elif args.serial_ch_size is 0:
        ch_mode_config["ch_mode"] = False

    if args.ch_mode_ch_delay:
        ch_mode_config["ch_mode_ch_delay"] = args.ch_mode_ch_delay
    dut = DutSerial(name="D%d" % index, port=port, baudrate=baudrate,
                    config=conf, ch_mode_config=ch_mode_config,
                    serial_config=serial_config, params=args)
    dut.index = index

    dut.platform = conf.get("platform_name", "serial")

    msg = 'Use device in serial port {} as D{}'
    contextlist.logger.info(msg.format(port,
                                       index))

    contextlist.duts.append(dut)
    contextlist.dutinformations.append(dut.get_info())


def init_mbed_dut(contextlist, conf, index, args):
    """
    Initializes a local hardware dut
    """
    binary = None
    try:
        binary = conf["application"]['bin']
    except KeyError:
        pass

    dev = conf.get('allocated', None)
    if not dev:
        raise ResourceInitError("Allocated device not found.")

    port = dev['serial_port']
    baudrate = (args.baudrate if args.baudrate else
                conf.get("application", {}).get("baudrate", 115200))
    serial_config = {}
    if args.serial_rtscts:
        serial_config["serial_rtscts"] = args.serial_rtscts
    elif args.serial_xonxoff:
        serial_config["serial_xonxoff"] = args.serial_xonxoff

    if args.serial_timeout:
        serial_config["serial_timeout"] = args.serial_timeout

    ch_mode_config = {}
    if args.serial_ch_size > 0:
        ch_mode_config["ch_mode"] = True
        ch_mode_config["ch_mode_chunk_size"] = args.serial_ch_size
    elif args.serial_ch_size is 0:
        ch_mode_config["ch_mode"] = False

    if args.ch_mode_ch_delay:
        ch_mode_config["ch_mode_ch_delay"] = args.ch_mode_ch_delay

    dut = DutMbed(name="D%d" % index, port=port, baudrate=baudrate,
                  config=conf, ch_mode_config=ch_mode_config,
                  serial_config=serial_config, params=args)
    dut.index = index

    # If something to flash, get the allocated device and flash it
    if binary and not args.skip_flash:
        if contextlist.check_flashing_need('hardware',
                                           binary,
                                           args.forceflash):
            if dut.flash(binary_location=binary, forceflash=args.forceflash):
                contextlist.logger.info('flash ready')
            else:
                dut.close_dut(False)
                dut.close_connection()
                dut = None
                raise ResourceInitError("Dut flashing failed!")

    dut.platform = dev["platform_name"]

    msg = 'Use board {} as "{}" (id: {})'
    contextlist.logger.info(msg.format(dev['platform_name'],
                                       dut.get_dut_name(),
                                       dev['target_id']))

    contextlist.duts.append(dut)
    contextlist.dutinformations.append(dut.get_info())


def init_process_dut(contextlist, conf, index, args):
    """
    Initialize process type Dut as DutProcess or DutConsole.
    """
    if "subtype" in conf and conf["subtype"]:
        if conf["subtype"] != "console":
            msg = "Unrecognized process subtype: {}"
            contextlist.logger.error(msg.format(conf["subtype"]))
            raise ResourceInitError("Unrecognized process subtype: {}")
        # This is a specialized 'console' process
        config = None
        if "application" in conf:
            config = conf["application"]
        contextlist.logger.debug("Starting a remote console")
        dut = DutConsole(name="D%d" % index, conf=config, params=args)
        dut.index = index
    else:
        binary = conf["application"]['bin']
        app_config = conf["application"]
        init_cli_cmds = app_config.get("init_cli_cmds", None)
        post_cli_cmds = app_config.get("post_cli_cmds", None)
        contextlist.logger.debug("Starting process '%s'" % binary)
        dut = DutProcess(name="D%d" % index, config=conf, params=args)
        dut.index = index
        dut.command = binary
        if args.valgrind:
            dut.use_valgrind(args.valgrind_tool,
                             not args.valgrind_text,
                             args.valgrind_console,
                             args.valgrind_track_origins,
                             args.valgrind_extra_params)
        if args.gdb == index:
            dut.use_gdb()
            contextlist.logger.info("GDB is activated for node %i" % index)
        if args.gdbs == index:
            dut.use_gdbs(True, args.gdbs_port)
            contextlist.logger.info("GDBserver is activated for node %i" % index)
        if args.vgdb == index:
            dut.use_vgdb()
            contextlist.logger.info("VGDB is activated for node %i" % index)
        if args.nobuf:
            dut.no_std_buf()

        if init_cli_cmds is not None:
            dut.set_init_cli_cmds(init_cli_cmds)
        if post_cli_cmds is not None:
            dut.set_post_cli_cmds(post_cli_cmds)

    contextlist.duts.append(dut)
    contextlist.dutinformations.append(dut.get_info())


class LocalAllocator(BaseAllocator):
    """
    LocalAllocator class, subclasses BaseAllocator. Implements allocation of local resources for
    use in test cases. Uses mbedls to detect mbed devices.
    """
    def __init__(self, args=None, logger=None, allocator_cfg=None):
        super(LocalAllocator, self).__init__()
        self.logger = logger
        if self.logger is None:
            self.logger = get_resourceprovider_logger("LocalAllocator", "LAL")
            set_level("LAL", logging.DEBUG)
        self._available_devices = []

    @property
    def share_allocations(self):
        """
        Just return False, allocation sharing not implemented for this allocator.

        :return: False
        """
        return False

    def can_allocate(self, dut_configuration):
        """
        Checks if resource type is supported.
        :param dut_configuration: ResourceRequirements object
        :return: True if type is supported, False otherwise
        """
        try:
            return dut_configuration["type"] in ["hardware", "process", "serial", "mbed"]
        except KeyError:
            return False

    def allocate(self, dut_configuration_list, args=None):
        """
        Allocates resources from available local devices.

        :param dut_configuration_list: List of ResourceRequirements objects
        :param args: Not used
        :return: AllocationContextList with allocated resources
        """
        dut_config_list = dut_configuration_list.get_dut_configuration()
        # if we need one or more local hardware duts let's search attached
        # devices using DutDetection
        if not isinstance(dut_config_list, list):
            raise AllocationError("Invalid dut configuration format!")

        if next((item for item in dut_config_list if item.get("type") == "hardware"), False):
            self._available_devices = DutDetection().get_available_devices()
            if len(self._available_devices) < len(dut_config_list):
                raise AllocationError("Required amount of devices not available.")

        # Enumerate all required DUT's
        try:
            for dut_config in dut_config_list:
                if not self.can_allocate(dut_config.get_requirements()):
                    raise AllocationError("Resource type is not supported")
                self._allocate(dut_config)
        except AllocationError:
            # Locally allocated don't need to be released any way for
            # now, so just re-raise the error
            raise
        alloc_list = AllocationContextList()
        res_id = None
        for conf in dut_config_list:
            if conf.get("type") == "mbed":
                res_id = conf.get("allocated").get("target_id")
            context = AllocationContext(resource_id=res_id, alloc_data=conf)
            alloc_list.append(context)

        alloc_list.set_dut_init_function("serial", init_generic_serial_dut)
        alloc_list.set_dut_init_function("process", init_process_dut)
        alloc_list.set_dut_init_function("mbed", init_mbed_dut)

        return alloc_list

    def release(self, dut=None):
        """
        Resource releasing is not necessary. Not implemented.

        :param dut: Not used
        :return: Nothing
        """
        pass

    def _allocate(self, dut_configuration):  # pylint: disable=too-many-branches
        """
        Internal allocation function. Allocates a single resource based on dut_configuration.

        :param dut_configuration: ResourceRequirements object which describes a required resource
        :return: True
        :raises: AllocationError if suitable resource was not found or if the platform was not
        allowed to be used.
        """
        if dut_configuration["type"] == "hardware":
            dut_configuration.set("type", "mbed")
        if dut_configuration["type"] == "mbed":
            if not self._available_devices:
                raise AllocationError("No available devices to allocate from")
            dut_reqs = dut_configuration.get_requirements()
            platforms = None if 'allowed_platforms' not in dut_reqs else dut_reqs[
                'allowed_platforms']
            platform_name = None if 'platform_name' not in dut_reqs else dut_reqs[
                "platform_name"]
            if platform_name is None and platforms:
                platform_name = platforms[0]
            if platform_name and platforms:
                if platform_name not in platforms:
                    raise AllocationError("Platform name not in allowed platforms.")
            # Enumerate through all available devices
            for dev in self._available_devices:
                if platform_name and dev["platform_name"] != platform_name:
                    self.logger.debug("Skipping device %s because of mismatching platform. "
                                      "Required %s but device was %s", dev['target_id'],
                                      platform_name, dev['platform_name'])
                    continue
                if dev['state'] == 'allocated':
                    self.logger.debug("Skipping device %s because it was "
                                      "already allocated", dev['target_id'])
                    continue

                if DutDetection.is_port_usable(dev['serial_port']):
                    dev['state'] = "allocated"
                    dut_reqs['allocated'] = dev
                    self.logger.info("Allocated device %s", dev['target_id'])
                    return True
                else:
                    self.logger.info("Could not open serial port (%s) of "
                                     "allocated device %s", dev['serial_port'], dev['target_id'])
            # Didn't find a matching device to allocate so allocation failed
            raise AllocationError("No suitable local device available")
        elif dut_configuration["type"] == "serial":
            dut_reqs = dut_configuration.get_requirements()
            if not dut_reqs.get("serial_port"):
                raise AllocationError("Serial port not defined for requirement {}".format(dut_reqs))
            if not DutDetection.is_port_usable(dut_reqs['serial_port']):
                raise AllocationError("Serial port {} not usable".format(dut_reqs['serial_port']))
        # Successful allocation, return True

        return True
