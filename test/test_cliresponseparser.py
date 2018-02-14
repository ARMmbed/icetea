# pylint: disable=missing-docstring

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
import sys
import logging

from icetea_lib.CliResponse import CliResponse
from icetea_lib.CliResponseParser import ParserManager
from icetea_lib.Plugin.plugins.default_parsers import DefaultParsers

sys.path.append('.')


class TestVerify(unittest.TestCase):

    def setUp(self):
        plugin = DefaultParsers()
        parsers = plugin.get_parsers()
        self.parsermanager = ParserManager(logging.getLogger())
        for parser in parsers:
            self.parsermanager.add_parser(parser, parsers[parser])

    def _create_line_response_parser(self, command, path):
        output = open(path, 'r').read()
        response = CliResponse()
        for line in output.splitlines():
            response.lines.append(line)
        parser = self.parsermanager
        resp = parser.parse(command, response)
        return resp


if __name__ == '__main__':
    unittest.main()
