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


class ParserManager(object):
    def __init__(self, logger=None):
        self.parsers = {}
        self.logger = logger
        if self.logger is None:
            # TODO: Add basic stream logger
            pass

    def has_parser(self, parser):
        """
        Returns True if given parser found in managed parsers.

        :param parser: Name of parser to look for
        :return: Boolean
        """
        return True if parser in self.parsers else False

    def add_parser(self, parser_name, parser_func):
        """
        Add new parser function for specific name.

        :param parser_name: Name of parser to add
        :param parser_func: Callable function to call when parsing responses
        :return: Nothing
        """
        self.parsers[parser_name] = parser_func

    # parse response
    def parse(self, *args, **kwargs):
        """
        Parse response.

        :param args: List. 2 first items used as parser name and response to parse
        :param kwargs: dict, not used
        :return: dictionary or return value of called callable from parser.
        """
        #pylint: disable=W0703
        cmd = args[0]
        resp = args[1]
        if cmd in self.parsers:
            try:
                return self.parsers[cmd](resp)
            except Exception as err:
                print(err)
        return {}
