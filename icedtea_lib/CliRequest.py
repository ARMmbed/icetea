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

import time

"""
CliRequest module. Contains CliRequest class.
"""
# Disable "too many instance attributes" and "too few public methods" warnings
# pylint: disable=R0902,R0903

# Command Request
class CliRequest(object):
    """
    CliRequest class. This is a command request object, that contains the command,
    creation timestamp and other values related to the command sent to a dut.
    """

    def __init__(self, cmd="", timestamp=time.time(), **kwargs):
        """
        Constuctor.
        :param cmd: Command sent as string
        :param timestamp: timestamp value, default is time.time() called when creating this object.
        :param kwargs: Keyword arguments. Used arguments are: wait, expected_retcode, timeout,
        async and dut_index. These values will populate class members that share the same name.
        expectedRetcode and dutIndex are also accepted for backwards compatibility.
        """

        self.cmd = cmd
        self.wait = True
        self.timeout = 10
        self.async = False
        self.timestamp = timestamp
        self.expected_retcode = 0
        self.response = None
        self.dut_index = -1

        for key in kwargs:
            if key == 'wait':
                self.wait = kwargs[key]
            elif key == 'expectedRetcode' or key == 'expected_retcode':
                self.expected_retcode = kwargs[key]
            elif key == 'timeout':
                self.timeout = kwargs[key]
            elif key == 'async':
                self.async = kwargs[key]
            elif key == 'dutIndex' or key == 'dut_index':
                self.dut_index = kwargs[key]

    def __str__(self):
        return self.cmd

    def get_timedelta(self, now):
        """
        Return time difference to now from the start of this Request.
        :param now: Timestamp to which time difference should be calculated to.
        :return: Result of calculation as integer.
        """
        return now-self.timestamp

    @property
    def dutIndex(self):
        return self.dut_index

    @dutIndex.setter
    def dutIndex(self, value):
        self.dut_index = value

    @property
    def expectedRetcode(self):
        return self.expected_retcode

    @expectedRetcode.setter
    def expectedRetcode(self, value):
        self.expected_retcode = value
