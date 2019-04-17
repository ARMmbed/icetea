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

# pylint: disable=missing-docstring,protected-access

import os
import unittest

from icetea_lib.IceteaManager import TCMetaSchema
from icetea_lib.TestSuite.TestcaseContainer import TestcaseContainer
from icetea_lib.TestSuite.TestcaseFilter import TestcaseFilter


class TCFilterTestcase(unittest.TestCase):

    def setUp(self):
        self.schemapath = os.path.abspath(os.path.join(__file__, os.path.pardir,
                                                       os.path.pardir, "icetea_lib"))

    def test_create_filter_simple(self):
        filt = TestcaseFilter().tc("test_cmdline")
        self.assertDictEqual(filt._filter, {'status': False,
                                            'group': False,
                                            'name': 'test_cmdline',
                                            'comp': False,
                                            'platform': False,
                                            'list': False,
                                            'subtype': False,
                                            'type': False,
                                            'feature': False})

        with self.assertRaises(TypeError):
            TestcaseFilter().tc(0)
        with self.assertRaises(IndexError):
            TestcaseFilter().tc([])
        with self.assertRaises(TypeError):
            TestcaseFilter().tc(None)
        with self.assertRaises(TypeError):
            TestcaseFilter().tc(True)

        self.assertDictEqual(TestcaseFilter().tc(1)._filter, {'status': False,
                                                              'group': False,
                                                              'name': False,
                                                              'comp': False,
                                                              'platform': False,
                                                              'list': [0],
                                                              'subtype': False,
                                                              'type': False,
                                                              'feature': False})

        self.assertDictEqual(TestcaseFilter().tc([1, 4])._filter, {'status': False,
                                                                   'group': False,
                                                                   'name': False,
                                                                   'comp': False,
                                                                   'platform': False,
                                                                   'list': [0, 3],
                                                                   'subtype': False,
                                                                   'type': False,
                                                                   'feature': False})

    def test_create_filter_complex(self):
        filt = TestcaseFilter()

        filt.tc("test_test")
        filt.component("test_comp")
        filt.group("test_group")
        filt.status("test_status")
        filt.testtype("test_type")
        filt.subtype("test_subtype")
        filt.feature("test_feature")
        filt.platform("test_platform")

        self.assertDictEqual(filt._filter, {"status": "test_status", "group": "test_group",
                                            "name": "test_test",
                                            "type": "test_type", "subtype": "test_subtype",
                                            "comp": "test_comp", 'list': False,
                                            'feature': "test_feature",
                                            "platform": "test_platform"})

        with self.assertRaises(TypeError):
            filt.component(2)

    def test_create_filter_list(self):
        filt = TestcaseFilter()
        filt.tc("test_test,test_test2")
        self.assertDictEqual(filt._filter, {"status": False, "group": False,
                                            "name": False, "type": False,
                                            "subtype": False, "comp": False,
                                            'list': ["test_test", "test_test2"], 'feature': False,
                                            "platform": False})

    def test_match(self):
        testcase = TestcaseContainer.find_testcases(
            "examples.test_cmdline", "." + os.path.sep + "examples",
            TCMetaSchema().get_meta_schema())
        filt = TestcaseFilter().tc("test_cmdline")
        self.assertTrue(filt.match(testcase[0], 0))
        filt.component("cmdline,testcomponent")
        filt.group("examples")
        self.assertTrue(filt.match(testcase[0], 0))
        filt.tc("test_something_else")
        self.assertFalse(filt.match(testcase[0], 0))
        filt = TestcaseFilter().tc([1])
        self.assertTrue(filt.match(testcase[0], 0))
        self.assertFalse(filt.match(testcase[0], 1))

    def test_match_complex(self):
        filt = TestcaseFilter().feature("feature1 or feature2")
        testcase = TestcaseContainer.find_testcases("test.tests.matching_test.feature2_test",
                                                    "." + os.path.sep + "test" + os.path.sep +
                                                    "tests" + os.path.sep + "matching_test",
                                                    TCMetaSchema(self.schemapath).get_meta_schema())
        self.assertTrue(filt.match(testcase[0], 0))
        testcase = TestcaseContainer.find_testcases("test.tests.matching_test.feature1_test",
                                                    "." + os.path.sep + "test" + os.path.sep +
                                                    "tests" + os.path.sep + "matching_test",
                                                    TCMetaSchema(self.schemapath).get_meta_schema())
        self.assertTrue(filt.match(testcase[0], 0))
        testcase = TestcaseContainer.find_testcases(
            "test.tests.matching_test.feature_and_component_test",
            "." + os.path.sep + "test" + os.path.sep +
            "tests" + os.path.sep + "matching_test",
            TCMetaSchema().get_meta_schema())
        filt = filt.component("component2")
        self.assertTrue(filt.match(testcase[0], 0))
        filt = filt.component("component1")
        self.assertFalse(filt.match(testcase[0], 0))

        filt = TestcaseFilter().feature("not feature2")
        testcase = TestcaseContainer.find_testcases("test.tests.matching_test.feature2_test",
                                                    "." + os.path.sep + "test" + os.path.sep +
                                                    "tests" + os.path.sep + "matching_test",
                                                    TCMetaSchema(self.schemapath).get_meta_schema())
        self.assertFalse(filt.match(testcase[0], 0))
        filt = TestcaseFilter().component("component1")
        testcase = TestcaseContainer.find_testcases("test.tests.matching_test.component1_test",
                                                    "." + os.path.sep + "test" + os.path.sep +
                                                    "tests" + os.path.sep + "matching_test",
                                                    TCMetaSchema(self.schemapath).get_meta_schema())
        self.assertTrue(filt.match(testcase[0], 0))
        testcase = TestcaseContainer.find_testcases("test.tests.matching_test.component1and2_test",
                                                    "." + os.path.sep + "test" + os.path.sep +
                                                    "tests" + os.path.sep + "matching_test",
                                                    TCMetaSchema(self.schemapath).get_meta_schema())
        self.assertTrue(filt.match(testcase[0], 0))

    def test_match_platform(self):
        meta = {"allowed_platforms": ["PLAT1", "PLAT2"]}
        filters = {"platform": "PLAT1"}
        string_to_match = "PLAT1"
        result = TestcaseFilter._match_platform(string_to_match, (meta, filters))
        self.assertTrue(result)
        string_to_match = "PLAT3"
        result = TestcaseFilter._match_platform(string_to_match, (meta, filters))
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
