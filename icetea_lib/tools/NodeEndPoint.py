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

NodeEndPoint class. Just a wrapper for a single Dut.
"""


class NodeEndPoint(object):  # pylint: disable=too-few-public-methods
    """
    Wrapper for a dut, contains a shortcut to send commands to this dut specifically.
    """

    def __init__(self, bench, endpoint_id):
        self.bench = bench
        self.endpoint_id = endpoint_id

    def command(self, cmd, expected_retcode=0):  # pylint: disable=invalid-name
        # expected_retcode kwd argument is used in many test cases, we cannot rename it.
        """
        Shortcut for sending a command to this node specifically.
        :param cmd: Command to send
        :param expected_retcode: Expected return code as int, default is 0
        :return: CliResponse
        """
        return self.bench.execute_command(self.endpoint_id, cmd, expected_retcode=expected_retcode)
