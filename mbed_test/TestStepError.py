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

import traceback
import sys
import LogManager

class TestStepError(Exception):
    '''
    TestStepError exception is used in case where something
    very fatal unexpected happens in test environment,
    like serial port connection dies.
    '''
    def __init__(self, message):
        self.__message = message

    # get failure reason
    def __str__(self):
        return self.__message

    # print detailed info
    def detailedInfo(self):
        _, _, tb = sys.exc_info()
        filename, linenumber, functionname, line = traceback.extract_tb(tb)[-2]
        self.logger = LogManager.get_bench_logger()
        self.logger.error("Exception details: ")
        self.logger.error("TC Name: " + str(filename))
        self.logger.error("Line number: " + str(linenumber))
        self.logger.error("Line: " + str(line))

class TestStepFail(Exception):
    '''
    TestStepFail exception is used when failure causes because of
    device/software under test, and probably not related to test environment
    '''
    def __init__(self, message):
        self.__message = message

    # get failure reason
    def __str__(self):
        return self.__message

class TestStepTimeout(TestStepFail):
    pass
