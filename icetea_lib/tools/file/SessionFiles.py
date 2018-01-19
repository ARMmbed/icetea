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
import logging
import os

from icetea_lib.tools.file import FileUtils


def initLogger(name):
    '''
    Initializes a basic logger. Can be replaced when constructing the
    HttpApi object or afterwards with setter
    '''
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    #Skip attaching StreamHandler if one is already attached to logger
    if not getattr(logger, "streamhandler_set", None):
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
        logger.streamhandler_set = True
    return logger


class JsonFile(object):
    def __init__(self, logger = None, filepath=None, filename=None):
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
            except OSError as e:
                self.logger.error("Error while creating directory: {}".format(e))
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
            self._write_json(path, name, 'w', data_to_write, 2)
            return os.path.join(path, name)
        except EnvironmentError as e:
            self.logger.error("Error while opening or writing to file: {}".format(e))
            raise
        except ValueError as e:
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
        except EnvironmentError as e:
            self.logger.error("Error while opening or reading the file: {}".format(e))
            raise
        except ValueError as e:
            self.logger.error("File contents cannot be decoded to JSON: {}".format(e))
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
        except EnvironmentError as e:
            self.logger.error("Error while opening or reading the file: {}".format(e))
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
            except EnvironmentError as e:
                self.logger.error("Error while opening or writing to file: {}".format(e))
                raise
            except ValueError as e:
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
                    except TypeError as e:
                        self.logger.error("File contents could not be serialized into a dict. {}".format(e))
                        raise
            self._write_json(path, name + ".temp", "w", output, indent)
            FileUtils.remove_file(name, path)
            FileUtils.rename_file(name + '.temp', name, path)
            return os.path.join(path, name)
        except EnvironmentError as e:
            self.logger.error("Error while writing to, opening or reading the file: {}".format(e))
            raise
        except ValueError as e:
            self.logger.error("File could not be decoded to JSON. It might be empty? {}".format(e))
            try:
                self._write_json(path, name, "w", data_to_write, indent)
                return os.path.join(path, name)
            except EnvironmentError:
                raise

    def _write_json(self, filepath, filename, writemode, content, indent):
        with open(os.path.join(filepath, filename), writemode) as fil:
            json.dump(content, fil, indent=indent)
            self.logger.info("Wrote content to file {}".format(filename))

    def _read_json(self, path, name):
        with open(os.path.join(path, name), 'r') as fil:
            output = json.load(fil)
            self.logger.info("Read contents of {}".format(name))
            return output

    def _ends_with(self, string, end):
        if not string.endswith(end):
            return string + end
        else:
            return string
