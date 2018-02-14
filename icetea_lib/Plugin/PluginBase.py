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
"""

import re

"""
PluginBase implementations.
"""


# pylint: disable=too-few-public-methods,no-self-use,unused-argument
class PluginTypes(object):
    """
    Just a small enum for types.
    """
    BENCH = 0
    PARSER = 1
    EXTSERVICE = 2
    ALLOCATOR = 3


class RunPluginBase(object):
    """
    Base class for run-level plugins.
    """
    def __init__(self):
        pass

    def get_allocators(self):
        """
        Get a dictionary with names and class references to BaseAllocator objects.

        :return: Dictionary
        """
        return None


class PluginBase(object):
    """
    Base class for test case level plugins. A plugin should implement at least one of the getters
    in this class.
    """
    def __init__(self):
        pass

    def get_bench_api(self):
        """
        Return dictionary with attribute names as strings as keys and attribute values (classes,
        functions, values) as values.

        :return: Dictionary
        """
        return None

    def get_parsers(self):
        """
        Return dictionary with parser names as keys and parser functions as values.

        :return: Dictonary
        """
        return None

    def get_external_services(self):
        """
        Get dictionary with external service names as keys and classes as values.

        :return: Dictionary
        """
        return None

    def init(self, bench=None):
        """
        Initialization function that test case plugins can implement.

        :param bench: test bench object (Bench).
        :return: Nothing
        """
        return None


    @staticmethod
    def find_one(line, lookup):
        """
        regexp search with one value to return.

        :param line: Line
        :param lookup: regexp
        :return: Match group or False
        """
        match = re.search(lookup, line)
        if match:
            if match.group(1):
                return match.group(1)
        return False

    # regex search with multiple values to return
    @staticmethod
    def find_multiple(line, lookup):
        """
        regexp search with one value to return.

        :param line: Line
        :param lookup: regexp
        :return: List of match groups or False
        """
        match = re.search(lookup, line)
        if match:
            ret = []
            for i in range(1, len(match.groups()) + 1):
                ret.append(match.group(i))
            if ret:
                return ret
        return False
