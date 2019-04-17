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

import os
from ast import literal_eval as le

from icetea_lib.tools.tools import create_match_bool
# pylint: disable=too-many-locals,unsupported-membership-test


class FilterException(Exception):
    """
    Exception the filter can throw when something really goes wrong.
    """
    pass


class TestcaseFilter(object):
    """
    TestcaseFilter class. Provides the handling for different filtering arguments.
    Provides a match function to match testcases with filter.
    """
    def __init__(self):
        self._filter = {'list': False, 'name': False, 'status': False,
                        'group': False, 'type': False, 'subtype': False,
                        'comp': False, 'feature': False, 'platform': False}

    def tc(self, value):  # pylint: disable=invalid-name,too-many-branches
        """
        Tc filter.

        :param value: test case.
        :return: TestcaseFilter (self)
        """
        # tc can be:
        # int, tuple, list or str(any of the above)
        if isinstance(value, str):
            # Wildcard check
            if value == 'all':
                self._filter['name'] = 'all'
                return self

            pfilter = []
            try:
                pfilter = le(value)
            except (ValueError, SyntaxError):
                # tc wasn't immediately parseable.
                # This can mean that it was a list/tuple with a string, which gets
                # interpreted as a variable, which causes a malformed string exception.
                # Therefore, need to split and evaluate each part of the list separately
                pass

            if pfilter == []:
                # we get bad names/indexes if we leave parentheses.
                # A dictionary will not add anything to pfilter.
                value = value.strip('([])')
                for item in value.split(','):
                    try:
                        # Transforms string into other python type
                        # Troublesome if someone names a testcase as a valid python type...
                        le_item = le(item)
                        pfilter.append(le_item)
                    except (ValueError, SyntaxError):
                        # It's just a string, but it's also a name(maybe).
                        # Hopefully we're on a filesystem that allows files with identical paths
                        pfilter.append(item)
                if len(pfilter) == 1:
                    # It was a single string.
                    self._filter['name'] = pfilter[0]
                    return self
                elif not pfilter:  # pylint: disable=len-as-condition
                    pass

            value = pfilter

        if isinstance(value, int) and (value is not False and value is not True):
            if value < 1:
                raise TypeError("Error, createFilter: non-positive integer " + str(value))
            else:
                self._filter['list'] = [value - 1]
        elif isinstance(value, (list, tuple)):
            if len(value) < 1:
                raise IndexError("Error, createFilter: Index list empty.")
            for i in value:
                if not isinstance(i, int) and not isinstance(i, str):
                    raise TypeError("Error, createFilter: "
                                    "Index list has invalid member: {}".format(str(value)))
            self._filter['list'] = [x - 1 for x in value if isinstance(x, int)]
            # pylint: disable=no-member
            self._filter['list'].extend([x for x in value if isinstance(x, str)])
        elif value is None:
            raise TypeError("tc filter cannot be None")
        else:
            # In case someone calls with NoneType or anything else
            raise TypeError("Unrecognised type for tc filter. tc must be int, str, list or tuple")
        return self

    def status(self, status):
        """
        Add status filter.

        :param status: filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("status", status)

    def group(self, group):
        """
        Add group filter.

        :param group: Filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("group", group)

    def testtype(self, testtype):
        """
        Add type filter.

        :param testtype: Filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("type", testtype)

    def subtype(self, subtype):
        """
        Add subtype filter.

        :param subtype: Filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("subtype", subtype)

    def component(self, component):
        """
        Add component filter.

        :param component: Filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("comp", component)

    def feature(self, feature):
        """
        Add feature filter.

        :param feature: Filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("feature", feature)

    def platform(self, platform):
        """
        Add platform filter.

        :param platform: Filter value
        :return: TestcaseFilter
        """
        return self._add_filter_key("platform", platform)

    def get_filter(self):
        """
        Get the filter dictionary.

        :return: dict.
        """
        return self._filter

    @staticmethod
    def _match_group(string_to_match, args):
        """
        Matcher for group-filter.

        :param string_to_match: Filter string.
        :param args: tuple or list of arguments, args[0] must be the test case metadata.
        args[1] must be the filter dictionary.
        :return: Boolean
        """
        testcase = args[0]
        filters = args[1]
        group_ok = True
        if 'group' in filters and string_to_match:
            group = string_to_match.split(os.sep)  # pylint: disable=no-member
            group = [x for x in group if len(x)]  # Remove empty members
            if len(group) == 1:
                group = string_to_match.split(',')  # pylint: disable=no-member
            tcgroup = testcase['group'].split(os.sep)

            for member in group:
                if member not in tcgroup:
                    group_ok = False
                    break
        return group_ok

    def _match_list(self, testcase, tc_index):
        """
        Matcher for test case list.

        :param testcase: Testcase metadata
        :param tc_index: index
        :return: Boolean
        """
        list_ok = False
        if 'list' in self._filter.keys() and self._filter['list']:
            for index in self._filter['list']:  # pylint: disable=not-an-iterable
                if isinstance(index, int):
                    if index < 0:
                        raise TypeError(
                            "Error, filterTestcases: "
                            "index list contained non-positive integer: %s" % self._filter['list'])
                    if index == tc_index:
                        list_ok = True
                        break
                elif isinstance(index, str):
                    if testcase['name'] == index:
                        list_ok = True
                        break
                else:
                    raise TypeError("Error, filterTestcases: "
                                    "index list contained non-integer: '%s'" % self._filter['list'])
            if not list_ok:
                return False
        else:
            list_ok = True
        return list_ok

    @staticmethod
    def _match_platform(string_to_match, args):
        """
        Matcher for allowed platforms

        :param string_to_match: Filter string
        :param args: Tuple or list of arguments, args[0] must be test case metadata dictionary,
        args[1] must be filter dictionary.

        :return: Boolean
        """
        testcase = args[0]
        filters = args[1]
        platform_ok = True
        if 'platform' in filters and string_to_match:
            platforms = string_to_match
            platforms = platforms if isinstance(platforms, list) else [platforms]
            tcplatforms = testcase['allowed_platforms']
            if tcplatforms:
                for member in platforms:
                    if member not in tcplatforms:
                        platform_ok = False
                    else:
                        platform_ok = True
                        break
        return platform_ok

    @staticmethod
    def _match_rest(string_to_match, args):
        """
        Matcher for generic metadata

        :param string_to_match: Filter string to match against.
        :param args: arguments as list or tuple, args[0] must be test case metadata as
        dictionary, args[1] must be list of filter keys, args[2] must be key currently
        being processed.

        :return: Boolean
        """
        testcase = args[0]
        filter_keys = args[1]
        filter_key = args[2]
        rest_ok = True
        if filter_key in filter_keys and string_to_match:
            # Possible that string comparison can cause encoding comparison error.
            # In the case where the caseFilter is 'all', the step is skipped
            if filter_key == 'name' and string_to_match == 'all':
                return True
            if isinstance(testcase[filter_key], list):
                if isinstance(
                        string_to_match, str) and string_to_match not in testcase[filter_key]:
                    return False

            elif isinstance(testcase[filter_key], str):
                # pylint: disable=unsupported-membership-test
                if isinstance(string_to_match, str) and testcase[filter_key] != string_to_match:
                    return False
                elif isinstance(
                        string_to_match, list) and testcase[filter_key] not in string_to_match:
                    return False
        return rest_ok

    def match(self, testcase, tc_index):  # pylint: disable=too-many-branches,too-many-statements
        """
        Match function. Matches testcase information with this filter.

        :param testcase: TestcaseContainer instance
        :param tc_index: Index of testcase in list
        :return: True if all filter fields were successfully matched. False otherwise.
        """
        testcase = testcase.get_infodict()
        filter_keys = self._filter.keys()
        list_ok = self._match_list(testcase, tc_index)
        try:
            if self._filter["group"]:
                group_ok = create_match_bool(self._filter["group"], self._match_group, (testcase,
                                                                                        filter_keys)
                                            )
            else:
                group_ok = True
        except SyntaxError as error:
            raise FilterException("Error while handling group filter {}".format(
                self._filter["group"]), error)
        try:
            if self._filter["platform"]:
                platform_ok = create_match_bool(self._filter["platform"],
                                                self._match_platform, (testcase, filter_keys))
            else:
                platform_ok = True
        except SyntaxError as error:
            raise FilterException("Error while handling platform filter {}".format(
                self._filter["platform"]), error)

        keys = ['status', 'type', 'subtype', 'comp', 'name', 'feature']
        rest_ok = True
        for key in keys:
            try:
                if self._filter[key]:
                    key_ok = create_match_bool(self._filter[key], self._match_rest, (testcase,
                                                                                     filter_keys,
                                                                                     key))
                    if not key_ok:
                        rest_ok = False
                        break
            except SyntaxError as error:
                raise FilterException(
                    "Error while handling filter {}: {}".format(key, self._filter[key]), error)

        return list_ok and group_ok and rest_ok and platform_ok

    def _add_filter_key(self, key, value):
        """
        Helper for populating filter keys.

        :param key: str
        :param value: multiple types, value to set.
        :return: TestcaseFilter (self).
        """
        if not key or not value:
            return self
        if not isinstance(value, str):
            raise TypeError("createFilter: filter argument {} not string.")
        self._filter[key] = value
        return self
