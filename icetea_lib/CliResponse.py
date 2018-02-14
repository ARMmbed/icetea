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

CliResponse module. Contains CliResponse class, which is the object returned by the command API.
"""


import logging

import icetea_lib.LogManager as LogManager
from icetea_lib.Searcher import verify_message
from icetea_lib.TestStepError import TestStepFail


# Disable "value x is unsubscriptable"
# pylint: disable=E1136


# Command Response
class CliResponse(object):
    """
    CliResponse class. Object returned by the command api when a command has finished.
    """

    # pylint:disable=invalid-name
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
        self.parsed = None

    def __str__(self):
        return str(self.retcode)

    def success(self):
        """
        Check if this is a response to a successful command
        :return: True or False
        """
        return self.retcode == 0

    def fail(self):
        """
        Check if this is a response to a failed command
        :return: True or False
        """
        return self.retcode != 0

    # verify that response message is expected
    def verify_message(self, expected_response, break_in_fail=True):
        """
        Verifies that expected_response is found in self.lines.

        :param expected_response: response or responses to look for. Must be list or str.
        :param break_in_fail: If set to True,
        re-raises exceptions caught or if message was not found
        :return: True or False
        :raises: LookupError if message was not found and break_in_fail was True. Other exceptions
        might also be raised through searcher.verify_message.
        """
        ok = True
        try:
            ok = verify_message(self.lines, expected_response)
        except (TypeError, LookupError) as inst:
            ok = False
            if break_in_fail:
                raise inst
        if ok is False and break_in_fail:
            raise LookupError("Unexpected message found")
        return ok

    def verify_trace(self, expected_traces, break_in_fail=True):
        """
        Verifies that expectedResponse is found in self.traces

        :param expected_traces: response or responses to look for. Must be list or str.
        :param break_in_fail: If set to True, re-raises exceptions caught or if message was
        not found
        :return: True or False
        :raises: LookupError if message was not found and breakInFail was True. Other Exceptions
        might also be raised through searcher.verify_message.
        """
        ok = True
        try:
            ok = verify_message(self.traces, expected_traces)
        except (TypeError, LookupError) as inst:
            ok = False
            if break_in_fail:
                raise inst
        if ok is False and break_in_fail:
            raise LookupError("Unexpected message found")
        return ok

    def set_response_time(self, seconds):
        """
        Set response time in seconds.

        :param seconds: integer
        :return: Nothing
        """
        self.timedelta = seconds

    def verify_response_duration(self, expected=None, zero=0, threshold_percent=0,
                                 break_in_fail=True):
        """
        Verify that response duration is in bounds.

        :param expected: seconds what is expected duration
        :param zero: seconds if one to normalize duration before calculating error rate
        :param threshold_percent: allowed error in percents
        :param break_in_fail: boolean, True if raise TestStepFail when out of bounds
        :return: (duration, expected duration, error)
        """
        was = self.timedelta - zero
        error = abs(was/expected)*100.0 - 100.0 if expected > 0 else 0
        msg = "should: %.3f, was: %.3f, error: %.3f %%" % (expected, was, error)
        self.logger.debug(msg)
        if abs(error) > threshold_percent:
            msg = "Thread::wait error(%.2f %%) was out of bounds (%.2f %%)" \
                  % (error, threshold_percent)
            self.logger.debug(msg)
            if break_in_fail:
                raise TestStepFail(msg)
        return was, expected, error

    def verify_response_time(self, expected_below):
        """
        Verify that response time (time span between request-response) is reasonable.

        :param expected_below: integer
        :return: Nothing
        :raises: ValueError if timedelta > expected time
        """
        if self.timedelta > expected_below:
            raise ValueError("Response time is more (%f) than expected (%f)!"
                             % (self.timedelta, expected_below))
