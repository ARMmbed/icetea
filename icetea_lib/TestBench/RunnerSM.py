# pylint: disable=no-member,attribute-defined-outside-init,too-many-statements
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

Runner state machine for running tests.
Uses pytransitions/transitions module that implements the state machine.
"""


from transitions import Machine

import icetea_lib.LogManager as LogManager
from icetea_lib.tools.tools import test_methods
from icetea_lib.ReturnCodes import ReturnCodes
from icetea_lib.TestStepError import TestStepError, TestStepFail, TestStepTimeout
from icetea_lib.TestStepError import InconclusiveError, SkippedTestcaseException
from icetea_lib.ResourceProvider.exceptions import ResourceInitError
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError


class RunnerSM(object):
    """
    State machine class.
    States defined in STATES constant and transitions in TRANSITIONS constant
    """

    INITIAL_STATE = "initial"
    SETUP_STATE = "setup"
    SETUP_TEST_STATE = "setup_test"
    EXECUTING_STATE = "executing"
    TD_TEST_STATE = "teardown_test"
    TEARDOWN_STATE = "teardown"
    FINISHED_STATE = "finished"

    STATES = [
        INITIAL_STATE,
        {"name": SETUP_STATE, "on_enter": "_setup_bench"},
        {"name": SETUP_TEST_STATE, "on_enter": "setup"},
        {"name": EXECUTING_STATE, "on_enter": "_run_cases"},
        {"name": TD_TEST_STATE, "on_enter": "teardown"},
        {"name": TEARDOWN_STATE, "on_enter": "_teardown_bench"},
        {"name": FINISHED_STATE, "on_enter": "_finish"}
    ]
    TRANSITIONS = [
        {"trigger": "start", "source": INITIAL_STATE, "dest": SETUP_STATE},
        {"trigger": "setup_to_setup_test", "source": SETUP_STATE, "dest": SETUP_TEST_STATE},
        {"trigger": "setup_test_to_executing", "source": SETUP_TEST_STATE, "dest": EXECUTING_STATE},
        {"trigger": "executing_to_teardown_test", "source": EXECUTING_STATE, "dest": TD_TEST_STATE},
        {"trigger": "teardown_test_to_teardown", "source": TD_TEST_STATE, "dest": TEARDOWN_STATE},
        {"trigger": "finish",
         "source": [SETUP_STATE, SETUP_TEST_STATE, TEARDOWN_STATE], "dest": FINISHED_STATE},
        {"trigger": "jump_to_teardown",
         "source": [SETUP_STATE, SETUP_TEST_STATE, EXECUTING_STATE, TD_TEST_STATE],
         "dest": TEARDOWN_STATE},
        {"trigger": "jump_to_teardown_test",
         "source": [SETUP_TEST_STATE, EXECUTING_STATE], "dest": TD_TEST_STATE}
    ]

    EXCEPTIONS = (
        EnvironmentError,
        AllocationError,
        TestStepError,
        ResourceInitError,
        TestStepTimeout,
        TestStepFail,
        InconclusiveError,
        SkippedTestcaseException,
        KeyboardInterrupt,
        NameError,
        LookupError,
        ValueError,
        Exception
    )

    def __init__(self, benchapi, logger=None, **kwargs):
        super(RunnerSM, self).__init__(**kwargs)
        self.machine = None
        self.logger = logger if logger else LogManager.get_dummy_logger()
        self._benchapi = benchapi

    def setup(self):
        """
        Alias for test case setup method.
        """
        if hasattr(self._benchapi, "setup"):
            if self._benchapi.args.skip_setup:
                self.logger.info("Skipping setup")
                return True
            return self._benchapi.setup()
        return True

    def teardown(self):
        """
        Alias for test case teardown method.
        """
        if hasattr(self._benchapi, "teardown"):
            if self._benchapi.args.skip_teardown:
                self.logger.info("Skipping teardown")
                return True
            return self._benchapi.teardown()
        return True

    def _run_cases(self):
        """
        Run test case functions.

        :return: Nothing
        """
        if not self._benchapi.args.skip_case:
            tests = test_methods(self._benchapi)
            for test in tests:
                getattr(self._benchapi, test)()
        else:
            self.logger.info("Skipping case-functions.")

    def check_skip(self):
        """
        Check if we need to skip this tc.

        :return: ReturnCodes.RETCODE_SKIP or None
        """
        skip = self._benchapi.check_skip()
        if skip:
            self.logger.info("TC '%s' will be skipped because of '%s'", self._benchapi.test_name,
                             (self._benchapi.skip_reason()))
            result = self._benchapi.get_result()
            result.set_verdict(verdict='skip', retcode=-1, duration=0)
            self._benchapi.set_failure(ReturnCodes.RETCODE_SKIP, self._benchapi.skip_reason())
            return ReturnCodes.RETCODE_SKIP
        return None

    def _setup_bench(self):
        """
        Initialize test bench. Validate dut configurations, kill putty and kitty processes,
        load plugins, create empty Result object for this test case, initialize duts,
        collect metainformation from initialized duts, start sniffer, start test case timer,
        start external services and finally send pre-commands to duts.
        :return: Nothing
        """
        self._benchapi.load_plugins()
        if self._benchapi.args.kill_putty:
            self.logger.debug("Kill putty/kitty processes")
            self._benchapi.kill_process(['kitty.exe', 'putty.exe'])
        self._benchapi.init_duts()
        self._benchapi.start_external_services()
        self._benchapi.send_pre_commands(self._benchapi.args.pre_cmds)

    def _teardown_bench(self):
        """
        Tear down the Bench object.
        :return: Nothing
        """
        # pylint: disable=broad-except
        try:
            self._benchapi.send_post_commands(self._benchapi.args.post_cmds)
        except Exception as error:
            self.logger.error(error)
        try:
            self._benchapi.duts_release()
        except Exception as error:
            self.logger.error(error)
        try:
            self._benchapi.clear_sniffer()
        except Exception as error:
            self.logger.error(error)
        try:
            self._benchapi.stop_external_services()
        except Exception as error:
            self.logger.error(error)

    def _call_exception(self, method, error, retcode, message=None):
        """
        Handle error situation. Makes sure that the test case proceeds to the correct step from
        the step where it failed.

        :param method: Method where fail happened
        :param error: Exception
        :param retcode: int
        :param message: Message to log
        :return: Nothing
        """
        if not self.retcode and retcode:
            self.__retcode = retcode

        message = message if message else str(error)
        self._benchapi.set_failure(retcode, message)
        self.logger.error("%s failed: %s" % (method, message))

        if method in ["setup_bench", "teardown_test"]:
            self.logger.info("------TEST BENCH TEARDOWN STARTS---------")
            try:
                self.jump_to_teardown()
            except self.EXCEPTIONS:
                self.logger.exception("Exception in test bench teardown!")
            self.logger.info("------TEST BENCH TEARDOWN ENDS---------")
        elif method in ["setup", "case"]:
            if (error.__class__ == TestStepFail and method == "setup") or method == "case":
                self.logger.info("------TC TEARDOWN STARTS---------")
                try:
                    self.jump_to_teardown_test()
                except self.EXCEPTIONS:
                    self.logger.exception("Exception in test case teardown!")
                self.logger.info("------TC TEARDOWN ENDS---------")
            self.logger.info("------TEST BENCH TEARDOWN STARTS---------")
            try:
                self.jump_to_teardown()
            except self.EXCEPTIONS:
                self.logger.exception("Exception in test bench teardown!")
            self.logger.info("------TEST BENCH TEARDOWN ENDS---------")
        if self.state != "finished":
            self.finish()

    def _finish(self):
        """
        Finish step.

        :return: Nothing
        """
        self.logger.info("Test case finished.")

    def run(self):  # pylint: disable=too-many-return-statements
        """
        Run through the state machine states, triggering states in the correct order for correct
        operation. Fail states are triggered through method 'failure'.

        :return: int
        """
        self.machine = Machine(self, states=self.STATES, transitions=self.TRANSITIONS,
                               initial="initial")
        self.retcode = ReturnCodes.RETCODE_SUCCESS
        try:
            # Move from initial to setup
            self.logger.info("------TEST BENCH SETUP STARTS---------")
            self.start()
        except self.EXCEPTIONS as error:
            returncode, message = self._select_error_returncode(self.SETUP_STATE, error)
            self.logger.info("------TEST BENCH SETUP ENDS---------")
            self.failure(error, "setup_bench", returncode, message)

        if self.state == self.FINISHED_STATE:
            return self.retcode
        self.logger.info("------TEST BENCH SETUP ENDS---------")

        try:
            # Move from setup to setup_test
            self.logger.info("------TC SETUP STARTS---------")
            self.setup_to_setup_test()
        except self.EXCEPTIONS as error:
            returncode, message = self._select_error_returncode(self.SETUP_TEST_STATE, error)
            self.logger.info("------TC SETUP ENDS---------")
            self.failure(error, "setup", returncode, message)

        if self.state == self.FINISHED_STATE:
            return self.retcode
        self.logger.info("------TC SETUP ENDS---------")

        try:
            # Move from setup_test to executing
            self.logger.info("------TEST CASE STARTS---------")
            self.setup_test_to_executing()
        except self.EXCEPTIONS as error:
            self.logger.error(error)
            returncode, message = self._select_error_returncode(self.EXECUTING_STATE, error)
            self.logger.info("-----------TEST CASE ENDS-----------")
            self.failure(error, "case", returncode, message)

        if self.state == self.FINISHED_STATE:
            return self.retcode
        self.logger.info("-----------TEST CASE ENDS-----------")

        try:
            # Move from executing to teardown_test
            self.logger.info("------TC TEARDOWN STARTS---------")
            self.executing_to_teardown_test()
        except self.EXCEPTIONS as error:
            returncode, message = self._select_error_returncode(self.TD_TEST_STATE, error)
            self.logger.info("------TC TEARDOWN ENDS---------")
            self.failure(error, "teardown_test", returncode, message)

        if self.state == self.FINISHED_STATE:
            return self.retcode
        self.logger.info("------TC TEARDOWN ENDS---------")

        try:
            # Move from teardown_test to teardown
            self.logger.info("------TEST BENCH TEARDOWN STARTS---------")
            self.teardown_test_to_teardown()
        except self.EXCEPTIONS as error:
            returncode, message = self._select_error_returncode(self.TEARDOWN_STATE, error)
            self.logger.info("------TEST BENCH TEARDOWN ENDS---------")
            self.failure(error, "teardown_bench", returncode, message)

        if self.state == self.FINISHED_STATE:
            return self.retcode
        self.logger.info("------TEST BENCH TEARDOWN ENDS---------")

        try:
            # Move from teardown to finished
            self.finish()
        except self.EXCEPTIONS as error:
            returncode, message = self._select_error_returncode(self.FINISHED_STATE, error)
            self.failure(error, "finish", returncode, message)
        if self.state == self.FINISHED_STATE:
            return self.retcode
        return self.retcode

    def _select_error_returncode(self, state, error):
        """
        Matrix for selecting return codes and messages for different fail states.

        :param state: State where fail happened
        :param error: Exception that happened.
        :return: (return_code, message)
        """
        retcode_matrix = {
            "setup": {
                EnvironmentError: ReturnCodes.RETCODE_FAIL_SETUP_BENCH,
                ResourceInitError: ReturnCodes.RETCODE_FAIL_SETUP_BENCH,
                SkippedTestcaseException: ReturnCodes.RETCODE_SKIP,
                KeyboardInterrupt: {"retcode": ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER,
                                    "message": "Aborted by user"},
                Exception: ReturnCodes.RETCODE_FAIL_SETUP_BENCH,

            },
            "setup_test": {
                TestStepTimeout: ReturnCodes.RETCODE_FAIL_SETUP_TC,
                TestStepFail: ReturnCodes.RETCODE_FAIL_SETUP_TC,
                TestStepError: ReturnCodes.RETCODE_FAIL_SETUP_TC,
                InconclusiveError: ReturnCodes.RETCODE_FAIL_INCONCLUSIVE,
                SkippedTestcaseException: ReturnCodes.RETCODE_SKIP,
                KeyboardInterrupt: {"retcode": ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER,
                                    "message": "Aborted by user"},
                Exception: ReturnCodes.RETCODE_FAIL_SETUP_TC
            },
            "executing": {
                TestStepTimeout: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION,
                TestStepFail: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION,
                TestStepError: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION,
                InconclusiveError: ReturnCodes.RETCODE_FAIL_INCONCLUSIVE,
                SkippedTestcaseException: ReturnCodes.RETCODE_SKIP,
                NameError: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION,
                LookupError: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION,
                ValueError: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION,
                KeyboardInterrupt: {"retcode": ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER,
                                    "message": "Aborted by user"},
                Exception: ReturnCodes.RETCODE_FAIL_TC_EXCEPTION
            },
            "teardown_test": {
                TestStepTimeout: ReturnCodes.RETCODE_FAIL_TEARDOWN_TC,
                TestStepFail: ReturnCodes.RETCODE_FAIL_TEARDOWN_TC,
                TestStepError: ReturnCodes.RETCODE_FAIL_TEARDOWN_TC,
                InconclusiveError: ReturnCodes.RETCODE_FAIL_INCONCLUSIVE,
                SkippedTestcaseException: ReturnCodes.RETCODE_SKIP,
                KeyboardInterrupt: {"retcode": ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER,
                                    "message": "Aborted by user"},
                Exception: ReturnCodes.RETCODE_FAIL_TEARDOWN_TC
            },
            "teardown": {
                KeyboardInterrupt: ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER,
            }
        }
        message = str(error)
        return_code = None
        if state in retcode_matrix:
            state_dict = retcode_matrix.get(state)
            if state_dict is not None:
                retcode = state_dict.get(error.__class__)
            else:
                retcode = state_dict.get(Exception)
            if retcode is None:
                return_code = state_dict.get(Exception)
            elif isinstance(retcode, dict):
                return_code = retcode.get("retcode")
                message = retcode.get("message")
            else:
                return_code = retcode
        self.retcode = return_code
        return return_code, message

    def failure(self, exception, method, retcode, message=None):
        """
        Failure handling.

        :param exception: Exception that happened
        :param method: Method where error happened
        :param retcode: int
        :param message: str
        :return: Nothing
        """
        exc_info = True if not isinstance(exception, SkippedTestcaseException) else False
        if method == "setup_bench":
            self.logger.error("Test bench initialization failed.", exc_info=exc_info)
        elif method == "setup":
            self.logger.error("Test setup failed.", exc_info=exc_info)
        elif method == "case":
            self.logger.error("Test case failed.", exc_info=exc_info)
        elif method == "teardown_test":
            self.logger.error("Test case teardown failed.", exc_info=exc_info)
        elif method == "teardown_bench":
            self.logger.error("Test bench teardown failed.", exc_info=exc_info)
        else:
            self.logger.error("Failed method unknown to handler: %s", method)
        self._call_exception(method, exception, retcode, message)
