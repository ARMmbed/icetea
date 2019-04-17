# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods,too-many-instance-attributes,too-many-arguments
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

BenchApi module.
"""

from six import iteritems

from icetea_lib.tools.deprecated import deprecated
from icetea_lib.TestBench.Configurations import Configurations
from icetea_lib.TestBench.ArgsHandler import ArgsHandler
from icetea_lib.TestBench.Logger import Logger
from icetea_lib.TestBench.Resources import ResourceFunctions
from icetea_lib.TestBench.Plugins import Plugins
from icetea_lib.TestBench.Commands import Commands
from icetea_lib.TestBench.Results import Results
from icetea_lib.TestBench.NetworkSniffer import NetworkSniffer
from icetea_lib.TestBench.BenchFunctions import BenchFunctions


class BenchApi(object):
    """
    BenchApi class. Implements methods that provide access to the implementations contained in
    the other TestBench modules.
    """
    def __init__(self, **kwargs):
        super(BenchApi, self).__init__()
        self._arguments = ArgsHandler()
        self._logger = Logger()
        self._configurations = Configurations(args=self._arguments.args,
                                              logger=self.logger, **kwargs)

        self._resources = ResourceFunctions(self._arguments.args, self.logger, self._configurations)
        self._plugins = Plugins(self.logger, self.env, self._arguments.args,
                                self._configurations.config)
        self._resultfunctions = Results(self.logger, self._resources,
                                        self._configurations, self._arguments.args)
        self._benchfunctions = BenchFunctions(self.resource_configuration,
                                              self._resources, self._configurations)
        self._commands = Commands(self.logger, self._plugins, self._resources, self._arguments.args,
                                  self._benchfunctions)
        self._nwsniffer = NetworkSniffer(self._resources,
                                         self._configurations, self._arguments.args,
                                         self.logger)

    def _init(self):
        """
        Initialize internal class instances.
        """
        self._logger.init_logger(self._configurations.test_name,
                                 self.args.verbose,
                                 self.args.silent,
                                 self.args.color,
                                 self.args.disable_log_truncate)
        self._benchfunctions.init(logger=self.logger)
        self._configurations.init(self.logger)
        self._resources.init(self._commands, self.logger)
        self._plugins.init(self, self.logger)
        self._resultfunctions.init(self.logger)
        self._nwsniffer.init(self.logger)
        self._commands.init(self.logger)
        self.__wrap_obsoleted_functions()

    def get_logger(self):
        """
        Get logger function. Calls Logger.get_logger().

        :return: BenchLoggerAdapter
        """
        return self._logger.get_logger()

    @property
    def args(self):
        """
        Gets known args from ArgsHandler.

        :return: Namespace
        """
        return self._arguments.args

    @args.setter
    def args(self, value):
        """
        Setter for known args.
        """
        self._arguments.args = value

    @property
    def unknown(self):
        """
        Gets unknown args from ArgsHandler.
        """
        return self._arguments.unknown

    @unknown.setter
    def unknown(self, value):
        """
        Setter for unknown args.
        """
        self._arguments.unknown = value

    @property
    def logger(self):
        """
        :return: Logger from Logger. BenchLoggerAdapter usually.
        """
        return self._logger.get_logger()

    @logger.setter
    def logger(self, value):
        """
        Sets logger.
        """
        self._logger.set_logger(value)

    @property
    def test_name(self):
        """
        Returns test_name from Configurations.
        """
        return self._configurations.test_name

    @property
    def config(self):
        """
        :return: Configurations.config
        """
        return self._configurations.config

    @config.setter
    def config(self, value):
        """
        Sets Configurations.config.
        """
        self._configurations.config = value

    @property
    def env(self):
        """
        :return: Configurations.env
        """
        return self._configurations.env

    def sync_cli(self, dut, generator_function=None, generator_function_args=None, retries=None,
                 command_timeout=None):
        """
        Synchronize cli for a dut using custom function.

        :param dut: Dut
        :param generator_function: callable
        :param generator_function_args: list of arguments for generator_function
        :param retries: int, if set to 0 will skip command entirely (for unit testing purposes)
        :param command_timeout: int
        :raises: TestStepError: if synchronization fails.
        :raises: AttributeError: if retries is set to 0, unit testing reasons.
        """
        return self._commands.sync_cli(dut, generator_function, generator_function_args,
                                       retries, command_timeout)

    def is_hardware_in_use(self):
        """
        :return: True if type is hardware
        """
        return self._configurations.is_hardware_in_use()

    def get_platforms(self):
        """
        Get list of dut platforms.

        :return: list
        """
        return self._resources.get_platforms()

    def get_serialnumbers(self):
        """
        Get list of dut serial numbers.

        :return: list
        """
        return self._resources.get_serialnumbers()

    def get_test_component(self):
        """
        Get test component.

        :return: string
        """
        return self._configurations.get_test_component()

    def get_features_under_test(self):
        """
        Get features tested by this test case.

        :return: list
        """
        return self._configurations.get_features_under_test()

    def get_allowed_platforms(self):
        """
        Return list of allowed platfroms from requirements.

        :return: list
        """
        return self._configurations.get_allowed_platforms()

    def status(self):
        """
        Get TC implementation status.

        :return: string or None
        """
        return self._configurations.status()

    def type(self):
        """
        Get test case type.

        :return: string or None
        """
        return self._configurations.type()

    def subtype(self):
        """
        Get test case subtype.

        :return: string or None
        """
        return self._configurations.subtype()

    def get_config(self):
        """
        Get test case configuration.

        :return: dict
        """
        return self._configurations.get_config()

    def skip(self):
        """
        Get skip value.

        :return: Boolean or None
        """
        return self._configurations.skip()

    def skip_info(self):
        """
        Get the entire skip dictionary.

        :return: dictionary or None
        """
        return self._configurations.skip_info()

    def skip_reason(self):
        """
        Get skip reason.

        :return: string
        """
        return self._configurations.skip_reason()

    def get_tc_abspath(self, tc_file=None):
        """
        Get path to test case.

        :param tc_file: name of the file. If None, tcdir used instead.
        :return: absolute path.
        """
        return self._configurations.get_tc_abspath(tc_file)

    def set_config(self, config):
        """
        Set the configuration for this test case.

        :param config: dictionary
        :return: Nothing
        """
        return self._configurations.set_config(config)

    def check_skip(self):
        """
        Check if tc should be skipped

        :return: Boolean
        """
        return self._configurations.check_skip()

    def load_plugins(self):
        """
        Initialize PluginManager and Load bench related plugins.

        :return: Nothing
        """
        return self._plugins.load_plugins()

    def init_duts(self):
        """
        Initialize Duts, and the network sniffer.

        :return: Nothing
        """
        return self._resources.init_duts(self)

    def duts_release(self):
        """
        Release Duts.

        :return: Nothing
        """
        return self._resources.duts_release()

    @property
    def resource_configuration(self):
        """
        Getter for __resource_configuration.

        :return: ResourceConfig
        """
        return self._resources.resource_configuration

    @resource_configuration.setter
    def resource_configuration(self, value):
        """
        Setter for __resource_configuration.

        :param value: ResourceConfig
        :return: Nothing
        """
        self._resources.resource_configuration = value

    def dut_count(self):
        """
        Getter for dut count from resource configuration.

        :return: int
        """
        return self._resources.dut_count()

    def get_dut_count(self):
        """
        Get dut count.

        :return: int
        """
        return self._resources.get_dut_count()

    @property
    def resource_provider(self):
        """
        Getter for __resource_provider

        :return: ResourceProvider
        """
        return self._resources.resource_provider

    @property
    def duts(self):
        """
        Get _duts.

        :return: list
        """
        return self._resources.duts

    @duts.setter
    def duts(self, value):
        """
        set a list as _duts.

        :param value: list
        :return: Nothing
        """
        self._resources.duts = value

    def duts_iterator_all(self):
        """
        Yield indexes and related duts.
        """
        return self._resources.duts_iterator_all()

    def duts_iterator(self):
        """
        Yield indexes and related duts that are for this test case.
        """
        return self._resources.duts_iterator()

    def is_allowed_dut_index(self, dut_index):
        """
        Check if dut_index is one of the duts for this test case.

        :param dut_index: int
        :return: Boolean
        """
        return self._resources.is_allowed_dut_index(dut_index=dut_index)

    @property
    def dut_indexes(self):
        """
        Get a list with dut indexes.

        :return: list
        """
        return self._resources.dut_indexes

    def get_dut(self, k):
        """
        Get dut object.

        :param k: index or nickname of dut.
        :return: Dut
        """
        return self._resources.get_dut(k)

    def get_node_endpoint(self, endpoint_id):
        """
        get NodeEndPoint object for dut endpoint_id.

        :param endpoint_id: nickname of dut
        :return: NodeEndPoint
        """
        return self._resources.get_node_endpoint(endpoint_id, self)

    def is_my_dut_index(self, dut_index):
        """
        :return: Boolean
        """
        return self._resources.is_my_dut_index(dut_index)

    @property
    def dutinformations(self):
        """
        Getter for DutInformation list.

        :return: list
        """
        return self._resources.dutinformations

    @dutinformations.setter
    def dutinformations(self, value):
        """
        Setter for dutinformations

        :param value: DutInformationList
        :return: Nothing
        """
        self._resources.dutinformations = value

    def reset_dut(self, dut_index="*"):
        """
        Reset dut k.

        :param dut_index: index of dut to reset. Default is *, which causes all duts to be reset.
        :return: Nothing
        """
        return self._resources.reset_dut(dut_index)

    def get_dut_nick(self, dut_index):
        """
        Get nick of dut index k.

        :param dut_index: index of dut
        :return: string
        """
        return self._resources.get_dut_nick(dut_index)

    def get_dut_index(self, nick):
        """
        Get index of dut with nickname nick.

        :param nick: string
        :return: integer > 1
        """
        return self._resources.get_dut_index(nick)

    def is_my_dut(self, k):
        """
        :return: Boolean
        """
        return self._resources.is_my_dut(k)

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
        return Results.create_new_result(verdict, retcode, duration, input_data)

    def add_new_result(self, verdict, retcode, duration, input_data):
        """
        Add a new Result to result object to the internal ResultList.

        :param verdict: Verdict as string
        :param retcode: Return code as int
        :param duration: Duration as time
        :param input_data: Input data as dict
        :return: Result
        """
        return self._resultfunctions.add_new_result(verdict, retcode, duration, input_data)

    @property
    def results(self):
        """
        Getter for internal _results variable.
        """
        return self._resultfunctions.get_results()

    @results.setter
    def results(self, value):
        """
        Call setter for internal ResultList.

        :param value: ResultList
        :return: Nothing
        """
        self._resultfunctions.set_results(value)

    @property
    def retcode(self):
        """
        Getter for return code.

        :return: int
        """
        return self._resultfunctions.retcode

    @retcode.setter
    def retcode(self, value):
        """
        Setter for retcode.

        :param value: int
        :return: Nothing
        """
        self._resultfunctions.retcode = value

    def get_result(self, tc_file=None):
        """
        Generate a Result object from this test case.

        :param tc_file: Location of test case file
        :return: Result
        """
        return self._resultfunctions.get_result(tc_file)

    def append_result(self, tc_file=None):
        """
        Append a new fully constructed Result to the internal ResultList.

        :param tc_file: Test case file path
        :return: Nothing
        """
        return self._resultfunctions.append_result(tc_file)

    def set_failure(self, retcode, reason):
        """
        Set internal state to reflect failure of test.

        :param retcode: return code
        :param reason: failure reason as string
        :return: Nothing
        """
        return self._resultfunctions.set_failure(retcode, reason)

    def input_from_user(self, title=None):
        """
        Input data from user.

        :param title: Title as string
        :return: stripped data from stdin.
        """
        return self._benchfunctions.input_from_user(title)

    def open_node_terminal(self, k="*", wait=True):
        """
        Open Putty (/or kitty if exists)

        :param k: number 1.<max duts> or '*' to open putty to all devices
        :param wait: wait while putty is closed before continue testing
        :return: Nothing
        """
        return self._benchfunctions.open_node_terminal(k, wait)

    def delay(self, seconds):
        """
        Sleep command.

        :param seconds: Amount of seconds to sleep.
        :return: Nothing
        """
        return self._benchfunctions.delay(seconds)

    def verify_trace_skip_fail(self, k, expected_traces):
        """
        Shortcut to set break_in_fail to False in verify_trace.

        :param k: nick or index of dut.
        :param expected_traces: Expected traces as a list or string
        :return: boolean
        """
        return self._benchfunctions.verify_trace_skip_fail(k, expected_traces)

    def verify_trace(self, k, expected_traces, break_in_fail=True):
        """
        Verify that traces expected_traces are found in dut traces.

        :param k: index or nick of dut whose traces are to be used.
        :param expected_traces: list of expected traces or string
        :param break_in_fail: Boolean, if True raise LookupError if search fails
        :return: boolean.
        :raises: LookupError if search fails.
        """
        return self._benchfunctions.verify_trace(k, expected_traces, break_in_fail)

    def get_time(self):
        """
        Get timestamp using time.time().

        :return: timestamp
        """
        return self._benchfunctions.get_time()

    @property
    def command(self):
        """
        Alias for execute_command.

        :return: execute_command attribute reference.
        """
        return self._commands.command

    def wait_for_async_response(self, cmd, async_resp):
        """
        Wait for the given asynchronous response to be ready and then parse it.

        :param cmd: The asynchronous command that was sent to DUT.
        :param async_resp: The asynchronous response returned by the preceding command call.
        :return: CliResponse object
        """
        return self._commands.wait_for_async_response(cmd, async_resp)

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
        return self._commands.execute_command(k, cmd,  # pylint: disable=invalid-name
                                              wait,
                                              timeout,
                                              expected_retcode,
                                              asynchronous,
                                              report_cmd_fail)

    def send_post_commands(self, cmds=""):
        """
        Send post commands to duts.

        :param cmds: Commands to send as string.
        :return:
        """
        return self._commands.send_post_commands(cmds)

    def send_pre_commands(self, cmds=""):
        """
        Send pre-commands to duts.

        :param cmds: Commands to send as string
        :return: Nothing
        """
        return self._commands.send_pre_commands(cmds)

    def init_sniffer(self):
        """
        Initialize and start sniffer if it is required.

        :return: Nothing
        """
        return self._nwsniffer.init_sniffer()

    def get_start_time(self):
        """
        Get test start timestamp.
        :return: None or timestamp.
        """
        return self._resources.get_start_time()

    @property
    def wshark(self):
        """
        Return wireshark object.

        :return: Wireshark
        """
        return self._nwsniffer.wshark

    @property
    def tshark_arguments(self):
        """
        Get tshark arguments.

        :return: dict
        """
        return self._nwsniffer.tshark_arguments

    @property
    def sniffer_required(self):
        """
        Check if sniffer was requested for this run.

        :return: Boolean
        """
        return self._nwsniffer.sniffer_required

    def clear_sniffer(self):
        """
        Clear sniffer

        :return: Nothing
        """
        return self._nwsniffer.clear_sniffer()

    @property
    def capture_file(self):
        """
        Return capture file path.

        :return: file path of capture file.
        """
        return self._nwsniffer.capture_file

    def get_nw_log_filename(self):
        """
        Get nw data log file name.

        :return: string
        """
        return self._nwsniffer.get_nw_log_filename()

    @property
    def pluginmanager(self):
        """
        Getter for PluginManager.

        :return: PluginManager
        """
        return self._plugins.pluginmanager

    @pluginmanager.setter
    def pluginmanager(self, value):
        """
        Setter for PluginManager.
        """
        self._plugins.pluginmanager = value

    def start_external_services(self):
        """
        Start ExtApps required by test case.

        :return: Nothing
        """
        return self._plugins.start_external_services()

    def stop_external_services(self):
        """
        Stop external services started via PluginManager
        """
        return self._plugins.stop_external_services()

    def parse_response(self, cmd, response):
        """
        Parse a response for command cmd.

        :param cmd: Command
        :param response: Response
        :return: Parsed response (usually dict)
        """
        return self._plugins.parse_response(cmd, response)

    def _validate_dut_configs(self, dut_configuration_list, logger):
        """
        Validate dut configurations.

        :param dut_configuration_list: dictionary with dut configurations
        :param logger: logger to be used
        :raises EnvironmentError if something is wrong
        """
        return self._resources.validate_dut_configs(dut_configuration_list, logger)

    # Backwards compatibility functions here

    def __wrap_obsoleted_functions(self):
        """
        Replaces obsoleted setup and teardown step names with old ones to provide backwards
        compatibility.

        :return: Nothing
        """
        wrappers = {
            'rampUp': 'setup',
            'setUp': 'setup',
            'rampDown': 'teardown',
            'tearDown': 'teardown'
        }
        for key, value in iteritems(wrappers):
            if hasattr(self, key) and not hasattr(self, value):
                self.logger.warning("%s has been deprecated, please rename it to %s", key, value)
                setattr(self, value, getattr(self, key))

    def get_dut_range(self, i=0):
        """
        get range of length dut_count with offset i.
        :param i: Offset
        :return: range
        """
        return self.resource_configuration.get_dut_range(i)

    @deprecated("Please use test_name property instead.")
    def get_test_name(self):
        """
        Get test case name.

        :return: str
        """
        return self.test_name

    @deprecated("_check_skip has been deprecated. Use check_skip instead.")
    def _check_skip(self):
        """
        Backwards compatibility.
        """
        return self._configurations.check_skip()

    @property
    @deprecated("_dut_count has been deprecated. Use dut_count() instead.")
    def _dut_count(self):
        """
        Backwards compatibility.
        """
        return self.dut_count()

    @property
    @deprecated("_platforms has been deprecated. Please use get_platforms() instead.")
    def _platforms(self):
        """
        Deprecated getter property for platforms.

        :return: list of strings
        """
        return self.get_platforms()

    @property
    @deprecated("_serialnumbers has been deprecated. Please use get_serialnumbers() instead.")
    def _serialnumbers(self):
        """
        Deprecated property for serial numbers.

        :return: list of strings
        """
        return self.get_serialnumbers()

    @property
    @deprecated("Use test_name instead.")
    def name(self):
        """
        Returns name from Configurations.
        """
        return self._configurations.name

    @deprecated("Please don't use this function.")
    def get_dut_versions(self):
        """
        Get nname results and set them to duts.

        :return: Nothing
        """
        return self._resources.get_dut_versions(self._commands)

    @property
    @deprecated("_starttime has been deprecated. Please use get_start_time instead.")
    def _starttime(self):
        """
        Deprecated getter for test start time.

        :return: None or timestamp.
        """
        return self.get_start_time()

    @property
    @deprecated("_results has been deprecated. Please use results instead.")
    def _results(self):
        """
        Deprecated getter for results.

        :return: ResultList
        """
        return self.results

    @_results.setter
    @deprecated("_results has been deprecated. Please use results instead.")
    def _results(self, value):
        """
        Deprecated setter for results.

        :param value: ResultList
        :return: Nothing
        """
        self.results = value

    @property
    @deprecated("_dutinformation has been deprecated. Please use dutinformations instead.")
    def _dutinformations(self):
        """
        Deprecated getter for dut information list.

        :return: DutInformationList
        """
        return self.dutinformations

    @_dutinformations.setter
    @deprecated("_dutinformation has been deprecated. Please use dutinformations instead.")
    def _dutinformations(self, value):
        """
        Deprecated setter for dut information list.

        :param value: DutInformationList
        :return: Nothing
        """
        self.dutinformations = value

    @deprecated("set_args has been deprecated, please use the args property instead.")
    def set_args(self, args):
        """
        Deprecated setter for args.

        :param args:
        :return:
        """
        self.args = args

    @deprecated("get_metadata has been deprecated, please use get_config() instead")
    def get_metadata(self):
        """
        Deprecated getter for test configuration and metadata.

        :return: dict
        """
        return self.get_config()

    @deprecated("get_resource_configuration has been deprecated, please use the "
                "resource_configuration property instead.")
    def get_resource_configuration(self):
        """
        Deprecated getter for resource configuration.
        :return: ResourceConfig
        """
        return self.resource_configuration
