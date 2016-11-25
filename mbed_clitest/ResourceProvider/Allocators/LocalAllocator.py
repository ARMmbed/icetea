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

import logging
from mbed_clitest.DeviceConnectors.DutDetection import DutDetection
from BaseAllocator import BaseAllocator
from exceptions import AllocationError

class LocalAllocator(BaseAllocator):
    def __init__(self, logger=None):
        super(BaseAllocator, self).__init__()

        if logger is None:
            logger = logging.getLogger("dummy")
            logger.addHandler(logging.NullHandler())
        self.logger = logger

        self._available_devices = DutDetection().get_available_devices()

    def can_allocate(self, dut_configuration):
        if "type" in dut_configuration and dut_configuration["type"] in ["hardware", "process"]:
            return True
        return False

    def allocate(self, dut_configuration_list, dut_factory = None):
        if not isinstance(dut_configuration_list, list):
            raise AllocationError("Invalid format for DUT configuration")

        # Enumerate all required DUT's
        try:
            for dut_configuration in dut_configuration_list:
                if not self.can_allocate(dut_configuration):
                    raise AllocationError("Allocator doesn't support allocating required resource type")
                self._allocate(dut_configuration)
        except AllocationError:
            # Locally allocated don't need to be released any way for now, so just re-raise the error
            raise

        # Create DUT using dut_factory if allocation was successful and dut_factory was given
        if dut_factory is not None:
            for dut_configuration in dut_configuration_list:
                    dut_factory(dut_configuration)

        return True

    def release(self, allocation_context):
        pass

    def _allocate(self, dut_configuration):
        if dut_configuration["type"] == "hardware":
            platforms = None if 'allowed_platforms' not in dut_configuration else dut_configuration['allowed_platforms']
            if self._available_devices is None:
                raise AllocationError("No available devices to allocate from")
            # Enumerate through all available devices
            for dev in self._available_devices:
                if platforms:
                    # Dut defines platforms that are allowed, check if device is one of them
                    if not dev['platform_name'] in platforms:
                        # Not allowed, continue to next device
                        self.logger.debug("Skipping device %s because of mismatching platform, required %s but device was %s" % (dev['target_id'], platforms, dev['platform_name']))
                        continue

                if dev['state'] == 'allocated':
                    self.logger.debug("Skipping device %s because it was already allocated" % dev['target_id'])
                    continue

                if DutDetection.is_port_usable( dev['serial_port'] ):
                    dev['state'] = "allocated"
                    dut_configuration['allocated'] = dev
                    self.logger.info("Allocated device %s" % dev['target_id'])
                    return True
                else:
                    self.logger.info("Could not open serial port (%s) of allocated device %s" % (dev['serial_port'], dev['target_id']))
            # Didn't find a matching device to allocate so allocation failed
            raise AllocationError("No matching device found to allocate for DUT")
        # Successful allocation, return True
        return True