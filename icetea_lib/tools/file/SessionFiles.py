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

from icetea_lib.tools.file import FileUtils
from icetea_lib.tools.tools import initLogger
# pylint: disable=too-many-arguments


class JsonFile(object):
    """
    JsonFile class, for generating and handling json files.
    """
    def __init__(self, logger=None, filepath=None, filename=None):
        self.logger = logger if logger else initLogger("JsonFile")
        self.filepath = filepath if filepath else os.path.sep
        self.filename = filename if filename else "default_file.json"

    def write_file(self, content, filepath=None, filename=None, indent=None, keys_to_write=None):
        '''
        Write a Python dictionary as JSON to a file.

        :param content: Dictionary of key-value pairs to save to a file
        :param filepath: Path where the file is to be created
        :param filename: Name of the file to be created
        :param indent: You can use this to specify indent level for pretty printing the file
        :param keys_to_write: array of keys that are to be picked from data and written to file.
                Default is None, when all data is written to file.
        :return: Path of file used
        :raises OSError, EnvironmentError, ValueError
        '''
        path = filepath if filepath else self.filepath
        name = filename if filename else self.filename
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as error:
                self.logger.error("Error while creating directory: {}".format(error))
                raise

        name = self._ends_with(name, ".json")
        path = self._ends_with(path, os.path.sep)

        if keys_to_write:
            data_to_write = {}
            for key in keys_to_write:
                data_to_write[key] = content[key]
        else:
            data_to_write = content

        try:
            indent = indent if indent else 2
            self._write_json(path, name, 'w', data_to_write, indent)
            return os.path.join(path, name)
        except EnvironmentError as error:
            self.logger.error("Error while opening or writing to file: {}".format(error))
            raise
        except ValueError:
            raise

    def read_file(self, filepath=None, filename=None):
        """
        Tries to read JSON content from filename and convert it to a dict.

        :param filepath: Path where the file is
        :param filename: File name
        :return: Dictionary read from the file
        :raises EnvironmentError, ValueError
        """
        name = filename if filename else self.filename
        path = filepath if filepath else self.filepath
        name = self._ends_with(name, ".json")
        path = self._ends_with(path, os.path.sep)

        try:
            return self._read_json(path, name)
        except EnvironmentError as error:
            self.logger.error("Error while opening or reading the file: {}".format(error))
            raise
        except ValueError as error:
            self.logger.error("File contents cannot be decoded to JSON: {}".format(error))
            raise

    def read_value(self, key, filepath=None, filename=None):
        """
        Tries to read the value of given key from JSON file filename.

        :param filepath: Path to file
        :param filename: Name of file
        :param key: Key to search for
        :return: Value corresponding to given key
        :raises OSError, EnvironmentError, KeyError
        """
        path = filepath if filepath else self.filepath
        name = filename if filename else self.filename
        name = self._ends_with(name, ".json")
        path = self._ends_with(path, os.path.sep)

        try:
            output = self._read_json(path, name)
            if key not in output:
                raise KeyError("Key '{}' not found in file {}".format(key, filename))
            else:
                return output[key]
        except EnvironmentError as error:
            self.logger.error("Error while opening or reading the file: {}".format(error))
            raise

    def write_values(self, data, filepath=None, filename=None, indent=None, keys_to_write=None):
        """
        Tries to write extra content to a JSON file.

        Creates filename.temp with updated content, removes the old file and
        finally renames the .temp to match the old file.
        This is in effort to preserve the data in case of some weird errors cause problems.

        :param filepath: Path to file
        :param filename: Name of file
        :param data: Data to write as a dictionary
        :param indent: indent level for pretty printing the resulting file
        :param keys_to_write: array of keys that are to be picked from data and written to file.
        Default is None, when all data is written to file.
        :return: Path to file used
        :raises EnvironmentError ValueError
        """

        name = filename if filename else self.filename
        path = filepath if filepath else self.filepath
        name = self._ends_with(name, ".json")
        path = self._ends_with(path, os.path.sep)

        if not os.path.isfile(path + name):
            try:
                return self.write_file(data, path, name, indent, keys_to_write)
            except EnvironmentError as error:
                self.logger.error("Error while opening or writing to file: {}".format(error))
                raise
            except ValueError:
                raise

        if keys_to_write:
            data_to_write = {}
            for key in keys_to_write:
                data_to_write[key] = data[key]
        else:
            data_to_write = data

        try:
            with open(path + name, 'r') as fil:
                output = json.load(fil)
                self.logger.info("Read contents of {}".format(filename))
                for key in data_to_write:
                    try:
                        output[key] = data_to_write[key]
                    except TypeError as error:
                        self.logger.error(
                            "File contents could not be serialized into a dict. {}".format(error))
                        raise
            self._write_json(path, name + ".temp", "w", output, indent)
            FileUtils.remove_file(name, path)
            FileUtils.rename_file(name + '.temp', name, path)
            return os.path.join(path, name)
        except EnvironmentError as error:
            self.logger.error(
                "Error while writing to, opening or reading the file: {}".format(error))
            raise
        except ValueError as error:
            self.logger.error(
                "File could not be decoded to JSON. It might be empty? {}".format(error))
            try:
                self._write_json(path, name, "w", data_to_write, indent)
                return os.path.join(path, name)
            except EnvironmentError:
                raise

    def _write_json(self, filepath, filename, writemode, content, indent):
        """
        Helper for writing content to a file.

        :param filepath: path to file
        :param filename: name of file
        :param writemode: writemode used
        :param content: content to write
        :param indent: value for dump indent parameter.
        :return: Norhing
        """
        with open(os.path.join(filepath, filename), writemode) as fil:
            json.dump(content, fil, indent=indent)
            self.logger.info("Wrote content to file {}".format(filename))

    def _read_json(self, path, name):
        """
        Load a json into a dictionary from a file.

        :param path: path to file
        :param name: name of file
        :return: dict
        """
        with open(os.path.join(path, name), 'r') as fil:
            output = json.load(fil)
            self.logger.info("Read contents of {}".format(name))
            return output

    def _ends_with(self, string_to_edit, end):  # pylint: disable=no-self-use
        """
        Check if string ends with characters in end, if not merge end to string.

        :param string_to_edit: string to check and edit.
        :param end: str
        :return: string_to_edit or string_to_edit + end
        """
        if not string_to_edit.endswith(end):
            return string_to_edit + end
        return string_to_edit
