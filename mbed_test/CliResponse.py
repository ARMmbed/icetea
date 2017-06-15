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

import logging
import mbed_clitest.LogManager as LogManager
from mbed_clitest.Searcher import *
from mbed_clitest.TestStepError import TestStepFail

#Command Response
class CliResponse(object):

    # Constructor
    def __init__(self):
        try:
            self.logger = LogManager.get_bench_logger()
        except KeyError:
            self.logger = logging.getLogger("bench")
        self.timeout = False
        self.timedelta = 0
        self.retcode = None
        self.lines = []
        self.traces = []
        self.parsed = False

    #
    def __str__(self):
        return str(self.retcode)

    # check if success response
    def success(self):
        return self.retcode == 0

    # Check if any Fail response
    def fail(self):
        return self.retcode != 0

    #
    def __index__(self, i):
        if self.parsed:
            return self.parsed[i]
        return None

    # verify that response message is expected
    def verifyMessage(self, expectedResponse, breakInFail = True):
        ok = True
        try:
            ok = verifyMessage(self.lines, expectedResponse)
        except Exception as inst:
            ok = False
            if breakInFail:
                raise inst
        if ok == False and breakInFail == True:
                raise LookupError("Unexpected message found")
        return ok

    # verify that there is expected traces
    def verifyTrace(self, expectedTraces, breakInFail = True):
        ok = True
        try:
            ok = verifyMessage(self.traces, expectedTraces)
        except Exception as inst:
            ok = False
            if breakInFail:
                raise inst
        if ok == False and breakInFail:
            raise LookupError("Unexpected message found")
        return ok

    # set response time in seconds
    def set_response_time(self, seconds):
        self.timedelta = seconds

    def verifyResponseDuration(self, expected = None, zero=0, threshold_percent=0, breakInFail = True ):
        '''
        verify that response duration is in bounds
        :param expected: seconds what is expected duration
        :param zero: seconds if one to normalize duration before calculating error rate
        :param threshold_percent: allowed error in percents
        :param breakInFail: boolean, True if raise TestStepFail when out of bounds
        :return:
        '''
        was = self.timedelta - zero
        error = abs(was/expected)*100.0 - 100.0 if expected > 0 else 0
        self.logger.debug("should: %.3f, was: %.3f, error: %.3f %%" % (expected, was, error))
        if abs(error) > threshold_percent:
            msg = "Thread::wait error(%.2f %%) was out of bounds (%.2f %%)" % (error, threshold_percent)
            self.logger.debug(msg)
            if breakInFail:
                raise TestStepFail(msg)
        return (was, expected, error)


    # verify that response time (time span between request-response) is reasonable
    def verifyResponseTime(self, expectedBelow):
        if self.timedelta > expectedBelow:
            raise ValueError("Response time is more (%f) than expected (%f)!" % (self.timedelta, expectedBelow))
