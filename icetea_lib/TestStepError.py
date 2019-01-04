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

import traceback
import sys

from icetea_lib.LogManager import get_bench_logger


class TestStepError(Exception):
    '''
    TestStepError exception is used in case where something
    very fatal unexpected happens in test environment or serial port connection dies.
    '''
    def __init__(self, message="TestStepError"):
        super(TestStepError, self).__init__(message)
        self.logger = None

    # print detailed info
    def detailed_info(self):
        """
        Print detailed exception information from traceback
        """
        _, _, trace = sys.exc_info()
        filename, linenumber, functionname, line = traceback.extract_tb(trace)[-2]
        self.logger = get_bench_logger()
        self.logger.error("Exception details: ")
        self.logger.error("TC Name: " + str(filename))
        self.logger.error("Function name: " + str(functionname))
        self.logger.error("Line number: " + str(linenumber))
        self.logger.error("Line: " + str(line))


class InconclusiveError(Exception):
    """
    Inconclusive error exception, used for showing errors such as
    broken environments and missing requirements.
    """
    pass


class TestStepFail(Exception):
    '''
    TestStepFail exception is used when failure causes because of
    device/software under test, and probably not related to test environment
    '''
    pass


class TestStepTimeout(TestStepFail):
    """
    TestStepTimeout, failure for  showing timeouts.
    """
    pass


class SkippedTestcaseException(Exception):
    """
    Error that indicates that this test case should be skipped for one reason or another.
    """
    pass
