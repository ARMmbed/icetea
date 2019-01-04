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

AllocationContext module, contains two classes that represent
allocation information of resources allocated for a test case.

These classes implement storing of Allocated resources as well as conversion of allocated
resources into Dut objects usable by test cases.
"""

import os

try:
    # Python 2.7 compatible import.
    from Queue import Queue
except ImportError:
    # Python 3 has renamed Queue to queue.
    from queue import Queue
from multiprocessing.pool import ThreadPool

from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.ResourceProvider.exceptions import ResourceInitError
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError
from icetea_lib.build.build import Build


class AllocationContext(object):
    """
    Class AllocationContext

    Contains allocation and resource_id:s used to define an allocated resource.
    Also contains supplementary data in _alloc_data dictionary.
    """

    def __init__(self, resource_id=None, alloc_id=None, alloc_data=None):
        self._resource_id = resource_id
        self._alloc_id = alloc_id
        self._alloc_data = alloc_data if alloc_data else {}

    def get(self, key):
        """
        Getter for configuration dictionary items

        :param key: Key to look for in configuration.
        :param default: Default value to be returned if key is not found in configuration.
                Default is None
        :return: value of configuration[key] if key exists in configuration, else value of default.
        """
        return self._alloc_data.get(key)

    def set(self, key, value):
        """
        Setter for configuration values

        :param key:
        :param value:
        :return: Nothing
        """
        self._alloc_data[key] = value

    def get_alloc_data(self):
        """
        Get allocation data dictionary

        :return: Allocation data (dictionary)
        """
        return self._alloc_data

    @property
    def alloc_id(self):
        """
        Getter for alloc_id

        :return: alloc_id
        """
        return self._alloc_id

    @property
    def resource_id(self):
        """
        Getter for resource_id

        :return: resource_id
        """
        return self._resource_id

    def __getitem__(self, item):
        """
        __getitem__ implementation for AllocationContext
        enables context[item]

        :param item: item to return
        :return: self._alloc_data[item] or None if item does not exist in self._alloc_data
        """
        return self._alloc_data.get(item, None)

    def __setitem__(self, key, value):
        """
        __setitem__ implementation for AllocationContext.
        Replaces item in list space key with value.

        :param key: Name of context data item to replace/add
        :param value: Value to replace context data item with
        :return: Nothing
        """
        self._alloc_data[key] = value


class AllocationContextList(object):
    """
    Class AllocationContextList

    Is used for storing and handling Duts after they have been allocated.
    Contains methods to iterate over AllocationContext objects and initialize duts from
    AllocationContext objects.
    """

    def __init__(self, logger=None):
        self._allocation_contexts = []
        self.logger = logger
        self.duts = []
        self.dutinformations = []
        self._resource_configuration = None
        self._dut_initialization_functions = {}

    def __len__(self):
        """
        len implementation for AllocationContextList

        :return: len(self._allocation_contexts)
        """
        return len(self._allocation_contexts)

    def __iter__(self):
        """
        Implementation of __iter__ to allow for item in list loops

        :return: iterator to self._allocation_contexts
        """
        return iter(self._allocation_contexts)

    def __getitem__(self, item):
        """
        __getitem__ implementation for AllocationContextList
        enables list[index]

        :param item: index to return
        :return: self._allocation_contexts[item]
        :raises: TypeError if item is not integer.
        :raises: IndexError if item < 0 or item > len(self._allocation_contexts)
        """
        if not isinstance(item, int):
            raise TypeError("AllocationContextList get expects an integer index")
        if len(self._allocation_contexts) <= item:
            raise IndexError("list getitem out of bounds")
        elif item < 0:
            raise IndexError("AllocationContextList get not implemented for negative values.")
        return self._allocation_contexts[item]

    def __setitem__(self, key, value):
        """
        __setitem__ implementation for AllocationContextList.
        Replaces item in list space key with value.

        :param key: Index of list item to replace
        :param value: Value to replace list item with
        :return: Nothing
        :raises: TypeError if key is not an integer.
        :raises: IndexError if key < 0 or key > len(self._allocation_contexts)
        """
        if not isinstance(key, int):
            raise TypeError("AllocationContextList set expects an integer index")
        if len(self._allocation_contexts) <= key:
            raise IndexError("list setitem out of bounds")
        elif key < 0:
            raise IndexError("AllocationContextList set not implemented for negative indexes.")
        self._allocation_contexts[key] = value

    def set_dut_init_function(self, dut_type, fnctn):
        """
        Setter for dut initialization function

        :param dut_type: Dut type
        :param fnctn: callable
        :return: Nothing
        """
        self._dut_initialization_functions[dut_type] = fnctn

    def get_dut_init_function(self, dut_type):
        """
        Get dut initialization function

        :param dut_type: Dut type.
        :return: callable
        """
        return self._dut_initialization_functions.get(dut_type)

    def set_resconf(self, resconf):
        """
        Set resource configuration.

        :param resconf: ResourceConfig object
        :return: Nothing
        """
        self._resource_configuration = resconf

    def get_resconf(self):
        """
        Get resource configuration for this AllocationContextList.

        :return: ResourceConfig
        """
        return self._resource_configuration

    def set_logger(self, logger):
        """
        Set logger.

        :param logger: logging.logger
        :return: Nothing
        """
        self.logger = logger

    def get_duts(self):
        """
        Get list of duts.

        :return: list of Dut objects
        """
        return self.duts

    def get_dutinformations(self):
        """
        Get DutInformation objects of current duts.

        :return: list of DutInformation objects
        """
        return self.dutinformations

    def append(self, alloc_context):
        """
        Appends alloc_context to self._allocation_contexts. No type-checking done here.

        :param alloc_context: AllocationContext object.
        :return: Nothing
        """
        self._allocation_contexts.append(alloc_context)

    # pylint: disable=too-many-statements
    def init_duts(self, args):  # pylint: disable=too-many-locals,too-many-branches
        """
        Initializes duts of different types based on configuration provided by AllocationContext.
        Able to do the initialization of duts in parallel, if --parallel_flash was provided.

        :param args: Argument Namespace object
        :return: list of initialized duts.
        """
        # TODO: Split into smaller chunks to reduce complexity.
        threads = []
        abort_queue = Queue()

        def thread_wrapper(*thread_args, **thread_kwargs):
            """
            Run initialization function for dut

            :param thread_args: arguments to pass to the function
            :param thread_kwargs: keyword arguments, (func: callable, abort_queue: Queue)
            :return: Result of func(*thread_args)
            """
            # pylint: disable=broad-except
            try:
                return thread_kwargs["func"](*thread_args)
            except Exception as error:
                thread_kwargs["abort_queue"].put((thread_args[2], error))

        for index, dut_conf in enumerate(self._allocation_contexts):
            dut_type = dut_conf.get("type")
            func = self.get_dut_init_function(dut_type)
            if func is None:
                continue

            threads.append(((self, dut_conf.get_alloc_data().get_requirements(), index + 1, args),
                            {"func": func, "abort_queue": abort_queue}))

        try:
            thread_limit = len(threads) if args.parallel_flash else 1
            pool = ThreadPool(thread_limit)
            async_results = [pool.apply_async(func=thread_wrapper,
                                              args=t[0], kwds=t[1])
                             for t in threads]
            # Wait for resources to be ready.
            [res.get() for res in async_results]  # pylint: disable=expression-not-assigned

            pool.close()
            pool.join()

            if not abort_queue.empty():
                msg = "Dut Initialization failed, reason(s):"
                while not abort_queue.empty():
                    dut_index, error = abort_queue.get()
                    msg = "{}\nDUT index {} - {}".format(msg, dut_index, error)

                raise AllocationError(msg)

            # Sort duts to same order as in dut_conf_list
            self.duts.sort(key=lambda d: d.index)
            self.dutinformations.sort(key=lambda d: d.index)

        except KeyboardInterrupt:
            msg = "Received keyboard interrupt, waiting for flashing to finish"
            self.logger.info(msg)
            for dut in self.duts:
                dut.close_dut(False)
                dut.close_connection()
                if hasattr(dut, "release"):
                    dut.release()
                dut = None
            raise
        except RuntimeError:
            self.logger.exception("RuntimeError during flashing")
        # ValueError is raised if ThreadPool is tried to initiate with
        # zero threads.
        except ValueError:
            self.logger.exception("No devices allocated")
            raise AllocationError("Dut Initialization failed!")
        except (DutConnectionError, TypeError):
            for dut in self.duts:
                if hasattr(dut, "release"):
                    dut.release()
            raise AllocationError("Dut Initialization failed!")
        finally:
            if pool:
                pool.close()
                pool.join()
        self.logger.debug("Allocated following duts:")
        for dut in self.duts:
            dut.print_info()

        return self.duts

    def open_dut_connections(self):
        """
        Opens connections to Duts. Starts Dut read threads.

        :return: Nothing
        :raises DutConnectionError: if problems were encountered while opening dut connection.
        """
        for dut in self.duts:
            try:
                dut.start_dut_thread()
                if hasattr(dut, "command"):
                    dut.open_dut(dut.command)
                else:
                    dut.open_dut()
            except DutConnectionError:
                self.logger.exception("Failed when opening dut connection")
                dut.close_dut(False)
                dut.close_connection()
                dut = None
                raise

    def check_flashing_need(self, execution_type, build_id, force):
        """
        Check if flashing of local device is required.

        :param execution_type: Should be 'hardware'
        :param build_id: Build id, usually file name
        :param force: Forceflash flag
        :return: Boolean
        """
        binary_file_name = AllocationContextList.get_build(build_id)
        if binary_file_name:
            if execution_type == 'hardware' and os.path.isfile(binary_file_name):
                if not force:
                    #@todo: Make a better check for binary compatibility
                    extension_split = os.path.splitext(binary_file_name)
                    extension = extension_split[-1].lower()
                    if extension != '.bin' and extension != '.hex':
                        self.logger.debug("File ('%s') is not supported to flash, skip it" %(
                            build_id))
                        return False
                    return True
                return True
            else:
                raise ResourceInitError("Given binary %s does not exist" % build_id)
        else:
            raise ResourceInitError("Given binary %s does not exist" % build_id)

    @staticmethod
    def get_build(build_id):
        """
        Gets a file related to build_id.
        """
        try:
            build = Build.init(build_id)
        except NotImplementedError:
            return None
        return build.get_file()
