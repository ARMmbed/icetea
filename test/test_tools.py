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

import json
import unittest
import sys
import os
import re
import mock
from pkg_resources import DistributionNotFound
import icetea_lib.tools.tools as tools
# pylint: disable=missing-docstring,too-few-public-methods,protected-access
# pylint: disable=inconsistent-return-statements


class TestClass(object):
    def __init__(self):
        self.test = True


def testingfunction(arg1, arg2):  # pylint: disable=unused-argument
    pass


class TestTools(unittest.TestCase):
    def test_load_class_success(self):
        sys.path.append(os.path.dirname(__file__))
        # Test that loadClass can import a class that is initializable
        module = tools.load_class("test_tools.TestClass", verbose=False, silent=True)
        self.assertIsNotNone(module)
        module_instance = module()
        self.assertTrue(module_instance.test)
        del module_instance

    def test_load_class_fail(self):
        with self.assertRaises(Exception):
            tools.load_class('testbase.level1.Testcase', verbose=False, silent=True)

        self.assertIsNone(tools.load_class('', verbose=False, silent=True))
        self.assertIsNone(tools.load_class(5, verbose=False, silent=True))
        self.assertIsNone(tools.load_class([], verbose=False, silent=True))
        self.assertIsNone(tools.load_class({}, verbose=False, silent=True))

    def test_combine_urls(self):
        self.assertEquals(tools.combine_urls("/path/one/", "path2"), "/path/one/path2")
        self.assertEquals(tools.combine_urls("/path/one", "path2"), "/path/one/path2")
        self.assertEquals(tools.combine_urls("/path/one/", "/path2"), "/path/one/path2")
        self.assertEquals(tools.combine_urls("/path/one", "/path2"), "/path/one/path2")

    def test_hex_escape_tester(self):
        failing_message = "\x00\x00\x00\x00\x00\x00\x01\xc8"
        success_message = "\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\xc8"

        converted = tools.hex_escape_str(failing_message)
        self.assertEqual(converted, success_message)

    def test_get_fw_version(self):
        version = None
        try:
            setup_path = os.path.abspath(os.path.dirname(__file__)+'/..')
            with open(os.path.join(setup_path, 'setup.py')) as setup_file:
                lines = setup_file.readlines()
                for line in lines:
                    match = re.search(r"VERSION = \"([\S]{5,})\"", line)
                    if match:
                        version = match.group(1)
                        break
        except Exception:  # pylint: disable=broad-except
            pass

        got_version = tools.get_fw_version()
        self.assertEqual(got_version, version)

        with mock.patch("icetea_lib.tools.tools.require") as mocked_require:
            mocked_require.side_effect = [DistributionNotFound]
            got_version = tools.get_fw_version()
            self.assertEqual(got_version, version)

    def test_check_int(self):
        integer = "10"
        prefixedinteger = "-10"
        decimal = "10.1"
        self.assertTrue(tools.check_int(integer))
        self.assertTrue(tools.check_int(prefixedinteger))
        self.assertFalse(tools.check_int(decimal))
        self.assertFalse(tools.check_int(1))

    def test_remove_empty_from_dict(self):
        dictionary = {"test": "val", "test2": None}
        dictionary = tools.remove_empty_from_dict(dictionary)
        self.assertDictEqual({"test": "val"}, dictionary)

    def test_setordelete(self):
        dictionary = {"test": "val",
                      "test2": "val2"}
        tools.set_or_delete(dictionary, "test", "val3")
        self.assertEqual(dictionary.get("test"), "val3")
        tools.set_or_delete(dictionary, "test2", None)
        self.assertTrue("test2" not in dictionary)

    def test_getargspec(self):
        expected_args = ["arg1", "arg2"]
        spec = tools.getargspec(testingfunction)
        for item in expected_args:
            self.assertTrue(item in spec.args)

    def test_strip_escape(self):
        test_data_no_escapes = "aaaa"
        self.assertEqual(tools.strip_escape(test_data_no_escapes), "aaaa")
        test_data_encoded = "aaaa".encode("utf-8")
        self.assertEqual(tools.strip_escape(test_data_encoded), "aaaa")
        mock_str = mock.MagicMock()
        mock_str.decode = mock.MagicMock(side_effect=[UnicodeDecodeError])
        with self.assertRaises(TypeError):
            tools.strip_escape(mock_str)

    def test_json_duplicate_keys(self):
        dict1 = '{"x": "1", "y": "1", "x": "2"}'
        with self.assertRaises(ValueError):
            json.loads(dict1, object_pairs_hook=tools.find_duplicate_keys)

        dict2 = '{"x": "1", "y": {"x": "2"}}'
        expected = {"y": {"x": "2"}, "x": "1"}
        self.assertDictEqual(json.loads(dict2, object_pairs_hook=tools.find_duplicate_keys),
                             expected)

    def test_create_combined_set(self):
        test_phrase = "filter3 and (filter1 or filter2)"
        test_list = test_phrase.split(" ")
        combined, _ = tools._create_combined_set(test_list, 2)
        self.assertEqual(combined, "(filter1 or filter2)")

        test_phrase = "(filter3 and (filter1 or filter2))"
        test_list = test_phrase.split(" ")
        combined, _ = tools._create_combined_set(test_list, 0)
        self.assertEqual(combined, "(filter3 and (filter1 or filter2))")

        test_phrase = "filter3 and (filter1 or filter2"
        test_list = test_phrase.split(" ")
        combined, _ = tools._create_combined_set(test_list, 2)
        self.assertIsNone(combined)

    def test_create_combined_words(self):
        test_phrase = "filter3 and 'filter1 with filter2'"
        test_list = test_phrase.split(" ")
        combined, _ = tools._create_combined_words(test_list, 2)
        self.assertEqual(combined, "'filter1 with filter2'")

    def test_create_match_bool(self):
        test_data = list()
        test_data.append("filter1")
        test_data.append("filter1,filter2")
        test_data.append("filter1 or filter2")
        test_data.append("(filter1 or filter2)")
        test_data.append("filter1 and filter2")
        test_data.append("filter3 and (filter1 or filter2)")
        test_data.append("filter1 and 'filter2 with filter3'")
        test_data.append("filter1 and ('filter2 with filter3' or filter1)")
        test_data.append("(filter1 or filter2 and (((not (filter3)) "
                         "and not filter4) and not filter5))")

        def eval_func(str_to_match, args):  # pylint: disable=unused-argument
            if str_to_match == "filter1":
                return True
            elif str_to_match == "filter2":
                return False
            elif str_to_match == "filter3":
                return True
            elif str_to_match == "filter4":
                return True
            elif str_to_match == "filter5":
                return False
            elif str_to_match == "filter2 with filter3":
                return True

        # Check that no exceptions are raised
        for test_string in test_data:
            tools.create_match_bool(test_string, eval_func, None)

        self.assertTrue(tools.create_match_bool(test_data[0], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[1], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[2], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[3], eval_func, None))
        self.assertFalse(tools.create_match_bool(test_data[4], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[5], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[6], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[7], eval_func, None))
        self.assertTrue(tools.create_match_bool(test_data[8], eval_func, None))
        test_data.append("filter3 and (filter1 or filter2")
        with self.assertRaises(SyntaxError):
            tools.create_match_bool(test_data[9], eval_func, None)
