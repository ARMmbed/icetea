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

import traceback
import os
import sys
from copy import copy
from collections import Counter

from icetea_lib.TestSuite.TestcaseContainer import TestcaseContainer, DummyContainer


class TestcaseList(object):
    """
    TestcaseList object, a list-like structure with helpers to collect local test cases and
    filter found tests for running.
    """
    def __init__(self, logger=None, testcases=None):
        self.logger = logger
        self._testcases = testcases if testcases else []
        self.search_errors = []
        if self.logger is None:
            import logging
            self.logger = logging.getLogger("TestcaseList")
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())
                self.logger.setLevel(logging.INFO)

    def __iter__(self):
        return iter(self._testcases)

    def __len__(self):
        return len(self._testcases)

    def get_list(self):
        """
        Returns the internal list of TestcaseContainers
        """
        return self._testcases

    def get_names(self):
        """
        Gets names of test cases in this TestcaseList.

        :return: list
        """
        lst = []
        for testcase in self._testcases:
            lst.append(testcase.tcname)
        return lst

    def filter(self, filt, tc_names=None):
        """
        Filter test cases from this list into a new TestcaseList object.
        :param filt: TestcaseFilter
        :param tc_names: List of test case names. Is used when running with tc or with a suite
        :return: new TestcaseList with filtered test cases.
        """
        templist = TestcaseList(self.logger)
        if tc_names is not None:
            self._filter_from_names(tc_names, templist, filt)
        else:
            for i, testcase in enumerate(self._testcases):
                if filt.match(testcase, i):
                    templist.append(testcase)

        # Check that all named testcases were found. Append dummies if some are missing
        self._check_filtered_tcs(filt, templist)
        templist.search_errors = self.search_errors
        return templist

    def import_from_path(self, path="./testcases"):
        """
        Import test cases from path to this TestcaseList

        :param path: Path to import from
        :return: Nothing
        """
        local_testcases = self._get_local_testcases(path)
        self._testcases = self._parse_local_testcases(local_testcases, True)

    def get(self, index):
        """
        dict-like getter based on index.

        :param index: Index of test case
        :return: TestcaseContainer or None if index is outside len
        """
        return self._testcases[index] if index < len(self) else None

    def append(self, val):
        """
        Append val to internal list of test cases.

        :param val: test case to append
        :return: Nothing
        """
        self._testcases.append(val)

    def _get_local_testcases(self, tcpath):
        """
        Crawl given path for .py files
        """
        i = 0
        returnlist = []
        if not isinstance(tcpath, str):
            self.logger.error("Error: testcase path is not string")
            sys.exit(0)

        # path is absolute
        tcpath = os.path.abspath(tcpath)
        if len(tcpath.split(os.sep)) > 1:
            strip_dir = os.sep.join(tcpath.split(os.sep)[:-1]) + os.sep
        else:
            strip_dir = ''

        for root, _, files in os.walk(tcpath):
            for file_handle in sorted(files):
                basename, extension = os.path.splitext(file_handle)
                if (basename == '__init__') or extension != '.py':
                    continue
                moduleroot = ''
                modulename = ''
                moduleroot = root.replace(strip_dir, '', 1)
                modulename = moduleroot.replace(os.sep, ".") + '.' + basename
                returnlist.append((modulename, moduleroot, root + os.sep + file_handle))
                i += 1
        if i == 0:
            self.logger.error("Error: No files found in given path: %s", tcpath)
        return returnlist

    def _parse_local_testcases(self, tc_list, verbose):
        """
        Parse list produced by get_local_testcases()
        """
        return_list = []
        if not isinstance(tc_list, list):
            self.logger.error("Error, parseLocalTestcases: Given argument not a list.")
            return return_list
        i = 0
        from icetea_lib.IceteaManager import TCMetaSchema
        schema = TCMetaSchema().get_meta_schema()
        for testcase in tc_list:
            i += 1
            try:
                parsedcases = TestcaseContainer.find_testcases(modulename=testcase[0],
                                                               moduleroot=testcase[1],
                                                               path=testcase[2],
                                                               tc_meta_schema=schema,
                                                               logger=self.logger)
                return_list.extend(parsedcases)
            except (IndexError, TypeError, ValueError):
                self.logger.error("Error, parse_local_testcases: Malformed list item. "
                                  "Skipping item %d", i)
                self.logger.debug("tc: %s", str(testcase))
                if verbose:
                    traceback.print_exc()
            except ImportError as error:
                error_item = {"module": testcase[0], "error": error}
                self.search_errors.append(error_item)
                continue
        return return_list

    def _filter_from_names(self, tc_names, tclist, filt):
        """
        Fill out missing test cases with dummies if a names test case is missing.

        :param tc_names: List of test case names requested.
        :param tclist: List of found test cases.
        :param filt: TestcaseFilter.
        :return: Nothing, modifies tclist in place.
        """
        for tcname in tc_names:
            found = False
            for i, testcase in enumerate(self._testcases):
                if filt.match(testcase, i) and testcase.tcname == tcname:
                    if testcase in tclist:
                        tclist.append(copy(testcase))
                    else:
                        tclist.append(testcase)
                    found = True
            if not found:
                dummy = DummyContainer(self.logger)
                dummy.tcname = tcname
                dummy.set_result_verdict("Test case not found")
                tclist.append(dummy)

    def _check_filtered_tcs(self, filt, tclist):
        """
        Check filtered test cases afor a few special circumstances.

        :param filt: TestcaseFilter.
        :param tclist: List of test cases.
        :return: Nothing, modifies tclist in place.
        """
        if filt.get_filter().get("name") is not False and filt.get_filter().get("name") != "all":
            # If --tc filter is set, length can be max 1
            if len(tclist) != 1:
                dummy = DummyContainer(self.logger)
                dummy.tcname = filt.get_filter().get("name")
                dummy.set_result_verdict("Test case not found")
                tclist.append(dummy)

        if filt.get_filter().get("list") is not False:
            if len(tclist) < len(filt.get_filter().get("list")):
                needed_names = filt.get_filter().get("list")
                found_names = tclist.get_names()
                counter1 = Counter(needed_names)
                counter2 = Counter(found_names)
                diff = counter1 - counter2
                lst = list(diff.elements())

                for name in lst:
                    dummy = DummyContainer(self.logger)
                    dummy.tcname = name
                    dummy.set_result_verdict("Test case not found")
                    tclist.append(dummy)
