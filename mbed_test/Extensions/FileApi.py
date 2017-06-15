"""
Copyright 2016 ARM Limited

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

import mbed_clitest.Extensions.file.SessionFiles as files
import os
import inspect

class FileApi():
    def __init__(self, bench):
        self.bench = bench
        self.logger = bench.logger
        #Direct access to JSON files
        setattr(self.bench, 'JsonFile', self.jsonFileConstructor)


    def jsonFileConstructor(self, filename=None, filepath=None, logger=None):
        if filepath:
            path = filepath
        else:
            tc_path = os.path.abspath(os.path.join(inspect.getfile(self.bench.__class__), os.pardir))
            path = os.path.abspath(os.path.join(tc_path, os.pardir, "session_data"))
        name = "default_file.json" if not filename else filename
        log = self.logger if not logger else logger
        self.logger.info("Setting json file location to: {}".format(path))
        return files.JsonFile(log, path, name)

