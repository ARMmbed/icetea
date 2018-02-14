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

ResourceRequirements module. Deals with requirements for resources that are to be allocated for
test cases. Handles storage of requirements and processing requirements to formats required by
allocators.
"""

from jsonmerge import merge
from icetea_lib.tools.tools import recursive_dictionary_get as recursive_search
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError


class ResourceRequirements(object):
    """
    ResourceRequirements class. Contains methods for getting and setting requirement values as
    well as processing requirements into formats supported by allocators.
    """
    def __init__(self, requirement_dict=None):
        self._requirements = requirement_dict if requirement_dict else {}

    def set(self, key, value):
        """
        Sets the value for a specific requirement.

        :param key: Name of requirement to be set
        :param value: Value to set for requirement key
        :return: Nothing, modifies requirement
        """
        if isinstance(value, dict) and key in self._requirements and isinstance(
                self._requirements[key], dict):
            self._requirements[key] = merge(self._requirements[key], value)
        else:
            self._requirements[key] = value

    def get(self, key):
        """
        Gets contents of requirement key.
        Switches to recursive search if dots ('.') are found in the key.

        :param key: key or dot separated string of keys to look for.
        :return: contents of requirement key/results of search or None.
        """
        # Catch the case where the key is "."
        if "." in key and len(key) > 1:
            return self._recursive_get(key)
        return self._requirements.get(key, None)

    def __getitem__(self, item):
        return self._requirements[item]

    def _recursive_get(self, key, dic=None):
        """
        Gets contents of requirement key recursively so users can search for
        specific keys inside nested requirement dicts.

        :param key: key or dot separated string of keys to look for.
        :param dic: Optional dictionary to use in the search.
        If not provided, self._requirements is used.
        :return: results of search or None
        """
        return recursive_search(key, dic) if dic else recursive_search(key, self._requirements)

    def get_requirements(self):
        """
        Return requirements as dict.

        :return: Dictionary
        """
        return self._requirements