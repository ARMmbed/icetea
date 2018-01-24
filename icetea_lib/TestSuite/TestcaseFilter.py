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

class TestcaseFilter(object):
    """
    TestcaseFilter class. Provides the handling for different filtering arguments.
    Provides a match function to match testcases with filter.
    """
    def __init__(self):
        self._filter = {'list': False, 'name': False, 'status': False,
                        'group': False, 'type': False, 'subtype': False,
                        'comp': False, 'feature': False, 'platform': False}

    def tc(self, value):
        # tc can be:
        # int, tuple, list or str(any of the above)
        if isinstance(value, str):
            # Wildcard chjeck
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
                elif len(pfilter) == 0:
                    pass

            value = pfilter

        if isinstance(value, int) and (value is not False and value is not True):
            if value < 1:
                raise TypeError("Error, createFilter: non-positive integer " + str(value))
            else:
                self._filter['list'] = [value - 1]
        elif isinstance(value, list) or isinstance(value, tuple):
            if len(value) < 1:
                raise IndexError("Error, createFilter: Index list empty.")
            for i in value:
                if not isinstance(i, int) and not isinstance(i, str):
                    raise TypeError("Error, createFilter: Index list has invalid member: %s" % str(value))
            self._filter['list'] = [x - 1 for x in value if isinstance(x, int)]
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
        return self._filter

    def match(self, testcase, tc_index):
        """
        Match function. Matches testcase information with this filter.

        :param testcase: TestcaseContainer instance
        :param tc_index: Index of testcase in list
        :return: True if all filter fields were successfully matched to information.
        False otherwise.
        """
        list_ok = False
        testcase = testcase.get_infodict()
        if 'list' in self._filter.keys() and self._filter['list']:
            for index in self._filter['list']:
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

        group_ok = False
        if 'group' in self._filter.keys() and self._filter['group']:
            group = self._filter['group'].split(os.sep)
            group = [x for x in group if len(x)] # Remove empty members
            if len(group) == 1:
                group = self._filter['group'].split(',')
            tcgroup = testcase['group'].split(os.sep)
            for member in group:
                if member not in tcgroup:
                    group_ok = False
                    break
                else:
                    group_ok = True
        else:
            group_ok = True

        platform_ok = True
        if 'platform' in self._filter.keys() and self._filter['platform']:
            platforms = self._filter['platform']
            platforms = platforms if isinstance(platforms, list) else [platforms]
            tcplatforms = testcase['allowed_platforms']
            if tcplatforms:
                for member in platforms:
                    if member not in tcplatforms:
                        platform_ok = False
                    else:
                        platform_ok = True
                        break

        rest_ok = True
        keys = ['status', 'type', 'subtype', 'comp', 'name', 'feature']
        for key in keys:
            if key in self._filter.keys() and self._filter[key]:
                # Possible that string comparison can cause encoding comparison error.
                # In the case where the caseFilter is 'all', the step is skipped
                if key == 'name' and self._filter[key] == 'all':
                    continue
                if isinstance(testcase[key], list):
                    if isinstance(self._filter[key], str) and self._filter[key] not in testcase[key]:
                        rest_ok = False
                        break
                    if isinstance(self._filter[key], list):
                        one_found = False
                        for k in self._filter[key]:
                            if k in testcase[key]:
                                one_found = True
                                break
                        if not one_found:
                            rest_ok = False
                            break
                elif isinstance(testcase[key], str):
                    if isinstance(self._filter[key], str) and testcase[key] != self._filter[key]:
                        rest_ok = False
                        break
                    elif isinstance(self._filter[key], list) and testcase[key] not in self._filter[key]:
                        rest_ok = False
                        break

        return list_ok and group_ok and rest_ok and platform_ok

    def _add_filter_key(self, key, value):
        if not key or not value:
            return self
        if not isinstance(value, str):
            raise TypeError("createFilter: filter argument {} not string.")
        if len(value.split(",")) > 1:
            self._filter[key] = value.split(",")
        else:
            self._filter[key] = value
        return self