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

BaseAllocator module, contains the base implementation for an allocator.
"""


class BaseAllocator(object):
    """
    Abstract base class for describing a resource allocator class.
    """
    def can_allocate(self, dut_configuration):
        """
        Returns True if this allocator supports allocating a resource
        matching the given dut_configuration. Returns False if allocating such resource is not
        supported.

        This method has to be implemented by the subclass.

        :param dut_configuration:
        :return: True if this allocator supports allocating
        resources as described in dut_configuration, otherwise False.
        """
        raise NotImplementedError("allocate has to be implemented by subclassing BaseAllocator")

    def allocate(self, dut_configuration_list, args=None):
        """
        Enumerates the dut_configuration_list to evaluate requirements
        for each DUT it contains and attempts to allocate a resource matching the requirements.
        Once all DUT's have a successfully allocated resource, they are
        instantiated by calling dut_factory callable for each dut_configuration contained in
        dut_configuration_list.

        This method has to be implemented by the subclass.

        :param dut_configuration_list: List of dut configuration dictionaries each
        containing a DUT configuration, which has the following generic form:
        {"type": "process", "nick": None }
        :param args: Extra arguments that can be passed to allocate to further
        configure the allocation.
        :raises AllocationError: If not all dut's we're allocated, raises AllocationError
        """
        raise NotImplementedError("allocate has to be implemented by subclassing BaseAllocator")

    def release(self, dut=None):
        """
        Release the allocated resource with the given context.
        This method has to be implemented by the subclass.

        :param allocation_context: The context of the allocated resource.
        :return:
        """
        raise NotImplementedError("release has to be implemented by subclassing BaseAllocator")

    def cleanup(self):
        """
        Cleanup will be called when testcase has been run and allocator should do any necessary
        cleanup operations
        :return:
        """
        pass

    @property
    def share_allocations(self):
        """
        Return boolean, which is True if allocations are shared between test cases in the run.

        :return: Boolean
        """
        raise NotImplementedError("share_allocations has to be implemented by subclassing "
                                  "BaseAllocator")
