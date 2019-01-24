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

Argument handling mixer for Bench.
"""

from icetea_lib.arguments import get_base_arguments
from icetea_lib.arguments import get_parser
from icetea_lib.arguments import get_tc_arguments


class ArgsHandler(object):
    """
    This mixer get and parses cli arguments
    It brings two API's:
    args -getter and setter
    """
    def __init__(self, **kwargs):
        super(ArgsHandler, self).__init__(**kwargs)
        parser = get_tc_arguments(get_base_arguments(get_parser()))
        self.__args, self.__unknown = parser.parse_known_args()

    @property
    def args(self):
        """
        Property for arguments.

        :return: arguments
        """
        return self.__args

    @args.setter
    def args(self, value):
        """
        Setter for arguments.

        :param value: arguments
        :return: Nothing
        """
        self.__args = value

    @property
    def unknown(self):
        """
        Getter for unknown arguments.
        """
        return self.__unknown

    @unknown.setter
    def unknown(self, value):
        """
        Setter for the unknown variable.
        """
        self.__unknown = value
