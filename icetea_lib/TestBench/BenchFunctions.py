# pylint: disable=no-member,unused-import
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

BenchFunctions module. Contains functions for the test bench.
"""

import os
import subprocess
import sys
import time

import icetea_lib.LogManager as LogManager
from icetea_lib.Searcher import verify_message


class BenchFunctions(object):
    """
    A collection of functions that add different functionalities to the test bench.
    """
    def __init__(self, resource_configuration, resources, configurations, **kwargs):
        super(BenchFunctions, self).__init__(**kwargs)
        self._resource_configuration = resource_configuration
        self._resources = resources
        self._configurations = configurations
        self._logger = LogManager.get_dummy_logger()

    def init(self, logger=None):
        """
        Set logger.
        """
        if logger:
            self._logger = logger

    # input data from user
    def input_from_user(self, title=None):  # pylint: disable=no-self-use
        """
        Input data from user.

        :param title: Title as string
        :return: stripped data from stdin.
        """
        if title:
            print(title)
        print("Press [ENTER] to continue")
        resp = sys.stdin.readline().strip()
        if resp != '':
            return resp.strip()
        return ""

    def open_node_terminal(self, k='*', wait=True):
        """
        Open Putty (/or kitty if exists)

        :param k: number 1.<max duts> or '*' to open putty to all devices
        :param wait: wait while putty is closed before continue testing
        :return: Nothing
        """
        if k == '*':
            for ind in self._resource_configuration.get_dut_range():
                self.open_node_terminal(ind, wait)
            return

        if not self._resources.is_my_dut_index(k):
            return

        params = '-serial ' + self._resources.duts[k - 1].comport + ' -sercfg ' + str(
            self._resources.duts[k - 1].serialBaudrate)

        putty_exe = self._configurations.env['extApps']['puttyExe']
        if os.path.exists(self._configurations.env['extApps']['kittyExe']):
            putty_exe = self._configurations.env['extApps']['kittyExe']

        if "kitty.exe" in putty_exe:
            params = params + ' -title "' + self._resources.duts[k - 1].comport

            params += ' - ' + self._configurations.test_name
            params += ' | DUT' + str(k) + ' ' + self._resources.get_dut_nick(k) + '"'
            params += ' -log "' + LogManager.get_testcase_logfilename('DUT%d.manual' % k) + '"'

        if os.path.exists(putty_exe):

            command = putty_exe + ' ' + params
            self._logger.info(command)
            if wait:
                if self._resources.is_my_dut_index(k):
                    self._resources.duts[k - 1].close_dut()
                    self._resources.duts[k - 1].close_connection()
                    self._resources.resource_provider.allocator.release(
                        dut=self._resources.duts[k - 1])
                    process = subprocess.Popen(command)
                    time.sleep(2)
                    process.wait()
                    self._resources.duts[k - 1].open_dut()
            else:
                subprocess.Popen(command, close_fds=True)
        else:
            self._logger.warning('putty not exists in path: %s', putty_exe)

    def delay(self, seconds):
        """
        Sleep command.

        :param seconds: Amount of seconds to sleep.
        :return: Nothing
        """
        self._logger.debug("Waiting for %i seconds", seconds)
        if seconds < 30:
            time.sleep(seconds)
        else:
            while seconds > 10:
                self._logger.debug("Still waiting... %i seconds remain", seconds)
                time.sleep(10)
                seconds = seconds - 10
            time.sleep(seconds)

    def verify_trace_skip_fail(self, k, expected_traces):
        """
        Shortcut to set break_in_fail to False in verify_trace.

        :param k: nick or index of dut.
        :param expected_traces: Expected traces as a list or string
        :return: boolean
        """
        return self.verify_trace(k, expected_traces, False)

    def verify_trace(self, k, expected_traces, break_in_fail=True):
        """
        Verify that traces expected_traces are found in dut traces.

        :param k: index or nick of dut whose traces are to be used.
        :param expected_traces: list of expected traces or string
        :param break_in_fail: Boolean, if True raise LookupError if search fails
        :return: boolean.
        :raises: LookupError if search fails.
        """
        if isinstance(k, str):
            dut_index = self._resources.get_dut_index(k)
            return self.verify_trace(dut_index, expected_traces, break_in_fail)

        # If expectedTraces given as a String (expecting only a certain trace), wrap it in a list.
        if isinstance(expected_traces, str):
            expected_traces = [expected_traces]

        status = True
        try:
            status = verify_message(self._resources.duts[k - 1].traces, expected_traces)
        except TypeError as inst:
            status = False
            if break_in_fail:
                raise inst
        if status is False and break_in_fail:
            raise LookupError("{} not found in traces.".format(expected_traces))
        return status

    def get_time(self):  # pylint: disable=no-self-use
        """
        Get timestamp using time.time().

        :return: timestamp
        """
        return time.time()
