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

__author__ = 'jaakuk03'
import unittest
import mock
import sys
import os
import re
import icetea_lib.tools.tools as tools
from pkg_resources import DistributionNotFound

class TestClass():
    def __init__(self):
        self.test = True


def testingfunction(arg1, arg2):  # pylint: disable=unused-argument
    pass


class TestTools(unittest.TestCase):
    def test_loadClass_Success(self):
        sys.path.append(os.path.dirname(__file__))
        # Test that loadClass can import a class that is initializable
        module = tools.load_class("test_tools.TestClass", verbose=False, silent=True)
        self.assertIsNotNone(module)
        moduleInstance = module()
        self.assertTrue(moduleInstance.test)
        del moduleInstance

    def test_loadClass_Fail(self):
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
                    m = re.search(r"VERSION = \"([\S]{5,})\"", line)
                    if m:
                        version = m.group(1)
                        break
        except Exception as e:
            pass

        v = tools.get_fw_version()
        self.assertEqual(v, version)

        with mock.patch("icetea_lib.tools.tools.require") as mocked_require:
            mocked_require.side_effect = [DistributionNotFound]
            v = tools.get_fw_version()
            self.assertEqual(v, version)

    def test_check_int(self):
        integer = "10"
        prefixedinteger = "-10"
        decimal = "10.1"
        self.assertTrue(tools.check_int(integer))
        self.assertTrue(tools.check_int(prefixedinteger))
        self.assertFalse(tools.check_int(decimal))
        self.assertFalse(tools.check_int(1))

    def test_remove_empty_from_dict(self):
        d = {"test": "val", "test2": None}
        d = tools.remove_empty_from_dict(d)
        self.assertDictEqual({"test": "val"}, d)

    def test_setordelete(self):
        d = {"test": "val",
             "test2": "val2"}
        tools.set_or_delete(d, "test", "val3")
        self.assertEqual(d.get("test"), "val3")
        tools.set_or_delete(d, "test2", None)
        self.assertTrue("test2" not in d)

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
