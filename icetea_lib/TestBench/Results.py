# pylint: disable=no-member,too-many-instance-attributes
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

Mixer containing helpers for handling Results and ResultLists.
"""

import os
from icetea_lib.ReturnCodes import ReturnCodes
import icetea_lib.LogManager as LogManager
from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList
from icetea_lib.tools.GitTool import get_git_info


# @todo this needs some more work
class Results(object):
    """
    ResultMixer manage test results and verdicts.
    It provide public API get_result() for TestManagement.
    """
    def __init__(self, logger, resources, configuration, args, **kwargs):
        super(Results, self).__init__(**kwargs)
        self._result_list = ResultList()
        self._retcode = ReturnCodes.RETCODE_SUCCESS
        self._failreason = ''
        self._logger = logger
        self._configuration = configuration
        self._args = args
        self._resources = resources

    def init(self, logger=None):
        """
        Initialize the internal ResultList.
        :return: Nothing
        """
        if logger:
            self._logger = logger
        self._result_list = ResultList()

    @staticmethod
    def create_new_result(verdict, retcode, duration, input_data):
        """
        Create a new Result object with data in function arguments.

        :param verdict: Verdict as string
        :param retcode: Return code as int
        :param duration: Duration as time
        :param input_data: Input data as dictionary
        :return: Result
        """
        new_result = Result(input_data)
        new_result.set_verdict(verdict, retcode, duration)
        return new_result

    def add_new_result(self, verdict, retcode, duration, input_data):
        """
        Add a new Result to result object to the internal ResultList.

        :param verdict: Verdict as string
        :param retcode: Return code as int
        :param duration: Duration as time
        :param input_data: Input data as dict
        :return: Result
        """
        new_result = Results.create_new_result(verdict, retcode, duration, input_data)
        self._result_list.append(new_result)
        return new_result

    @property
    def retcode(self):
        """
        Getter for return code.

        :return: int
        """
        return self._retcode

    @retcode.setter
    def retcode(self, value):
        """
        Setter for retcode.

        :param value: int
        :return: Nothing
        """
        self._retcode = value

    def set_failure(self, retcode, reason):
        """
        Set internal state to reflect failure of test.

        :param retcode: return code
        :param reason: failure reason as string
        :return: Nothing
        """
        if self._resources.resource_provider:
            if hasattr(self._resources.resource_provider, "allocator"):
                # Check for backwards compatibility with older pyclient versions.
                if hasattr(self._resources.resource_provider.allocator, "get_status"):
                    pr_reason = self._resources.resource_provider.allocator.get_status()
                    if pr_reason:
                        reason = "{}. Other error: {}".format(pr_reason, reason)
                        retcode = ReturnCodes.RETCODE_FAIL_DUT_CONNECTION_FAIL

        if self.retcode is None or self.retcode == ReturnCodes.RETCODE_SUCCESS:
            self.retcode = retcode
            self._failreason = reason
            self._logger.error("Test Case fails because of: %s", reason)
        else:
            self._logger.info("another fail reasons: %s", reason)

    def get_results(self):
        """
        Getter for internal _results variable.
        """
        return self._result_list

    def get_result(self, tc_file=None):
        """
        Generate a Result object from this test case.

        :param tc_file: Location of test case file
        :return: Result
        """
        self.append_result(tc_file)
        return self._result_list.data[0]

    def set_results(self, value):
        """
        Setter for _result_list.

        :param value: ResultList
        :return: Nothing
        """
        self._result_list = value

    def append_result(self, tc_file=None):
        """
        Append a new fully constructed Result to the internal ResultList.

        :param tc_file: Test case file path
        :return: Nothing
        """
        result = Result()

        result.set_tc_metadata(self._configuration.config)
        tc_rev = get_git_info(self._configuration.get_tc_abspath(tc_file),
                              verbose=self._args.verbose)
        if self._logger:
            self._logger.debug(tc_rev)
        result.set_tc_git_info(tc_rev)
        result.component = self._configuration.get_test_component()
        result.feature = self._configuration.get_features_under_test()
        result.skip_reason = self._configuration.skip_reason() if self._configuration.skip() else ''
        result.fail_reason = self._failreason
        result.logpath = os.path.abspath(LogManager.get_base_dir())
        result.logfiles = LogManager.get_logfiles()
        result.retcode = self.retcode
        result.set_dutinformation(self._resources.dutinformations)
        # pylint: disable=unused-variable
        for platform, serialnumber in zip(self._resources.get_platforms(),
                                          self._resources.get_serialnumbers()):
            #  Zipping done to keep platforms and serial numbers aligned in case some sn:s are
            #  missing
            result.dut_vendor.append('')
            result.dut_resource_id.append(serialnumber)
        result.dut_count = self._resources.get_dut_count()
        result.duts = self._resources.resource_configuration.get_dut_configuration()
        if self._resources.resource_configuration.count_hardware() > 0:
            result.dut_type = 'hw'
        elif self._resources.resource_configuration.count_process() > 0:
            result.dut_type = 'process'
        else:
            result.dut_type = None

        self._result_list.append(result)
