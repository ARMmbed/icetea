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


import inspect
import os

import icetea_lib.tools.file.SessionFiles as files
from icetea_lib.Plugin.PluginBase import PluginBase


class FileApiPlugin(PluginBase):
    """
    Plugin interface for JsonFile plugin.
    """
    def __init__(self):
        super(FileApiPlugin, self).__init__()  # pylint: disable=useless-super-delegation
        self.bench = None

    def init(self, bench=None):
        """
        Init function to store the Bench object reference.

        :param bench: Bench
        :return: Nothing
        :raises AttributeError if bench is None.
        """
        self.bench = bench
        if self.bench is None:
            raise AttributeError("Bench instance not present!")

    def get_bench_api(self):
        """
        Get the descriptor for the plugin interface.

        :return: dict
        """
        return {"JsonFile": self._jsonfileconstructor}

    def _jsonfileconstructor(self, filename=None, filepath=None, logger=None):
        """
        Constructor method for the JsonFile object.

        :param filename: Name of the file
        :param filepath: Path to the file
        :param logger: Optional logger.
        :return: JsonFile
        """
        if filepath:
            path = filepath
        else:
            tc_path = os.path.abspath(os.path.join(inspect.getfile(self.bench.__class__),
                                                   os.pardir))
            path = os.path.abspath(os.path.join(tc_path, os.pardir, "session_data"))
        name = "default_file.json" if not filename else filename
        log = self.bench.logger if not logger else logger
        self.bench.logger.info("Setting json file location to: {}".format(path))
        return files.JsonFile(log, path, name)
