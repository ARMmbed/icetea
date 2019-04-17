# pylint: disable=too-many-arguments
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

Logger with helpers to enable logging in Bench.
"""

import icetea_lib.LogManager as LogManager


class Logger(object):
    """
    This Mixer provide public logger property for everybody usage.
    """
    def __init__(self, **kwargs):
        super(Logger, self).__init__(**kwargs)
        self.__logger = LogManager.get_dummy_logger()

    def get_logger(self):
        """
        Getter for the logger.

        :return: Logger
        """
        return self.__logger

    def init_logger(self, test_name, verbose, silent, color, disable_log_truncate):
        """
        This function is called from Bench right after test is started.
        """
        LogManager.init_testcase_logging(test_name, verbose,
                                         silent, color,
                                         not disable_log_truncate)
        self.__logger = LogManager.get_bench_logger()

    def set_logger(self, value):
        """
        Setter for logger.
        """
        self.__logger = value
