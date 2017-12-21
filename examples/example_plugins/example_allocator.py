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

This is an example of the implementation of an allocator type global plugin for Icetea.
"""

from icetea_lib.Plugin.PluginBase import RunPluginBase
from icetea_lib.ResourceProvider.Allocators.BaseAllocator import BaseAllocator
from icetea_lib.AllocationContext import AllocationContextList


class ExampleAllocatorPlugin(RunPluginBase):
    def __init__(self):
        super(ExampleAllocatorPlugin, self).__init__()
        pass

    def get_allocators(self):
        """
        Return reference to allocator class.
        """
        return {"ExampleAllocator": ExampleAllocator}


class ExampleAllocator(BaseAllocator):
    """
    The allocator needs to be a class that implements the api from BaseAllocator.
    """
    def __init__(self, args=None, logger=None):
        super(ExampleAllocator, self).__init__()

    def can_allocate(self, dut_configuration):
        return True

    def allocate(self, dut_configuration_list, args=None):
        return AllocationContextList()

    def cleanup(self):
        pass

    def release(self, dut=None):
        pass
