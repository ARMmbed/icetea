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
        if key == "tags":
            self._set_tag(tags=value)
        else:
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

    def _set_tag(self, tag=None, tags=None, value=True):
        """
        Sets the value of a specific tag or merges existing tags with a dict of new tags.
        Either tag or tags must be None.

        :param tag: Tag which needs to be set.
        :param tags: Set of tags which needs to be merged with existing tags.
        :param value: Value to set for net tag named by :param tag.
        :return: Nothing
        """
        existing_tags = self._requirements.get("tags")
        if tags and not tag:
            existing_tags = merge(existing_tags, tags)
            self._requirements["tags"] = existing_tags
        elif tag and not tags:
            existing_tags[tag] = value
            self._requirements["tags"] = existing_tags

    def remove_empty_tags(self, tags=None):
        """
        Tags whose value is set to None shall be removed from tags.
        :param tags: Tags which are to be processed.
        If None, tags found in self._requirements are used.
        :return: If tags is not None, returns dict with processed tags. Else returns None.
        """
        new_tags = {}
        old_tags = tags if tags else self.get("tags")
        for tag in old_tags.keys():
            if old_tags[tag] is not None:
                new_tags[tag] = old_tags[tag]
        if not tags:
            self._requirements["tags"] = new_tags
            return None
        return new_tags
