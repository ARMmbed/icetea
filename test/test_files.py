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
import time
import unittest
import uuid
import sys

import jsonmerge
import icedtea_lib.tools.file.FileUtils as FileUtils
import mock

from icedtea_lib.tools.file.SessionFiles import JsonFile


class FileTestCase(unittest.TestCase):

    def setUp(self):
        self.fileName = "test_file"
        self.filePath = os.path.join("path", "to", "right")
        self.filePath2 = os.path.join("path", "of", "no", "rights") + os.path.sep
        self.nonExistingFile = "NoFile"
        self.testJson = {"test1": "value1", "test2": "value2", "test3": "value3", "test4": "test5"}
        self.testJson2 = {"Test": "Value", "Test1": "Value1", "Test2": "Value2"}
        self.testToken = {"token": "XXXXXXXXXXX", "life_time": 12, "creation_time": 1, "user_role": "test"}
        self.jsonfile = JsonFile()


    '''
        FileUtils tests here
    '''
    @mock.patch("icedtea_lib.tools.file.FileUtils.os.chdir")
    @mock.patch("icedtea_lib.tools.file.FileUtils.os.remove")
    def test_remove_file(self, mock_rm, mock_chdir):
        mock_chdir.side_effect = iter([OSError, 1, 1, 1, 1])
        mock_rm.side_effect = iter([OSError, 1])
        path_nowhere=os.path.join("testPath", "to", "nowhere")
        path_somewhere=os.path.join("testPath", "to", "somewhere")
        with self.assertRaises(OSError):
            FileUtils.removeFile("testName", path_nowhere)
        with self.assertRaises(OSError):
            FileUtils.removeFile("testName", path_nowhere)
        self.assertTrue(FileUtils.removeFile("testName", path_somewhere))


    @mock.patch("icedtea_lib.tools.file.FileUtils.os.chdir")
    @mock.patch("icedtea_lib.tools.file.FileUtils.os.rename")
    def test_rename_file(self, mock_rn, mock_chdir):
        mock_chdir.side_effect = iter([OSError, 1, 1, 1, 1])
        mock_rn.side_effect = iter([OSError, 1])
        path_nowhere=os.path.join("testPath", "to", "nowhere")
        path_somewhere=os.path.join("testPath", "to", "somewhere")
        with self.assertRaises(OSError):
            FileUtils.renameFile("testName", "new_testName", path_nowhere)
        with self.assertRaises(OSError):
            FileUtils.renameFile("testName", "new_testName", path_nowhere)
        self.assertTrue(FileUtils.renameFile("testName", "new_testName", path_somewhere))

    '''
        JsonFile tests start here
    '''

    def test_writing_file(self):
        # run test for saving a json to a new file. File path should not exists so it is created.
        self.jsonfile.write_file(self.testJson, self.filePath, self.fileName, 2)
        self.assertTrue(os.path.exists(self.filePath + os.path.sep + self.fileName + ".json"))
        with open(self.filePath + os.path.sep + self.fileName + ".json", 'r') as f:
            self.assertDictEqual(json.load(f), self.testJson)

        # save a json to an old file to overwrite entire file
        self.jsonfile.write_file(self.testJson2, self.filePath, self.fileName, 2)
        with open(self.filePath + os.path.sep + self.fileName + ".json", 'r') as f:
            self.assertDictEqual(json.load(f), self.testJson2)

    @unittest.skipIf(sys.platform=='win32', "os.chmod with 0o444 or stat.S_IREAD doesn't work")
    def test_writing_file_fail_windows(self):
        # run test to save json to a file with an invalid path
        os.makedirs(self.filePath2, 0o777)
        os.chmod(self.filePath2, 0o444)
        with self.assertRaises(IOError):
            self.jsonfile.write_file(self.testJson, self.filePath2, self.fileName, 2)

    def test_writing_with_filter(self):
        self.jsonfile.write_file(self.testJson, self.filePath, self.fileName, 2, keys_to_write=["test1", "test2"])
        ref = {"test1": self.testJson["test1"], "test2": self.testJson["test2"]}
        with open(self.filePath + os.path.sep + self.fileName + ".json", 'r') as f:
            self.assertDictEqual(json.load(f), ref)

        self.jsonfile.write_file(self.testJson, self.filePath, self.fileName, 2)
        self.jsonfile.write_values(self.testJson2, self.filePath, self.fileName, 2, keys_to_write=["Test"])
        with open(self.filePath + os.path.sep + self.fileName + ".json", 'r') as f:
            self.assertDictEqual(jsonmerge.merge(self.testJson, {"Test": self.testJson2["Test"]}), json.load(f))

        #ToDo: write malformed data

    @mock.patch("icedtea_lib.tools.file.SessionFiles.JsonFile._write_json")
    @mock.patch("icedtea_lib.tools.file.SessionFiles.os.path.exists")
    @mock.patch("icedtea_lib.tools.file.SessionFiles.os.makedirs")
    def test_write_file_errors(self, mock_mkdir, mock_exists, mock_json):
        mock_mkdir.side_effect = iter([OSError])
        mock_exists.side_effect = iter([False, True, True])
        mock_json.side_effect = iter([EnvironmentError, ValueError])
        with self.assertRaises(OSError):
            self.jsonfile.write_file(self.testJson, self.filePath, self.fileName)
        with self.assertRaises(EnvironmentError):
            self.jsonfile.write_file(self.testJson, self.filePath, self.fileName)
        with self.assertRaises(ValueError):
            self.jsonfile.write_file(self.testJson, self.filePath, self.fileName)

    def test_reading_file(self):
        #Write test data
        self.jsonfile.write_file(self.testJson, self.filePath, self.fileName, 2)
        # read json from nonexisting file
        with self.assertRaises(IOError):
            self.jsonfile.read_file(self.filePath, self.nonExistingFile)

        # read json from existing file
        data = self.jsonfile.read_file(self.filePath, self.fileName)
        self.assertDictEqual(data, self.testJson)
        #ToDo: read from malformed file

    def test_writing_values(self):
        #Test writing to a malformed file.
        self.jsonfile.write_file("", self.filePath, "malformed_" + self.fileName)
        with self.assertRaises(TypeError):
            self.jsonfile.write_values(self.testJson, self.filePath, "malformed_" + self.fileName)

        cwd = os.getcwd()
        os.chdir(self.filePath)
        open("empty_" + self.fileName + ".json", "w")
        os.chdir(cwd)
        self.assertEquals(self.jsonfile.write_values(self.testJson, self.filePath, "empty_" + self.fileName), os.path.join(self.filePath, "empty_" + self.fileName + ".json"))

        # save a json to a new file with write_values instead of write_file
        self.assertEqual(self.jsonfile.write_values(self.testJson, self.filePath, self.fileName, 2), self.filePath + os.path.sep + self.fileName + ".json")

        # save a json to an old file to append to existing data
        self.jsonfile.write_file(self.testJson, self.filePath, self.fileName, 2)
        self.jsonfile.write_values(self.testJson2, self.filePath, self.fileName, 2)
        with open(self.filePath + os.path.sep + self.fileName + ".json", 'r') as f:
            self.assertDictEqual(jsonmerge.merge(self.testJson, self.testJson2), json.load(f))

    @unittest.skipIf(sys.platform=='win32', "os.chmod with 0o444 or stat.S_IREAD doesn't work")
    def test_writing_value_fail_windows(self):
        #Try adding content to a file with no write permissions
        os.makedirs(self.filePath2, 0o777)
        self.jsonfile.write_file(self.testJson2, self.filePath2, self.fileName, 2)
        os.chmod(self.filePath2, 0o444)
        with self.assertRaises(IOError):
            self.jsonfile.write_values(self.testJson, self.filePath2, self.fileName, 2)

    def test_reading_values(self):
        # Test writing to a malformed file.
        self.jsonfile.write_file("", self.filePath, "malformed_" + self.fileName)
        with self.assertRaises(KeyError):
            self.jsonfile.read_value("test1", self.filePath, "malformed_" + self.fileName)

        # read json from nonexisting file
        with self.assertRaises(IOError):
            self.jsonfile.read_value("Test1", self.filePath, self.fileName)

        #Create test data for reading
        self.jsonfile.write_file(self.testJson, self.filePath, self.fileName, 2)
        # read json from existing file

        self.assertEqual("value1", self.jsonfile.read_value("test1", self.filePath, self.fileName))

        # try to read nonexisting key
        with self.assertRaises(KeyError):
            self.jsonfile.read_value("value1", self.filePath, self.fileName)

    def tearDown(self):
        # Do tearDown stuff.
        if os.path.exists(os.path.join(self.filePath, "malformed_" + self.fileName + ".json")):
            FileUtils.removeFile("malformed_" + self.fileName + ".json", self.filePath + os.path.sep)

        if os.path.exists(os.path.join(self.filePath, "empty_" + self.fileName + ".json")):
            FileUtils.removeFile("empty_" + self.fileName + ".json", self.filePath + os.path.sep)

        if os.path.exists(self.filePath + os.path.sep + self.fileName + ".json"):
            FileUtils.removeFile(self.fileName +".json", self.filePath + os.path.sep)
            os.removedirs(self.filePath + os.path.sep)
        if os.path.exists(self.filePath2):
            os.chmod(self.filePath2, 0o777)
            if os.path.exists(self.filePath2 + self.fileName + ".json"):
                FileUtils.removeFile(self.fileName + ".json", self.filePath2)
            os.removedirs(self.filePath2)


if __name__ == '__main__':
    unittest.main()
