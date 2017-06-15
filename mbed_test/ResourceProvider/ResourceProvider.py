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

import os
import mbed_test.LogManager as LogManager

from mbed_test.DeviceConnectors.DutSerial import DutSerial
from mbed_test.DeviceConnectors.DutProcess import DutProcess
from mbed_test.DeviceConnectors.DutConsole import DutConsole
from ResourceConfig import ResourceConfig
from exceptions import ResourceInitError
from Allocators.exceptions import AllocationError
from Allocators.LocalAllocator import LocalAllocator

class ResourceProvider(object):

    def __init__(self, args):
        self.logger = LogManager.get_bench_logger("ResourceProvider", "RSP")
        #@TODO: Refactor args into some separate configuration class maybe?
        self.args = args
        self._resource_configuration = ResourceConfig(logger=self.logger)
        self._jsonconf = None
        self._duts = []
        self.allocator = None

    def resolve_configuration(self, conf):
        """
        Resolve the configuration from given JSON encoded configuration data.
        :param conf: JSON encoded configuration
        :return:
        """
        self.jsonconf = conf
        self._resource_configuration.resolve_configuration(conf)

    def get_resource_configuration(self):
        return self._resource_configuration

    def initialize_duts(self, DEFAULT_BIN=None):
        """
        Initialize DUT's.
        :param resource_configuration: A ResourceConfig object containing the desired configuration of DUT's
        :return: Array of DUT objects
        """
        self.DEFAULT_BIN = DEFAULT_BIN
        if not self._resource_configuration:
            raise ResourceInitError("No resource configuration defined!")

        for item in self._resource_configuration.get_dut_configuration():
            if 'application' in item:
                if 'bin' in item['application']:
                    if item['application']['bin'] != self.DEFAULT_BIN:
                        if 'type' in item:
                            self.check_flashing_need(item['type'], item['application']['bin'], self.args.forceflash)
                    else:  # DEFAULT_BIN
                        if self.args.forceflash:
                            raise ResourceInitError("Can't forceflash %s to device" % self.DEFAULT_BIN)


        self.allocator = self.__get_allocator()

        try:
            # Try to allocate resources and instantiate DUT's
            self.allocator.allocate(self._resource_configuration.get_dut_configuration(), self.__dut_factory)
        except AllocationError as e:
            # If error occurred, close already opened duts
            for d in self._duts:
                d.Close()
            raise ResourceInitError("Couldn't allocate all required devices (%s)" % e)



        self.logger.info("Required duts %d, actual duts %d" % (self.get_resource_configuration().count_duts(), len(self._duts)))
        if self.get_resource_configuration().count_duts() != len(self._duts):
            self.logger.error("Invalid dut count. Required: %i, initialized count: %i" % (self.get_resource_configuration().count_duts(), len(self._duts)))
            raise ResourceInitError("Cannot initialize required amount of Duts")

        self.logger.info("The following duts were allocated for this test case: \n")
        for d in self._duts:
            d.printInfo()

        return self._duts

    def cleanup(self):
        if self.allocator:
            self.allocator.cleanup()
            self.allocator = None
        self._duts = None

    def get_build(self, build_id):
        # initial support for id to filename mapping
        return build_id

    def check_flashing_need(self, execution_type, build_id, force):
        binary_file_name = self.get_build(build_id)
        if os.path.isfile(binary_file_name):
            if execution_type == 'hardware':
                if not force:
                    #@todo: Make a better check for binary compatibility
                    extension = os.path.splitext(binary_file_name)[-1].lower()
                    if extension != '.bin' and extension != '.hex':
                        self.logger.debug("File ('%s') is not supported to flash, skip it", binary_file_name)
                        return False
                    else:
                        return True
                else:
                    return True
        else:
            raise ResourceInitError("Given binary %s does not exist" % binary_file_name)

    def __get_allocator(self):
        return LocalAllocator(logger = self.logger)

    def __dut_factory(self, dutconf):
        if dutconf["type"] == "hardware":
            self._duts.append(self.__init_hardware_dut(dutconf, len(self._duts) + 1))
        elif dutconf["type"] == "process":
            self._duts.append(self.__init_process_dut(dutconf, len(self._duts) + 1))

    def __init_hardware_dut(self, conf, index):
        try:
            from mbed_flasher.flash import Flash
        except ImportError:
            self.logger.warning("mbed-flasher not installed. (https://github.com/ARMmbed/mbed-flasher)")
        else:
            binary = None
            try:
                binary = conf["application"]['bin']
            except KeyError:
                pass

            # If something to flash, get the allocated device and flash it
            if binary and binary != self.DEFAULT_BIN:
                if self.check_flashing_need('hardware', binary, self.args.forceflash):
                    dev = conf['allocated']
                    self.logger.info('Flashing dev: %s', dev['target_id'])
                    # Flasher imported so continue flashing
                    flasher = Flash()
                    flasher.flash(build=binary, target_id=dev['target_id'], device_mapping_table=[dev])
                    self.logger.info('flash ready')

        # Finally open serial connection and return
        return self.__open_serial_connection(conf, index)

    def __open_serial_connection(self, conf, index):
        dev = conf['allocated']
        port = dev['serial_port']
        if 'baud_rate' in dev:
            baudrate = dev['baud_rate']
        else: baudrate = 115200
        if self.args.baudrate:
            baudrate = self.args.baudrate
        dut = DutSerial( name="D%d" % index, port=port, baudrate=baudrate)

        if self.args.serial_rtscts:
          dut.serial_rtscts = self.args.serial_rtscts
        elif self.args.serial_xonxoff:
            dut.serial_xonxoff = self.args.serial_xonxoff

        if self.args.serial_ch_size > 0:
            dut.ch_mode = True
            dut.ch_mode_chunk_size = self.args.serial_ch_size
        elif self.args.serial_ch_size is 0:
            dut.ch_mode = False
        if self.args.ch_mode_ch_delay:
            dut.ch_mode_ch_delay = self.args.ch_mode_ch_delay
        if self.args.serial_timeout:
            dut.serial_timeout = self.args.serial_timeout
        init_cli_cmds = None
        if "init_cli_cmds" in conf["application"]:
            init_cli_cmds = conf["application"]["init_cli_cmds"]
        if init_cli_cmds != None:
            dut.setInitCLICmds(init_cli_cmds)
        post_cli_cmds = None
        if "post_cli_cmds" in conf["application"]:
            post_cli_cmds = conf["application"]["post_cli_cmds"]
        if post_cli_cmds != None:
            dut.setPostCLICmds(post_cli_cmds)
        dut.Open()
        self.logger.info('Use board %s as "%s" (id: %s)' % (dev['platform_name'], dut.getDutName(), dev['target_id']))
        return dut

    def __init_process_dut(self, conf, index):
        if "subtype" in conf and conf["subtype"]:
            if conf["subtype"] == "console":
                # This is a specialized 'console' process
                if "application" in conf:
                    config = conf["application"]
                else:
                    config = None
                self.logger.debug("Starting a remote console")
                dut = DutConsole(name="D%d" % index, conf=config)
            else:
                self.logger.error("Unrecognized process subtype: %s"%conf["subtype"])
                return None
            dut.Open()
        else:
            binary = conf["application"]['bin']
            self.logger.debug("Starting process '%s'" % binary)
            dut = DutProcess(name="D%d" % index)
            if self.args.valgrind:
                dut.useValgrind(self.args.valgrind_tool, not self.args.valgrind_text,
                                self.args.valgrind_console, self.args.valgrind_track_origins,
                                self.args.valgrind_extra_params)
            if self.args.gdb == index:
                dut.useGdb()
                self.logger.info("GDB is activated for node %i" % index)
            if self.args.gdbs == index:
                dut.useGdbs(True, self.args.gdbs_port)
                self.logger.info("GDBserver is activated for node %i" % index)
            if self.args.vgdb == index:
                dut.useVgdb()
                self.logger.info("VGDB is activated for node %i" % index)
            if self.args.nobuf:
                dut.noStdbuf()
            dut.Open(binary)
        return dut

    def get_my_duts(self):
        if self.args.my_duts:
            myduts = self.args.my_duts.split(',')
