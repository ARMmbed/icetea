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

from icetea_lib.bench import Bench

'''
Icetea test case command and response public API usage example. For details, please check 
doc/tc_api.md

function:
    self.command(k, cmd, wait = True, expectedRetcode = 0, timeout=50, async=False, reportCmdFail=True)
        """
        :param: k: Value: 1. DUT Index or DUT nick will send command to a DUT
                          2. '*' -send command to all DUTs

        :param: cmd: Command to be sent to DUT.

        :param: wait: True/False. For special cases when retcode is not wanted to wait.

        :param: expectedRetcode: 0 by default. Can be None

        :param: timeout: Command timeout in seconds.

        :param: async: for details usage, please see testcase_example_usage/sample_async.py

        :param: reportCmdFail: If True (default), exception is thrown on command execution error.

        :return: CliResponse object
        """

Object: CliResponse
    functions:
        1. success(): return True, if command retcode is 0, otherwise False.

        2. fail(): return True, if command retcode is NOT 0, otherwise False.

        3. verifyTrace(expectedTraces, breakInFail=True): search for expected traces

        4. verifyMessage(expectedResponse, breakInFail=True): search for expected messages

        5. verifyResponseDuration(expected=None, zero=0, threshold_percent=0, breakInFail=True):
            Verifies that response duration is in bounds

        6. verifyResponseTime(expectedBelow): Verifies that response time was below expected threshold.
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_command_response",
                       title="Icetea command and response APIs example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of Icetea command and response APIs",
                       component=["Icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 2, # devices number
                                    "type": "hardware",  # "hardware" (by default) or "process"
                                    "application": {
                                        "bin": "build_path/build_full_name",  # build binary path
                                    }
                                },
                                "1": {
                                    "nick": "dut1" # give dut a nick
                                },
                                "2": {
                                    "nick": "dut2"
                                }
                            }
                        }
                       )

    def case(self):
        # send command "echo hello" to 1st dut by index
        self.command(1, "echo hello")

        # send command "echo hello" to 2nd dut by nick
        self.command("dut2", "echo hello")

        # send command "echo hello" to all duts by '*'
        self.command("*", "echo hello")

        # send know command "echo hello" and retcode expected to be 0 --> success() is True
        response = self.command(1, "echo hello", expectedRetcode=0)
        self.assertTrue(response.success())

        # send unknown command "hello" and the retcode for unknown command is -5 --> fail() is True
        response = self.command(1, "hello", expectedRetcode=-5)
        self.assertTrue(response.fail())

        # get response and verify traces
        response = self.command(2, "echo world")
        response.verify_trace("world")

        # send command to all duts by '*'
        responses = self.command('*', "echo hello world! ")
        # the 'responses' will be a list of all the returned response
        for response in responses:
            response.verify_message("hello world!")
            response.verify_response_time(1)
