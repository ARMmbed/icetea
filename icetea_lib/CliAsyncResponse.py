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

CliAsyncResponse module, contains CliAsyncResponse class,
which is a proxy for a future CliResponse.

"""

import icetea_lib.LogManager as LogManager


class CliAsyncResponse(object):  # pylint: disable=too-few-public-methods
    """Proxy class to a future CliResponse, a response to an async comand.
       If any function of Cliresponse is called on an instance of this class
       the system will wait and block for the response to become ready.
    """

    def __init__(self, dut):
        try:
            self.logger = LogManager.get_bench_logger()
        except KeyError:
            self.logger = None
        self.response = None
        self.dut = dut

    def set_response(self, response):
        """
        Set the response, this function should not be called directly,
        the DUT will do it when a response is available.
        """
        if self.response is None:
            self.response = response

    def __wait_for_response(self):
        """
        Explicitelly wait and block for the response
        """
        if self.response is None:
            # The response will be filled - anyway - by the DUT,
            # there is no need to set it twice.
            self.dut._wait_for_exec_ready()  # pylint: disable=protected-access

    def __getattr__(self, name):
        """
        Forward calls and attribute lookup to the inner response once it is available
        """
        self.__wait_for_response()
        return getattr(self.response, name)

    def __str__(self):
        """
        Return the string representation of the response once it is available
        """
        self.__wait_for_response()
        return self.response.__str__()

    def __getitem__(self, item):
        """
        Index operator forwarded to the response once it is available
        """
        self.__wait_for_response()
        return self.response.__getitem__(item)
