# pylint: disable=no-member,too-many-arguments
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

Commands for duts.
"""

import sys
from threading import Event
import uuid

from icetea_lib.CliRequest import CliRequest
from icetea_lib.CliAsyncResponse import CliAsyncResponse
from icetea_lib.CliResponse import CliResponse
from icetea_lib.Events.EventMatcher import EventMatcher
from icetea_lib.Events.Generics import EventTypes
from icetea_lib.TestStepError import TestStepError, TestStepFail, TestStepTimeout


class CommandResponseCodes(object):  # pylint: disable=too-few-public-methods
    """
    Enum for cliapp command invalid return codes.
    """
    INVALID_PARAMS = -2
    NOT_IMPLEMENTED = -3
    CALLBACK_MISSING = -4
    UNKNOWN_COMMAND = -5


class Commands(object):
    """
    This mixer manage command execution for individual dut.
    It brings API's for pre and post command sending
    """
    def __init__(self, logger, plugins, resources, args, benchfunctions, **kwargs):
        self.__preliminary_verdict = None
        super(Commands, self).__init__(**kwargs)
        self._plugins = plugins
        self._logger = logger
        self._resources = resources
        self._args = args
        self._benchfunctions = benchfunctions

    def init(self, logger=None):
        """
        Nothing to see here.
        """
        if logger:
            self._logger = logger

    @property
    def command(self):
        """
        Alias for execute_command.

        :return: execute_command attribute reference.
        """
        return self.execute_command

    def wait_for_async_response(self, cmd, async_resp):
        """
        Wait for the given asynchronous response to be ready and then parse it.

        :param cmd: The asynchronous command that was sent to DUT.
        :param async_resp: The asynchronous response returned by the preceding command call.
        :return: CliResponse object
        """
        if not isinstance(async_resp, CliAsyncResponse):
            self._logger.error("Not an asynchronous response")
            raise AttributeError("%s is not an instance of CliAsyncResponse" % async_resp)

        # Check if this object has already been parsed.
        # If the response isn't yet ready, accessing 'resp.parsed' will call the __getattr__
        # method of CliAsyncResponse,
        # which will block until a response is ready.
        if async_resp.parsed:
            # If parser was already run for this CliAsyncResponse object just return the result
            return async_resp.response

        # Parse response
        resp = async_resp.response
        if resp:
            parsed = self._plugins.parse_response(cmd.split(' ')[0].strip(), resp)
            if parsed is not None:
                resp.parsed = parsed
                if parsed.keys():
                    self._logger.info(parsed)
        return resp

    def execute_command(self, k, cmd,  # pylint: disable=invalid-name
                        wait=True,
                        timeout=50,
                        expected_retcode=0,
                        asynchronous=False,
                        report_cmd_fail=True):
        """
        Do Command request for DUT.
        If this fails, testcase will be marked as failed in internal mechanisms.
        This will happen even if you later catch the exception in your testcase.
        To get around this (allow command failing without throwing exceptions),
        use the reportCmdFail parameter which disables the raise.

        :param k: Index where command is sent, '*' -send command for all duts.
        :param cmd: Command to be sent to DUT.
        :param wait: For special cases when retcode is not wanted to wait.
        :param timeout: Command timeout in seconds.
        :param expected_retcode: Expecting this retcode, default: 0, can be None when it is ignored.
        :param asynchronous: Send command, but wait for response in parallel.
        When sending next command previous response will be wait. When using async mode,
        response is dummy.
        :param report_cmd_fail: If True (default), exception is thrown on command execution error.
        :return: CliResponse object
        """
        ret = None
        if not report_cmd_fail:
            expected_retcode = None
        if k == '*':
            ret = self._send_cmd_to_all(cmd, wait=wait, expected_retcode=expected_retcode,
                                        timeout=timeout, asynchronous=asynchronous,
                                        report_cmd_fail=report_cmd_fail)
        else:
            if isinstance(k, str):
                k = self._resources.get_dut_index(k)

            if not self._resources.is_allowed_dut_index(k):
                self._logger.error("Invalid DUT number")
                raise ValueError("Invalid DUT number when calling execute_command(%i)" % k)

            if not self._resources.is_my_dut_index(k):
                self._wait_for_exec_ext_dut_cmd(k, cmd)
                return CliResponse()

            dut = self._resources.get_dut(k)
            ret = self._execute_command(dut, cmd, wait=wait, expected_retcode=expected_retcode,
                                        timeout=timeout, asynchronous=asynchronous,
                                        report_cmd_fail=report_cmd_fail)
        return ret

    # private members
    def _send_cmd_to_all(self, cmd, wait=True, expected_retcode=0, timeout=50, asynchronous=False,
                         report_cmd_fail=True):
        """
        Send command to all duts.
        :return: list of CliResponses
        """
        resps = []
        for i in self._resources.dut_indexes:
            resps.append(
                self.execute_command(i, cmd, wait=wait, expected_retcode=expected_retcode,
                                     timeout=timeout, asynchronous=asynchronous,
                                     report_cmd_fail=report_cmd_fail))
        return resps

    def _wait_for_exec_ext_dut_cmd(self, k, command):
        """
        Wait for Enter to be pressed when dut has executed command.
        :param k: Dut to command
        :param command: command to send
        :return: Nothing
        :raises: EnvironmentError if command failed.
        """

        if self._args.pause_when_external_dut:
            nick = self._resources.get_dut_nick(k)
            print("Press [ENTER] when %s execute command '%s'" % (nick, command))
            resp = sys.stdin.readline().strip()
            if resp != '':
                raise EnvironmentError("%s fail command" % nick)

    def send_pre_commands(self, cmds=""):
        """
        Send pre-commands to duts.

        :param cmds: Commands to send as string
        :return: Nothing
        """
        # Execute DUT-specific pre-commands
        for k, conf in enumerate(self._resources.resource_configuration.get_dut_configuration()):
            pre = conf.get("pre_cmds")
            if pre:
                for cmd in pre:
                    self.execute_command(k + 1, cmd)
        if cmds and cmds:
            if cmds.startswith('file:'):
                # @todo
                raise NotImplementedError('"--pre-cmds" -option with file not supported')
            else:
                self.execute_command('*', cmds)

    def send_post_commands(self, cmds=""):
        """
        Send post commands to duts.

        :param cmds: Commands to send as string.
        :return:
        """
        for k, conf in enumerate(self._resources.resource_configuration.get_dut_configuration()):
            post = conf.get("post_cmds")
            if post:
                for cmd in post:
                    self.execute_command(k + 1, cmd)
        if cmds and cmds:
            self.execute_command('*', cmds)

    def _check_expected_retcode(self, expected_retcode, req):
        """
        Check if retcode of req was what we expected.

        :param expected_retcode: Expected return code.
        :param req: Request
        :return: Nothing
        """
        if expected_retcode is not None:
            # reconfigure preliminary verdict
            # print only first failure
            if self.__preliminary_verdict is None:
                # init first preliminary when calling first time
                self.__preliminary_verdict = req.response.retcode == req.expected_retcode
                if self.__preliminary_verdict is False:
                    self._logger.warning("command fails - set preliminaryVerdict as FAIL")
            elif req.response.retcode != req.expected_retcode:
                if self.__preliminary_verdict is True:
                    # if any command fails, it mean that TC fails
                    self.__preliminary_verdict = False
                    self._logger.warning("command fails - set preliminaryVerdict as FAIL")
            # Raise expection if command fails
            if req.response.retcode != req.expected_retcode:
                self._command_fail(req)

    # pylint: disable=too-many-branches
    def _execute_command(self, dut, cmd, wait=True, expected_retcode=0, timeout=50,
                         asynchronous=False, report_cmd_fail=True):
        """
        Internal command sender.
        """
        try:
            # construct command object to be execute

            req = CliRequest(cmd, timestamp=self._benchfunctions.get_time(), wait=wait,
                             expected_retcode=expected_retcode, timeout=timeout,
                             asynchronous=asynchronous,
                             dutIndex=dut.index)
            # execute command
            try:
                req.response = dut.execute_command(req)
            except (TestStepFail, TestStepError, TestStepTimeout) as error:
                if not report_cmd_fail:
                    self._logger.error(
                        "An error occured when executing command on dut %s", dut.index)
                    self._logger.debug("reportCmdFail is set to False, don't raise.")
                    self._logger.error("Supressed error: %s", error)
                    if req.response is None:
                        req.response = CliResponse()
                else:
                    raise

            if wait and not asynchronous:
                # There should be valid responses
                self._check_expected_retcode(expected_retcode, req)
                # Parse response
                parsed = self._plugins.parse_response(cmd.split(' ')[0].strip(), req.response)
                if parsed is not None:
                    req.response.parsed = parsed
                    if parsed.keys():
                        self._logger.info(parsed)
            return req.response

        except (KeyboardInterrupt, SystemExit):
            # shut down tc directly
            self._logger.warning("Keyboard/SystemExit request - shut down TC")
            self._command_fail(CliRequest(), "Aborted by user")

    def _command_fail(self, req, fail_reason=None):
        """
        Command has failed.
        :raises: TestStepTimeout if dut timed out. TestStepFail in other cases. NameError if
        fail_reason was given.
        """

        self._logger.error('Test step fails!')

        if fail_reason:
            raise NameError(fail_reason)
        if req.response:
            if req.response.lines:
                self._logger.debug("Last command response from D%s:", req.dut_index)
                self._logger.debug('\n'.join(req.response.lines))

            if req.response.timeout:
                raise TestStepTimeout("dut" + str(req.dut_index) + " TIMEOUT, cmd: '" + req.cmd +
                                      "'")
            else:
                reason = "dut" + str(req.dut_index) + " cmd: '" + req.cmd + "',"
                if req.response.retcode == CommandResponseCodes.UNKNOWN_COMMAND:
                    reason += " unknown cmd"
                elif req.response.retcode == CommandResponseCodes.INVALID_PARAMS:
                    reason += " invalid params"
                elif req.response.retcode == CommandResponseCodes.NOT_IMPLEMENTED:
                    reason += " not implemented"
                elif req.response.retcode == CommandResponseCodes.CALLBACK_MISSING:
                    reason += " cb missing"
                else:
                    reason += "retcode: " + str(req.response.retcode)
                raise TestStepFail(reason)
        raise TestStepFail("command FAIL by unexpected reason")

    @staticmethod
    def get_echo_uuid(*args):  # pylint: disable=unused-argument
        """
        Get a echo command for start synchronization.

        :param args: Nothing
        :return: tuple ("echo <uuid>, <uuid>")
        """
        uid = str(uuid.uuid1())
        return ("echo {}".format(uid), uid)

    def sync_cli(self, dut, generator_function=None, generator_function_args=None, retries=None,
                 command_timeout=None):
        """
        Synchronize cli for a dut using custom function.

        :param dut: str or int
        :param generator_function: callable
        :param generator_function_args: list of arguments for generator_function
        :param retries: int, if set to 0 will skip command entirely (for unit testing purposes)
        :param command_timeout: int
        :raises: TestStepError: if synchronization fails.
        :raises: AttributeError: if retries is set to 0. Unit testing reasons.
        """
        # pylint: disable=too-many-locals
        if dut == "*":
            for dut_index in self._resources.dut_indexes:
                self.sync_cli(dut_index, generator_function, generator_function_args, retries,
                              command_timeout)
            return None
        dut = self._resources.get_dut(dut)
        generator_args = generator_function_args if generator_function_args else []
        init_done_flag = Event()
        matcher = None
        cmd_timeout = command_timeout if command_timeout else None
        retry_count = retries if retries is not None else None
        generator_function = generator_function if generator_function else None
        app = dut.config.get("application")
        if not app:
            if cmd_timeout is None:
                cmd_timeout = 5
            if retry_count is None:
                retry_count = 5
        else:
            sync_cli = app.get("sync_cli", dict())
            if cmd_timeout is None:
                cmd_timeout = sync_cli.get("command_timeout", 5)
            if retry_count is None:
                retry_count = sync_cli.get("retries", 5)
        if generator_function is None:
            generator_function = self.get_echo_uuid
        for _ in range(0, retry_count):
            cmd_tuple = generator_function(generator_args)
            command = cmd_tuple[0]
            retval = cmd_tuple[1]
            self._logger.debug("Sending %s. Expecting %s", command, retval)
            matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED,
                                   retval, dut, init_done_flag)
            self.command(dut.index, command, timeout=cmd_timeout, asynchronous=True,
                         wait=False, report_cmd_fail=False)
            if init_done_flag.wait(cmd_timeout):
                self._logger.info("Synchronization complete.")
                break
            else:
                self._logger.debug("Retrying...")
                matcher.forget()
        if not init_done_flag.isSet():
            self._logger.error("Command line interface synchronization failed.")
            dut.close_dut()
            dut.close_connection()
            matcher.forget()
            raise TestStepError("Synchronization for dut {} failed.".format(dut.index))
        matcher.forget()
        return None
