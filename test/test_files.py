# pylint: disable=missing-docstring,pointless-string-statement

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
import os
import sys
import unittest

import jsonmerge
import mock

import icetea_lib.tools.file.FileUtils as FileUtils
from icetea_lib.tools.file.SessionFiles import JsonFile


class FileTestCase(unittest.TestCase):

    def setUp(self):
        self.file_name = "test_file"
        self.file_path = os.path.join("path", "to", "right")
        self.file_path2 = os.path.join("path", "of", "no", "rights") + os.path.sep
        self.non_existing_file = "NoFile"
        self.test_json = {"test1": "value1", "test2": "value2", "test3": "value3", "test4": "test5"}
        self.test_json2 = {"Test": "Value", "Test1": "Value1", "Test2": "Value2"}
        self.jsonfile = JsonFile()

    '''
        FileUtils tests here
    '''

    @mock.patch("icetea_lib.tools.file.FileUtils.os.chdir")
    @mock.patch("icetea_lib.tools.file.FileUtils.os.remove")
    def test_remove_file(self, mock_rm, mock_chdir):
        mock_chdir.side_effect = iter([OSError, 1, 1, 1, 1])
        mock_rm.side_effect = iter([OSError, 1])
        path_nowhere = os.path.join("testPath", "to", "nowhere")
        path_somewhere = os.path.join("testPath", "to", "somewhere")
        with self.assertRaises(OSError):
            FileUtils.remove_file("testName", path_nowhere)
        with self.assertRaises(OSError):
            FileUtils.remove_file("testName", path_nowhere)
        self.assertTrue(FileUtils.remove_file("testName", path_somewhere))

    @mock.patch("icetea_lib.tools.file.FileUtils.os.chdir")
    @mock.patch("icetea_lib.tools.file.FileUtils.os.rename")
    def test_rename_file(self, mock_rn, mock_chdir):
        mock_chdir.side_effect = iter([OSError, 1, 1, 1, 1])
        mock_rn.side_effect = iter([OSError, 1])
        path_nowhere = os.path.join("testPath", "to", "nowhere")
        path_somewhere = os.path.join("testPath", "to", "somewhere")
        with self.assertRaises(OSError):
            FileUtils.rename_file("testName", "new_testName", path_nowhere)
        with self.assertRaises(OSError):
            FileUtils.rename_file("testName", "new_testName", path_nowhere)
        self.assertTrue(FileUtils.rename_file("testName", "new_testName", path_somewhere))

    '''
        JsonFile tests start here
    '''

    def test_writing_file(self):
        # run test for saving a json to a new file. File path should not exists so it is created.
        self.jsonfile.write_file(self.test_json, self.file_path, self.file_name, 2)
        self.assertTrue(os.path.exists(self.file_path + os.path.sep + self.file_name + ".json"))
        with open(self.file_path + os.path.sep + self.file_name + ".json", 'r') as file_opened:
            self.assertDictEqual(json.load(file_opened), self.test_json)

        # save a json to an old file to overwrite entire file
        self.jsonfile.write_file(self.test_json2, self.file_path, self.file_name, 2)
        with open(self.file_path + os.path.sep + self.file_name + ".json", 'r') as file_opened:
            self.assertDictEqual(json.load(file_opened), self.test_json2)

    @unittest.skipIf(sys.platform == 'win32', "os.chmod with 0o444 or stat.S_IREAD doesn't work")
    def test_writing_file_fail_windows(self):
        # run test to save json to a file with an invalid path
        os.makedirs(self.file_path2, 0o777)
        os.chmod(self.file_path2, 0o444)
        with self.assertRaises(IOError):
            self.jsonfile.write_file(self.test_json, self.file_path2, self.file_name, 2)

    def test_writing_with_filter(self):
        self.jsonfile.write_file(self.test_json, self.file_path, self.file_name, 2,
                                 keys_to_write=["test1", "test2"])
        ref = {"test1": self.test_json["test1"], "test2": self.test_json["test2"]}
        with open(self.file_path + os.path.sep + self.file_name + ".json", 'r') as file_opened:
            self.assertDictEqual(json.load(file_opened), ref)

        self.jsonfile.write_file(self.test_json, self.file_path, self.file_name, 2)
        self.jsonfile.write_values(self.test_json2, self.file_path, self.file_name, 2,
                                   keys_to_write=["Test"])
        with open(self.file_path + os.path.sep + self.file_name + ".json", 'r') as file_opened:
            self.assertDictEqual(jsonmerge.merge(self.test_json,
                                                 {"Test": self.test_json2["Test"]}),
                                 json.load(file_opened))


    @mock.patch("icetea_lib.tools.file.SessionFiles.JsonFile._write_json")
    @mock.patch("icetea_lib.tools.file.SessionFiles.os.path.exists")
    @mock.patch("icetea_lib.tools.file.SessionFiles.os.makedirs")
    def test_write_file_errors(self, mock_mkdir, mock_exists, mock_json):
        mock_mkdir.side_effect = iter([OSError])
        mock_exists.side_effect = iter([False, True, True])
        mock_json.side_effect = iter([EnvironmentError, ValueError])
        with self.assertRaises(OSError):
            self.jsonfile.write_file(self.test_json, self.file_path, self.file_name)
        with self.assertRaises(EnvironmentError):
            self.jsonfile.write_file(self.test_json, self.file_path, self.file_name)
        with self.assertRaises(ValueError):
            self.jsonfile.write_file(self.test_json, self.file_path, self.file_name)

    def test_reading_file(self):
        #Write test data
        self.jsonfile.write_file(self.test_json, self.file_path, self.file_name, 2)
        # read json from nonexisting file
        with self.assertRaises(IOError):
            self.jsonfile.read_file(self.file_path, self.non_existing_file)

        # read json from existing file
        data = self.jsonfile.read_file(self.file_path, self.file_name)
        self.assertDictEqual(data, self.test_json)
        #ToDo: read from malformed file

    def test_writing_values(self):
        #Test writing to a malformed file.
        self.jsonfile.write_file("", self.file_path, "malformed_" + self.file_name)
        with self.assertRaises(TypeError):
            self.jsonfile.write_values(self.test_json, self.file_path,
                                       "malformed_" + self.file_name)

        cwd = os.getcwd()
        os.chdir(self.file_path)
        open("empty_" + self.file_name + ".json", "w")
        os.chdir(cwd)
        self.assertEquals(self.jsonfile.write_values(self.test_json, self.file_path,
                                                     "empty_" + self.file_name),
                          os.path.join(self.file_path, "empty_" + self.file_name + ".json"))

        # save a json to a new file with write_values instead of write_file
        self.assertEqual(self.jsonfile.write_values(self.test_json, self.file_path,
                                                    self.file_name, 2),
                         self.file_path + os.path.sep + self.file_name + ".json")

        # save a json to an old file to append to existing data
        self.jsonfile.write_file(self.test_json, self.file_path, self.file_name, 2)
        self.jsonfile.write_values(self.test_json2, self.file_path, self.file_name, 2)
        with open(self.file_path + os.path.sep + self.file_name + ".json", 'r') as file_opened:
            self.assertDictEqual(jsonmerge.merge(self.test_json, self.test_json2),
                                 json.load(file_opened))

    @unittest.skipIf(sys.platform == 'win32', "os.chmod with 0o444 or stat.S_IREAD doesn't work")
    def test_writing_value_fail_windows(self):
        # Try adding content to a file with no write permissions
        os.makedirs(self.file_path2, 0o777)
        self.jsonfile.write_file(self.test_json2, self.file_path2, self.file_name, 2)
        os.chmod(self.file_path2, 0o444)
        with self.assertRaises(IOError):
            self.jsonfile.write_values(self.test_json, self.file_path2, self.file_name, 2)

    def test_reading_values(self):
        # Test writing to a malformed file.
        self.jsonfile.write_file("", self.file_path, "malformed_" + self.file_name)
        with self.assertRaises(KeyError):
            self.jsonfile.read_value("test1", self.file_path, "malformed_" + self.file_name)

        # read json from nonexisting file
        with self.assertRaises(IOError):
            self.jsonfile.read_value("Test1", self.file_path, self.file_name)

        # Create test data for reading
        self.jsonfile.write_file(self.test_json, self.file_path, self.file_name, 2)
        # read json from existing file

        self.assertEqual("value1", self.jsonfile.read_value("test1",
                                                            self.file_path, self.file_name))

        # try to read nonexisting key
        with self.assertRaises(KeyError):
            self.jsonfile.read_value("value1", self.file_path, self.file_name)

    def tearDown(self):
        # Do tearDown stuff.
        if os.path.exists(os.path.join(self.file_path, "malformed_" + self.file_name + ".json")):
            FileUtils.remove_file("malformed_" + self.file_name + ".json",
                                  self.file_path + os.path.sep)

        if os.path.exists(os.path.join(self.file_path, "empty_" + self.file_name + ".json")):
            FileUtils.remove_file("empty_" + self.file_name + ".json", self.file_path + os.path.sep)

        if os.path.exists(self.file_path + os.path.sep + self.file_name + ".json"):
            FileUtils.remove_file(self.file_name + ".json", self.file_path + os.path.sep)
            os.removedirs(self.file_path + os.path.sep)
        if os.path.exists(self.file_path2):
            os.chmod(self.file_path2, 0o777)
            if os.path.exists(self.file_path2 + self.file_name + ".json"):
                FileUtils.remove_file(self.file_name + ".json", self.file_path2)
            os.removedirs(self.file_path2)


if __name__ == '__main__':
    unittest.main()
