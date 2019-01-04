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

import unittest
import json
import os
import mock

from icetea_lib.TestSuite.TestcaseContainer import TestcaseContainer, DummyContainer
from icetea_lib.TestSuite.TestcaseList import TestcaseList
# pylint: disable=missing-docstring,protected-access


class TCListTestcase(unittest.TestCase):

    def setUp(self):
        with open(os.path.join("./icetea_lib", 'tc_schema.json')) as data_file:
            self.tc_meta_schema = json.load(data_file)

    def test_append_and_len(self):
        testcase = TestcaseContainer.find_testcases("examples.test_cmdline",
                                                    "examples", self.tc_meta_schema)
        tlist = TestcaseList()
        tlist.append(testcase[0])
        self.assertEqual(len(tlist), 1)
        tlist.append(testcase[0])
        self.assertEqual(len(tlist), 2)

    @mock.patch("icetea_lib.TestSuite.TestcaseList.TestcaseContainer.find_testcases")
    def test_parse_local_testcases_exceptions(self, mock_finder):  # pylint: disable=invalid-name
        mock_finder.side_effect = [IndexError, TypeError, ValueError, ImportError, [1], [2]]
        lst = TestcaseList()
        self.assertEqual(len(lst._parse_local_testcases("", False)), 0)
        lst._parse_local_testcases(["1234", "1234", "1234", "1234", "1234"], False)

    def test_filtering_adds_dummycontainers(self):  # pylint: disable=invalid-name
        filt = mock.MagicMock()
        filt.match = mock.MagicMock()
        filt.match.side_effect = [True, False, True]
        filt.get_filter = mock.MagicMock(return_value={"list": [0, 0, 0], "name": False})
        tclist = TestcaseList()
        mock_tc = mock.MagicMock()
        tcname = mock.PropertyMock(return_value="test_case")
        type(mock_tc).tcname = tcname
        tclist.append(mock_tc)
        new_list = tclist.filter(filt, ["test_case", "test_case_2", "test_case"])
        self.assertEqual(len(new_list), 3)
        self.assertTrue(isinstance(new_list.get_list()[1], DummyContainer))
        self.assertFalse(isinstance(new_list.get_list()[0], DummyContainer))
        self.assertFalse(isinstance(new_list.get_list()[2], DummyContainer))

    @mock.patch("icetea_lib.TestSuite.TestcaseList.TestcaseContainer.find_testcases")
    def test_import_error_store(self, mock_finder):
        mock_finder.side_effect = [ImportError]
        tclist = TestcaseList()
        self.assertEqual(len(tclist.search_errors), 0)
        tclist._parse_local_testcases([["examples.test_cmdline", "examples",
                                        "examples/test_cmdline.py"]], False)
        self.assertEqual(len(tclist.search_errors), 1)


if __name__ == '__main__':
    unittest.main()
