# pylint: disable=too-many-lines,too-many-arguments,too-many-statements,too-many-branches

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

Bench module. This does all the things and is in dire need of refactoring to reduce complexity
and speed up further development and debugging.
"""

import logging
import os
import sys
import time
import traceback
import json
from pprint import pformat
import subprocess
from jsonmerge import merge

from six import string_types

# Internal libraries

from icetea_lib.CliRequest import CliRequest
from icetea_lib.CliResponse import CliResponse
from icetea_lib.CliAsyncResponse import CliAsyncResponse
from icetea_lib.CliResponseParser import ParserManager

from icetea_lib.arguments import get_parser
from icetea_lib.arguments import get_base_arguments
from icetea_lib.arguments import get_tc_arguments
from icetea_lib.build import Build

from icetea_lib.GenericProcess import GenericProcess
from icetea_lib.GitTool import get_git_info

from icetea_lib.ResourceProvider.ResourceProvider import ResourceProvider
from icetea_lib.ResourceProvider.ResourceConfig import ResourceConfig
from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList

from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.ResourceProvider.Allocators.exceptions import AllocationError
import icetea_lib.LogManager as LogManager
from icetea_lib.Plugin.PluginManager import PluginManager, PluginException
from icetea_lib.Searcher import verify_message
from icetea_lib.TestStepError import TestStepError, TestStepFail, TestStepTimeout
from icetea_lib.TestStepError import InconclusiveError
from icetea_lib.tools.tools import load_class


class ReturnCodes(object): #pylint: disable=no-init,too-few-public-methods
    #pylint: disable=invalid-name
    """
    Enum for Bench return codes.
    """
    RETCODE_SKIP = -1
    RETCODE_SUCCESS = 0
    RETCODE_FAIL_SETUP_BENCH = 1000
    RETCODE_FAIL_SETUP_TC = 1001
    RETCODE_FAIL_MISSING_DUTS = 1002
    RETCODE_FAIL_UNDEFINED_REQUIRED_DUTS_COUNT = 1003
    RETCODE_FAIL_DUT_CONNECTION_FAIL = 1004
    RETCODE_FAIL_TC_EXCEPTION = 1005
    RETCODE_FAIL_TEARDOWN_TC = 1006
    RETCODE_FAIL_INITIALIZE_BENCH = 1007
    RETCODE_FAIL_NO_PRELIMINARY_VERDICT = 1010
    RETCODE_FAIL_TEARDOWN_BENCH = 1011
    RETCODE_FAIL_ABORTED_BY_USER = 1012
    RETCODE_FAIL_UNKNOWN = 1013
    RETCODE_FAIL_INCONCLUSIVE = 1014
    INCONCLUSIVE_RETCODES = [RETCODE_FAIL_ABORTED_BY_USER, RETCODE_FAIL_INITIALIZE_BENCH,
                             RETCODE_FAIL_TEARDOWN_BENCH, RETCODE_FAIL_SETUP_BENCH,
                             RETCODE_FAIL_DUT_CONNECTION_FAIL, RETCODE_FAIL_INCONCLUSIVE]


class NodeEndPoint(object): #pylint: disable=too-few-public-methods
    """
    Wrapper for a dut, contains a shortcut to send commands to this dut specifically.
    """

    def __init__(self, bench, endpoint_id):
        self.bench = bench
        self.endpoint_id = endpoint_id

    def command(self, cmd, expected_retcode=0):
        # expectedRetcode kwd argument is used in many test cases, we cannot rename it.
        """
        Shortcut for sending a command to this node specifically.

        :param cmd: Command to send
        :param expected_retcode: Expected return code as int, default is 0
        :return: CliResponse
        """
        return self.bench.command(self.endpoint_id, cmd, expected_retcode=expected_retcode)


class Bench(object):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """
    Bench class. Bench is the core of the test case execution. It triggers the execution of the
    test case, allocation of resources, setting up the environment, tearing down the test case
    and finally cleaning up the execution and generating the results.

    This class is a monolithic beast of some 1400 lines of code and it needs to be refactored
    completely at some point.
    """
    # pylint: disable=anomalous-backslash-in-string
    __env = {
        "sniffer": {
            "iface": "Sniffer"
        },
        "extApps": {
            "puttyExe": "C:\Program Files (x86)\PuTTY\putty.exe",
            "kittyExe": "C:\Program Files (x86)\PuTTY\kitty.exe"
        }
    }

    @staticmethod
    def _validate_dut_configs(dut_configuration_list, logger):
        """
        Validate dut configurations

        :param dut_configuration_list: dictionary with dut configurations
        :param logger: logger to be used
        :raises EnvironmentError if something is wrong
        """

        # for now we validate only binaries - if it exists or not.
        for conf in dut_configuration_list:
            try:
                binar = conf.get("application").get("bin")
                if binar:
                    build = Build.init(binar)
                    if not build.is_exists():
                        logger.warning("Binary '{}' not found".format(binar))
                        raise EnvironmentError("Binary not found")
            except(KeyError, AttributeError):
                pass
        logger.debug("Configurations seems to be ok")


    # Test Bench constructor
    # kwargs contains keys, like name, required_duts, ...
    #
    # executeCommand returns CliResponse class
    #

    @staticmethod
    def create_new_result(verdict, retcode, duration, input_data):
        new_result = Result(input_data)
        new_result.set_verdict(verdict, retcode, duration)
        return new_result

    def __init__(self, **kwargs):
        self.__retcode = None
        self.__failreason = ""
        self.__preliminary_verdict = None
        # TODO: Refactor when working on ExtApps as plugins
        self.__externalServices = [] # pylint: disable=invalid-name
        self.__sniffing = False
        self._parser_manager = None
        self.args = None
        self.name = ''
        self._dut_count = 0
        self._platforms = []
        self._serialnumbers = []
        self._starttime = None
        self.capture_file = None
        self.wshark = None
        self.tshark_arguments = {}
        self.tshark_preferences = {}
        self.duts = []
        self._result = None
        self._results = None
        self._dutinformations = []
        self.resource_configuration = None
        self.open_putty = self.open_node_terminal
        self._resource_provider = None
        self.logger = logging.getLogger()
        self._integer_keys_found = None
        self._pluginmanager = None
        self.dut_type = "unknown"
        self.config = {
            "compatible": {
                "framework": {
                    "name": "Icetea",
                    "version": ">=1.0.0-rc1"
                },
                "automation": {
                    "value": True
                },
                "hw": {
                    "value": True
                }
            },
            "name": None,
            "type": None,
            "sub_type": None,
            "requirements": {
                "duts": {"*": {
                    "application": {
                        "bin": None
                    }
                }},
                "external": {
                    "apps": [
                    ]
                }
            }
        }
        try:
            if len(kwargs["requirements"]["duts"]) > 1:
                self._integer_keys_found = False
                for key in kwargs["requirements"]["duts"]:
                    if isinstance(key, int):
                        self._integer_keys_found = True
                        val = kwargs["requirements"]["duts"].pop(key)
                        kwargs["requirements"]["duts"][str(key)] = val
        except KeyError:
            pass

        for key in kwargs:
            if isinstance(kwargs[key], dict) and key in self.config:
                self.config[key] = merge(self.config[key], kwargs[key])
            else:
                self.config[key] = kwargs[key]
        #set alias
        self.command = self.execute_command
        self.__parse_arguments()

    def add_new_result(self, verdict, retcode, duration, input_data):
        new_result = Bench.create_new_result(verdict, retcode, duration, input_data)
        if not self._results:
            self._results = ResultList()
        self._results.append(new_result)

    def get_config(self):
        """
        Get configuration of this test case

        :return: dictionary
        """
        return self.config

    def set_config(self, config):
        """
        Set the configuration for this test case

        :param config: dictionary
        :return: Nothing
        """
        self.config = config

    def get_allowed_platforms(self):
        try:
            return self.config["requirements"]["duts"]["*"]["allowed_platforms"]
        except KeyError:
            return []

    def get_tc_abspath(self, tc_file=None):
        """
        Get path to test case

        :param tc_file: name of the file. If None, tcdir used instead.
        :return: absolute path.
        """
        if not tc_file:
            return os.path.abspath(self.args.tcdir)
        return os.path.abspath(tc_file)

    def get_node_endpoint(self, endpoint_id):
        """
        Get NodeEndPoint object for dut endpoint_id

        :param endpoint_id: nickname of dut
        :return: NodeEndPoint
        """
        if isinstance(endpoint_id, string_types):
            endpoint_id = self.get_dut_index(endpoint_id)
        return NodeEndPoint(self, endpoint_id)

    def get_time(self):
        """
        Get time from start of test case.

        :return: time delta from start of test case.
        """
        return time.time() - self._starttime

    def __initialize(self):
        """
        Handle initialization of Parsers, ResourceProvider and logging. Read environment and
        execution configuration files.

        :return: True if everything went smoothly. False if environment configuration read failed.
        """
        # Initialize log instances
        self.__init_logs()
        self._parser_manager = ParserManager(self.logger)
        self._pluginmanager = PluginManager(responseparser=self._parser_manager, bench=self,
                                            logger=self.logger)
        # Read cli given environment configuration file
        env_cfg = self.__read_env_configs()
        if not env_cfg:
            self.logger.error("Error when reading environment configuration. Aborting")
            return False
        # Read cli given TC configuration file and merge it
        self.__read_exec_configs()

        # Create ResourceProvider object and resolve the resource requirements from configuration
        self._resource_provider = ResourceProvider(self.args)
        # @todo need better way to handle forceflash_once option
        # because provider is singleton instance.
        self._resource_provider.args.forceflash = self.args.forceflash
        self.resource_configuration = ResourceConfig(logger=self.logger)
        self._resource_provider.resolve_configuration(self.config, self.resource_configuration)
        return True

    # Parse Command line arguments
    def __parse_arguments(self):
        """
        Parse command line arguments

        :return: Nothing
        """
        parser = get_tc_arguments(get_base_arguments(get_parser()))
        self.args, self.unknown = parser.parse_known_args()

    def set_args(self, args):
        """
        Set args

        :param args: args
        :return: Nothing
        """
        self.args = args

    def __remove_handlers(self, logger): #pylint: disable=no-self-use
        """
        Remove handlers from logger.

        :param logger: logger whose handlers to remove
        :return: Nothing
        """
        while True:
            try:
                if isinstance(logger.handlers[0], logging.FileHandler):
                    logger.handlers[0].close()
                logger.removeHandler(logger.handlers[0])
            except: #pylint: disable=bare-except
                break

    # Initialize Logging library
    def __init_logs(self):
        """
        Initialize logging.

        :return: Nothing
        """
        LogManager.init_testcase_logging(self.get_test_name(), self.args.verbose,
                                         self.args.silent, self.args.color,
                                         not self.args.disable_log_truncate)
        self.logger = LogManager.get_bench_logger()

    # Read Environment Configuration JSON file
    def __read_env_configs(self):
        """
        Read environment configuration json file

        :return: False if read fails, True otherwise.
        """
        data = None

        env_cfg_filename = self.args.env_cfg if self.args.env_cfg != '' else './env_cfg.json'
        if os.path.exists(env_cfg_filename):
            with open(env_cfg_filename) as data_file:
                data = json.load(data_file)
        elif self.args.env_cfg != '':
            self.logger.error('Environment file %s does not exist', self.args.env_cfg)
            return False

        if data:
            self.__env = merge(self.__env, data)

        if self.args.iface:
            self.__env = merge(self.__env, {'sniffer': {'iface': self.args.iface}})
        return True

    # Read Execution Configuration file
    def __read_exec_configs(self):
        """
        Read execution configuration file

        :return: Nothing.
        :raises TestStepError if file cannot be read or merged into config, or if platform_name
        is not in allowed_platforms.
        """
        tc_cfg = None
        if self.args.tc_cfg:
            tc_cfg = self.args.tc_cfg
        #TODO: this bit is not compatible with IceteaManager's --tc argument.
        elif isinstance(self.args.tc, string_types) and os.path.exists(self.args.tc+'.json'):
            tc_cfg = self.args.tc +'.json'

        if tc_cfg:
            with open(tc_cfg) as data_file:
                try:
                    data = json.load(data_file)
                    self.config = merge(self.config, data)
                except Exception as error:
                    self.logger.error("Testcase configuration read from file (%s) failed!", tc_cfg)
                    self.logger.error(error)
                    raise TestStepError("TC CFG read fail!")

        if self.args.type:
            self.config["requirements"]["duts"]["*"] = merge(
                self.config["requirements"]["duts"]["*"],
                {"type": self.args.type})

        if self.args.bin:
            self.config["requirements"]["duts"]["*"] = merge(
                self.config["requirements"]["duts"]["*"],
                {"application": {'bin': self.args.bin}})

        if self.args.platform_name:
            allowed = self.config["requirements"]["duts"]["*"].get("allowed_platforms")
            if allowed:
                if self.args.platform_name in allowed:
                    self.config["requirements"]["duts"]["*"][
                        "platform_name"] = self.args.platform_name
                else:
                    raise TestStepError("Required platform_name not in allowed_platforms.")
            else:
                self.config["requirements"]["duts"]["*"][
                    "platform_name"] = self.args.platform_name

        self.name = self.config['name']

    def __ext_class_loader(self, name, class_type="ExtApps"): #pylint: disable=no-self-use
        """
        Load a module from icetea_lib.class_type.name

        :param name: name of module
        :param class_type: Name of module in which the loaded module is under icetea_lib
        :return: class object or None.
        """
        name = "icetea_lib."+class_type+"." + name
        return load_class(name)

    def __load_plugins(self):
        """
        Initialize PluginManager and Load bench related plugins

        :return: Nothing
        """
        self._pluginmanager = PluginManager(responseparser=self._parser_manager, bench=self,
                                            logger=self.logger)

        self._pluginmanager.load_default_tc_plugins()
        self._pluginmanager.load_custom_tc_plugins(self.args.plugin_path)

    # All required external services starting here
    def __start_external_services(self):
        """
        Start ExtApps required by test case.

        :return:
        """
        try:
            apps = self.config['requirements']['external']['apps']
        except KeyError:
            return
        for app in apps:
            # Check if we have an environment configuration for this app
            conf = app

            try:
                conf = merge(conf, self.__env["extApps"][app["name"]])
            except KeyError:
                self.logger.warning("Unable to merge configuration for app %s",
                                    app["name"],
                                    exc_info=True if not self.args.silent else False)

            if 'name' in app:
                try:
                    self._pluginmanager.start_external_service(app['name'], conf=conf)
                except PluginException:
                    self.logger.error("Failed to start requested external services.")
                    raise EnvironmentError("Failed to start requested external services.")
                self.logger.info("done")
            else:
                conf_path = None
                conf_cmd = None
                try:
                    conf_path = conf["path"]
                except KeyError:
                    self.logger.warning("No path defined for app %s", app["name"])

                try:
                    conf_cmd = conf["cmd"]
                except KeyError:
                    self.logger.warning("No command defined for app %s", app["name"])
                appname = app['name'] if 'name' in app else 'generic'
                newapp = GenericProcess(name=appname, path=conf_path, cmd=conf_cmd)
                newapp.ignore_return_code = True
                self.__externalServices.append(newapp)
                newapp.start_process()

    def __stop_external_services(self):
        """
        Stop all external services started from plugins.
        """
        self._pluginmanager.stop_external_services()

    def skip(self):
        """
        Get skip value

        :return: Boolean or None
        """
        try:
            return self.config['execution']['skip']['value']
        except KeyError:
            return None

    def skip_info(self):
        """
        Get the entire skip dictionary

        :return: dictionary or None
        """
        try:
            return self.config['execution']['skip']
        except KeyError:
            return None

    # Get Skip Reason
    def skip_reason(self):
        """
        Get skip reason

        :return: string
        """
        try:
            return self.config['execution']['skip']['reason']
        except KeyError:
            return ''

    def status(self):
        """
        Get TC implementation status

        :return: string or None
        """
        try:
            return self.config['status']
        except KeyError:
            return None

    def type(self):
        """
        Get test case type.

        :return: string or None
        """
        try:
            return self.config['type']
        except KeyError:
            return None

    def subtype(self):
        """
        Get test case subtype

        :return: string or None
        """
        try:
            return self.config['subtype']
        except KeyError:
            return None

    def get_test_name(self):
        """
        Get test bench name

        :return: string
        """
        try:
            return self.config["name"]
        except KeyError:
            return "unknown"

    def get_features_under_test(self):
        """
        Get features tested by this test case

        :return: list
        """
        try:
            fea = self.config["feature"]
            if isinstance(fea, str):
                return [fea]
            return fea
        except KeyError:
            return []

    def get_test_component(self):
        """
        Get test component

        :return: string
        """
        try:
            return self.config["component"]
        except KeyError:
            return ''

    def get_metadata(self):
        """
        Get test case configuration/metadata

        :return: dictionary
        """
        return self.get_config()

    def get_resource_configuration(self):
        """
        Get resource configuration

        :return: ResourceConfig
        """
        return self.resource_configuration

    def get_result(self, tc_file=None):
        """
        Generate a Result object from this test case.

        :param tc_file: Location of test case file
        :return: Result
        """
        if self._results is not None:
            return self._results
        result = self._result if self._result else Result()
        results = self._results if self._results else ResultList()
        result.set_tc_metadata(self.config)

        # regonize filepath and git information
        result.set_tc_git_info(get_git_info(self.get_tc_abspath(tc_file),
                                            verbose=self.args.verbose))
        self.logger.debug(result.tc_git_info)
        result.component = self.get_test_component()
        if isinstance(result.component, str):
            result.component = [result.component]

        result.feature = self.get_features_under_test()

        if self.skip_reason():
            result.skip_reason = self.skip_reason()

        result.fail_reason = self.__failreason
        result.logpath = os.path.abspath(LogManager.get_base_dir())
        result.logfiles = LogManager.get_logfiles()
        result.retcode = self.__retcode
        return result

    def verify_trace_skip_fail(self, k, expected_traces):
        """
        Shortcut to set break_in_fail to False in verify_trace

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
            dut_index = self.get_dut_index(k)
            return self.verify_trace(dut_index, expected_traces, break_in_fail)

        # If expectedTraces given as a String (expecting only a certain trace), wrap it in a list.
        if isinstance(expected_traces, str):
            expected_traces = [expected_traces]

        status = True
        try:
            status = verify_message(self.duts[k-1].traces, expected_traces)
        except TypeError as inst:
            status = False
            if break_in_fail:
                raise inst
        if status is False and break_in_fail:
            raise LookupError("{} not found in traces.".format(expected_traces))
        return status

    def get_dut_count(self):
        """
        Get dut count

        :return: integer
        """
        return len(self.duts)

    def get_dut_range(self, i=0):
        """
        get range of length dut_count with offset i.

        :param i: Offset
        :return: range
        """
        # TODO: This is a weird way to implement the desired functionality. TBD
        return range(1+i, self.resource_configuration.count_duts()+i+1)

    def get_nw_log_filename(self): #pylint: disable=no-self-use
        """
        Get nw data log file name.

        :return: string
        """
        return LogManager.get_testcase_logfilename("network.nw.pcap")

    def reset_dut(self, dut_index='*'):
        """
        Reset dut k.

        :param dut_index: index of dut to reset. Default is *, which causes all duts to be reset.
        :return: Nothing
        """
        if dut_index == '*':
            for ind in self.get_dut_range():
                if self.is_my_dut(ind):
                    self.reset_dut(ind)
            return
        method = None
        if self.args.reset == "hard" or self.args.reset == "soft":
            self.logger.debug("Sending reset %s to dut %d", self.args.reset, dut_index - 1)
            method = self.args.reset
        self.duts[dut_index - 1].init_wait_register()
        self.duts[dut_index - 1].reset(method)
        self.logger.debug("Waiting for dut %d to initialize", dut_index)
        result = self.duts[dut_index - 1].wait_init()
        if not result:
            self.logger.warning("Cli initialization trigger not found. Maybe your application"
                                " started before we started reading? Try adding --reset"
                                " to your run command.")
            raise DutConnectionError("Dut cli failed to initialize within set timeout!")
        self.logger.debug("CLI initialized")
        self.duts[dut_index - 1].init_cli()

    def is_hardware_in_use(self):
        """
        :return: True if type is hardware
        """
        return self.config["requirements"]["duts"]["*"]["type"] == "hardware"

    # Internal function to Initialize cli dut's
    def __init_duts(self):
        """
        Internal function to initialize duts

        :return: Nothing
        :raises: DutConnectionError if correct amount of duts were not initialized or if reset
        failed or if cli initialization wait loop timed out.
        """

        # Initialize command line interface
        self.logger.info("---------------------")
        self.logger.info("Initialize DUT's connections")

        allocations = self._resource_provider.allocate_duts(self.resource_configuration)
        allocations.set_logger(self.logger)
        allocations.set_resconf(self.resource_configuration)
        try:
            self.duts = allocations.init_duts(args=self.args)

            if len(self.duts) != self.resource_configuration.count_duts():
                raise DutConnectionError("Unable to initialize required amount of duts.")

            self._dutinformations = allocations.get_dutinformations()
        except AllocationError:
            raise

        for dut in self.duts:
            dut.init_wait_register()

        try:
            allocations.open_dut_connections()
        except DutConnectionError:
            self.logger.exception("Error while opening DUT connections!")
            for dut in self.duts:
                dut.close_dut()
                dut.close_connection()
            raise

        for ind, dut in enumerate(self.duts):
            self.logger.info("Waiting for dut %d to initialize.", ind+1)

            res = dut.wait_init()
            if not res:
                self.logger.warning("Cli initialization trigger not found. Maybe your application"
                                    " started before we started reading? Try adding --reset"
                                    " to your run command.")
                raise DutConnectionError("Dut cli failed to initialize within set timeout!")

            self.logger.debug("Cli initialized.")

        # @TODO: Refactor this into some more sensible way
        for i in self.get_dut_range(-1):
            if self.is_my_dut(i+1):
                self.duts[i].Testcase = self.name
                self.duts[i].init_cli()

        for i in self.get_dut_range(-1):
            if self.is_my_dut(i+1):
                self.logger.debug("DUT[%i]: %s", i, self.duts[i].comport)

        self.logger.debug("Initialized %d %s "
                          "for this testcase.", len(self.duts),
                          "dut" if len(self.duts) == 1 else "duts")

    def __get_nw_interface(self):
        """
        Get the capture pipe or sniffer interface.

        :return:
        """
        return self.__env['sniffer']['iface']

    def __required_sniffer(self):
        """
        Check if sniffer was requested for this run.

        :return: Boolean
        """
        required = self.args.use_sniffer
        self.logger.debug("%s" % "Required NW Sniffer" if required else "Skip Sniffing NW data")
        return required

    def __start_sniffer(self):
        """
        Start network sniffer capturing pcap to a file.

        :return: Nothing
        """
        from icetea_lib.wireshark import Wireshark
        # TODO: Replace hardcoded network log filename
        self.capture_file = LogManager.get_testcase_logfilename("network.nw.pcap")
        self.logger.debug('Start wireshark capture: %s', self.capture_file)
        self.wshark = Wireshark()

        # Add self.tshark_preferences to parameters
        # when pyshark starts supporting the -o tshark argument
        self.wshark.startCapture(self.__get_nw_interface(),
                                 self.capture_file,
                                 self.tshark_arguments)
        self.__sniffing = True

    def __stop_sniffer(self):
        """
        Stop the network sniffer.

        :return: Nothing
        """
        if self.__sniffing:
            self.logger.debug('Stop wireshark capture: %s', self.capture_file)
            packet_count = self.wshark.stopCapture()
            self.logger.debug("Got total %i NW packets", packet_count)

    def delay(self, seconds):
        """
        Sleep command

        :param seconds: Amount of seconds to sleep.
        :return: Nothing
        """
        self.logger.debug("Waiting for %i seconds", seconds)
        if seconds < 30:
            time.sleep(seconds)
        else:
            while seconds > 10:
                self.logger.debug("Still waiting... %i seconds remain", seconds)
                time.sleep(10)
                seconds = seconds - 10
            time.sleep(seconds)

    def wait_for_stable_network(self, delay=10):
        """
        Wait for network to stabilize by sleeping for delay seconds

        :param delay: seconds to sleep.
        :return: Nothing
        """
        self.delay(delay)

    def get_node_index_by_address(self, address, address_type):
        """
        Get node index by address

        :param address: addres whose index to get
        :param address_type: address type
        :return: Integer or None
        """
        for i in self.get_dut_range():
            dut_address = self.duts[i-1].mesh0['address'][address_type]
            if dut_address is not None and dut_address == address:
                return i
        return None

    def pause(self):  # pylint: disable=no-self-use
        """
        Pause test execution and continue after ENTER has been pressed.

        :return: Nothing
        """
        print("Press [ENTER] to continue")
        sys.stdin.readline().strip()

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
            for ind in self.get_dut_range():
                self.open_node_terminal(ind, wait)
            return

        if not self.is_my_dut(k):
            return

        params = '-serial '+self.duts[k-1].comport + ' -sercfg '+str(self.duts[k-1].serial_baudrate)

        putty_exe = self.__env['extApps']['puttyExe']
        if os.path.exists(self.__env['extApps']['kittyExe']):
            putty_exe = self.__env['extApps']['kittyExe']

        if "kitty.exe" in putty_exe:
            params = params+' -title "'+self.duts[k-1].comport

            params += ' - '+ self.get_test_name()
            params += ' | DUT'+str(k)+' '+self.get_dut_nick(k)+'"'
            params += ' -log "' + LogManager.get_testcase_logfilename('DUT%d.manual' % k) + '"'

        if os.path.exists(putty_exe):

            command = putty_exe+' '+params
            self.logger.info(command)
            if wait:
                if self.is_my_dut(k):
                    self.duts[k - 1].close_dut()
                    self.duts[k-1].close_connection()
                    self._resource_provider.allocator.release(dut=self.duts[k - 1])
                    process = subprocess.Popen(command)
                    time.sleep(2)
                    process.wait()
                    self.duts[k-1].open_dut()
            else:
                subprocess.Popen(command, close_fds=True)
        else:
            self.logger.warning('putty not exists in path: %s', putty_exe)

    def kill_process(self, apps_to_kill): #pylint: disable=no-self-use
        """
        Run taskkill /F /im <app> for apps in apps_to_kill

        :param apps_to_kill: list of apps to kill
        :return: Nothing
        """
        for app in apps_to_kill:
            os.system("taskkill /F /im " + app)

    def __set_failure(self, retcode, reason):
        """
        Set internal state to reflect failure of test

        :param retcode: return code
        :param reason: failure reason as string
        :return: Nothing
        """
        if self._resource_provider:
            if hasattr(self._resource_provider, "allocator"):
                # Check for backwards compatibility with older pyclient versions.
                if hasattr(self._resource_provider.allocator, "get_status"):
                    pr_reason = self._resource_provider.allocator.get_status()
                    if pr_reason:
                        reason = "{}. Other error: {}".format(pr_reason, reason)
                        retcode = ReturnCodes.RETCODE_FAIL_DUT_CONNECTION_FAIL
        if self.__retcode is None or self.__retcode == 0:
            self.__retcode = retcode
            self.__failreason = reason
            self.logger.error("Test Case fails because of: %s", reason)
        else:
            self.logger.info("another fail reasons: %s", reason)

    def _check_skip(self):
        """
        Check if tc should be skipped

        :return: Boolean
        """
        if not self.skip():
            return False

        info = self.skip_info()
        only_type = info.get('only_type')
        platforms = info.get('platforms', [])

        allowed = self.config["requirements"]["duts"]["*"].get("allowed_platforms", [])
        # validate platforms in allowed_platforms, otherwise no skip
        if allowed and platforms and not set(platforms).issubset(allowed):
            return False

        # skip tests by either only_type or platforms
        if only_type or platforms:
            for keys in self.config['requirements'].get('duts', {}):
                # skip tests by only_type
                type_expr = "type" in self.config['requirements']['duts'][keys] and \
                            self.config['requirements']['duts'][keys]["type"] == only_type
                if only_type and type_expr:
                    return True

                # skip test by platforms condition 1:
                plat_expr = "platform_name" in self.config['requirements']['duts'][keys] and \
                            self.config['requirements']['duts'][keys]["platform_name"] in platforms
                if platforms and plat_expr:
                    return True

        # no skip if neither only_type nor platforms is defined
        return False

    # run Test Bench and Test Case
    def run(self):  # pylint: disable=too-many-return-statements,too-many-branches
        """
        Main run loop for test case.

        :return: return code from Bench ReturnCodes.
        """
        # TODO: Refactor properly to get rid of too-many-return-statements and too-many-branches
        skip_case = self.args.skip_case

        try:
            result = self.__initialize()
            if not result:
                self.__set_failure(ReturnCodes.RETCODE_FAIL_INITIALIZE_BENCH,
                                   "Exception while initializing")
                return self.__prepare_exit()
            # Check skip here, since we now have the final configuration properly merged.
            skip = self._check_skip()
            if skip:
                self.logger.info("TC '%s' will be skipped because of '%s'", self.get_test_name(),
                                 (self.skip_reason()))
                result = self.get_result()
                result.set_verdict(verdict='skip', retcode=-1, duration=0)
                self.__retcode = -1
                self._result = result
                self.__set_failure(ReturnCodes.RETCODE_SKIP, self.skip_reason())
                return self.__prepare_exit()

        except Exception: #pylint: disable=broad-except
            #Disable broad exception warning, we want to catch all unhandled exceptions here.
            self.logger.error("Initialize causes exception", exc_info=True)
            self.__set_failure(ReturnCodes.RETCODE_FAIL_INITIALIZE_BENCH,
                               "Exception while initializing")
            return self.__prepare_exit()
        if self._integer_keys_found:
            self.logger.warning("Integer keys found in configuration for DUT requirements. "
                                "Keys forced to strings for this run. "
                                "Please update your DUT requirements keys to strings.")

        self.logger.info("Start Test case '%s'", self.get_test_name())

        if self.args.verbose:
            self.logger.info("Environment configurations:")
            self.logger.info(pformat(self.__env))
            self.logger.info("TC configurations:")
            self.logger.info(pformat(self.config))

        try:
            self.logger.info("====setUpTestBench====")
            self.__setup_bench()
        except EnvironmentError as err:
            self.logger.error("setUpBench Throw environment error",
                              exc_info=True if not self.args.silent else False)
            self.__teardown_bench()
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            return self.__prepare_exit()
        except TestStepTimeout as err:
            self.__teardown_bench()
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            return self.__prepare_exit()
        except TestStepFail as err:
            self.__teardown_bench()
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            return self.__prepare_exit()
        except NameError as err:
            self.logger.error("setUpBench Throw NameError exception")
            self.logger.error(err, exc_info=True if not self.args.silent else False)
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            self.__teardown_bench()
            return self.__prepare_exit()
        except (KeyboardInterrupt, SystemExit):
            # shut down tc directly
            self.logger.warning("Keyboard/SystemExit request - shut down TC")
            self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
            self.__teardown_bench()
            return self.__prepare_exit()
        except Exception as err: #pylint: disable=broad-except
            #Disable broad exception warning, we want to catch all unhandled exceptions here.
            self.logger.error("setUpBench Throw exception",
                              exc_info=True if not self.args.silent else False)
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            self.__teardown_bench()
            return self.__prepare_exit()

        if hasattr(self, 'rampUp'):
            self.logger.error("obsolete rampUp() in TC, please update it to setup()")
            self.setup = self.rampUp  # pylint: disable=no-member,W0201

        if hasattr(self, 'setUp'):
            self.logger.warning("obsolete setUp() in TC, please update it to setup()")
            self.setup = self.setUp  # pylint: disable=no-member,W0201

        if not self.args.skip_setup:
            if hasattr(self, 'setup'):
                try:
                    self.logger.info("------TC SET UP---------")
                    self.setup()
                except TestStepTimeout as err:
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    self.__teardown_bench()
                    return self.__prepare_exit()
                except TestStepFail as err:
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    skip_case = True
                except TestStepError as err:
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    self.__teardown_bench()
                    if not self.args.silent:
                        err.detailed_info()
                    return self.__prepare_exit()
                except InconclusiveError as err:
                    self.logger.error("Testcase setUp raised InconclusiveError.")
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_INCONCLUSIVE, str(err))
                    self.__teardown_bench()
                    return self.__prepare_exit()
                except KeyboardInterrupt:
                    self.logger.error("TC setUp aborted by user")
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
                    self.__teardown_bench()
                    return self.__prepare_exit()
                except Exception as err: #pylint: disable=broad-except
                    #Disable broad exception warning, we want to catch all unhandled exceptions here
                    self.logger.error("TC setUp Throw exception")
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    self.__teardown_bench()
                    return self.__prepare_exit()
        else:
            self.logger.info("Skip TC setUp")

        if not skip_case:
            self.logger.info("------TC START---------")
            try:
                self.case()  # pylint: disable=no-member
                self.__retcode = ReturnCodes.RETCODE_SUCCESS
            except TestStepTimeout as err:
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except TestStepFail as err:
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except TestStepError as err:
                self.logger.error(err, exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
                if not self.args.silent:
                    err.detailed_info()
            except InconclusiveError as err:
                self.logger.error("Testcase setUp raised InconclusiveError.")
                self.logger.error(err, exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_INCONCLUSIVE, str(err))
            except NameError as err:
                self.logger.error(err, exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except LookupError as err:
                self.logger.error(err, exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except ValueError as err:
                self.logger.error(err, exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except KeyboardInterrupt:
                self.logger.info("Test Case aborted by user")
                self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
            except Exception as err: #pylint: disable=broad-except
                #Disable broad exception warning, we want to catch all unhandled exceptions here.
                self.logger.error("case Throw exception",
                                  exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
                if not self.args.silent:
                    traceback.print_exc()

            self.logger.info("-----------TC END-----------")
            if self.__retcode == ReturnCodes.RETCODE_SUCCESS and \
                            self.__preliminary_verdict is not False:
                self.logger.debug("TC PASS")
            else:
                # TODO: CHECK THIS LOGIC
                self.logger.debug("TC FAIL")
                self.__set_failure(ReturnCodes.RETCODE_FAIL_UNKNOWN, "Unknown failure reason")
                self.logger.debug("Testcase failed due to unknown reason. "
                                  "Perhaps the exception causing the fail was caught?")
        else:
            self.logger.info("Skip TC case")

        if hasattr(self, 'rampDown'):
            self.logger.error("obsolete rampDown() in TC, please update it to teardown()")
            self.teardown = self.rampDown  # pylint: disable=no-member,W0201

        if hasattr(self, 'tearDown'):
            self.logger.warning("obsolete tearDown() in TC, please update it to teardown()")
            self.teardown = self.tearDown  # pylint: disable=no-member,W0201

        if not self.args.skip_teardown:
            if hasattr(self, 'teardown'):
                try:
                    self.logger.info("====TC TEAR DOWN====")
                    self.teardown()
                except TestStepTimeout as err:
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    self.__teardown_bench()
                    return self.__prepare_exit()
                except TestStepFail as err:
                    self.__teardown_bench()
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    return self.__prepare_exit()
                except TestStepError as err:
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__teardown_bench()
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    if not self.args.silent:
                        err.detailed_info()
                    return self.__prepare_exit()
                except InconclusiveError as err:
                    self.logger.error("Testcase setUp raised InconclusiveError.")
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_INCONCLUSIVE, str(err))
                    self.__teardown_bench()
                    return self.__prepare_exit()
                except KeyboardInterrupt:
                    self.logger.error("TC tearDown aborted by user")
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
                    self.__teardown_bench()
                    return self.__prepare_exit()
                except Exception as err: #pylint: disable=broad-except
                    #Disable broad exception warning, we want to catch all unhandled exceptions here
                    self.logger.error("tearDown Throw exception",
                                      exc_info=True if not self.args.silent else False)
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    if not self.args.silent:
                        traceback.print_exc()
                    self.__teardown_bench()
                    return self.__prepare_exit()
        else:
            self.logger.info("Skip TC tearDown")

        # end
        self.__teardown_bench()

        if self.args.putty:
            self.open_node_terminal('*', wait=False)

        retcode = self.__prepare_exit()
        return retcode

    def get_platforms(self):
        """
        Get list of dut platforms

        :return: list
        """
        plat_list = []
        for info in self._dutinformations:
            plat_list.append(info.platform)
        return plat_list

    def get_serialnumbers(self):
        """
        Get list of dut serial numbers

        :return: list
        """
        serial_number_list = []
        for info in self._dutinformations:
            serial_number_list.append(info.resource_id)
        return serial_number_list

    def __setup_bench(self):
        """
        Initialize test bench. Validate dut configurations, kill putty and kitty processes,
        load plugins, create empty Result object for this test case, initialize duts,
        collect metainformation from initialized duts, start sniffer, start test case timer,
        start external services and finally send pre-commands to duts.

        :return: Nothing
        """

        # Validate dut configurations
        Bench._validate_dut_configs(self.resource_configuration.get_dut_configuration(),
                                    self.logger)

        if self.args.kill_putty:
            self.logger.debug("Kill putty/kitty processes")
            self.kill_process(['kitty.exe', 'putty.exe'])

        self.__load_plugins()
        # Initialize tc result object.
        self._result = Result()
        if self.resource_configuration.count_duts() > 0:
            self.logger.info("====setUpTestBench====")

            # Initialize duts and collect information to result object.
            self.__init_duts()
            self._result.set_dutinformation(self._dutinformations)
            for _, serialnumber in zip(self.get_platforms(), self.get_serialnumbers()):
                self._result.dut_vendor.append('')
                self._result.dut_resource_id.append(serialnumber)
            self._result.dut_count = self.resource_configuration.count_duts()
            self._result.duts = self.resource_configuration.get_dut_configuration()
            if self.resource_configuration.count_hardware() > 0:
                self._result.dut_type = 'hw'
            elif self.resource_configuration.count_process() > 0:
                self._result.dut_type = 'process'

            self._starttime = time.time()

            if self.__required_sniffer():
                self.__start_sniffer()
        else:
            self.logger.debug("This TC doesn't use DUT's at all :o")
            self._dut_count = 0
            self._platforms = []
            self._serialnumbers = []
            self.dut_type = "unknown"
            self.__preliminary_verdict = True

        # Start External services/applications
        self.__start_external_services()
        self.__send_pre_commands(self.args.pre_cmds)

    def __send_pre_commands(self, cmds=""):
        """
        Send pre-commands to duts.

        :param cmds: Commands to send as string
        :return: Nothing
        """
        # Execute DUT-specific pre-commands
        for k, conf in enumerate(self.resource_configuration.get_dut_configuration()):
            pre = conf.get("pre_cmds")
            if pre:
                for cmd in pre:
                    self.execute_command(k+1, cmd)
        if cmds and cmds:
            if cmds.startswith('file:'):
                # @todo
                raise NotImplementedError('"--pre-cmds" -option with file not supported')
            else:
                self.execute_command('*', cmds)

    def __send_post_commands(self, cmds=""):
        """
        Send post commands to duts

        :param cmds: Commands to send as string.
        :return:
        """
        for k, conf in enumerate(self.resource_configuration.get_dut_configuration()):
            post = conf.get("post_cmds")
            if post:
                for cmd in post:
                    self.execute_command(k+1, cmd)
        if cmds and cmds:
            self.execute_command('*', cmds)

    def __teardown_bench(self):  # pylint: disable=too-many-branches
        """
        Tear down the Bench object.

        :return: Nothing
        """
        # TODO: Refactor to have less branches
        self.logger.info("====tearDownTestBench====")
        self.__send_post_commands(self.args.post_cmds)

        try:
            # try to close node's by nicely by `exit` command
            # if it didn't work, kill it by OS process kill command
            # also close reading threads if any
            self.logger.debug("Close node connections")
            if self.duts:
                for i in self.get_dut_range(-1):
                    if self.is_my_dut(i+1):
                        try:
                            self.duts[i].close_dut(use_prepare=True)
                            self.duts[i].close_connection()
                        except Exception as exc:  # pylint: disable=broad-except
                            # We want to catch all uncaught Exceptions here.
                            self.logger.error("Exception while closing dut %s!",
                                              self.duts[i].dut_name,
                                              exc_info=True if not self.args.silent else False)
                            self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_BENCH, str(exc))

                self.logger.debug("Close node threads")
                # finalize dut thread
                for i in self.get_dut_range(-1):
                    if self.is_my_dut(i+1):
                        while not self.duts[i].finished():
                            time.sleep(0.05)
                            print("not finished..")
        except KeyboardInterrupt:
            self.logger.debug("key interrupt")
            for i in self.get_dut_range(-1):
                if self.is_my_dut(i+1):
                    self.duts[i].kill_received = True

            self.logger.debug("delete duts")
            del self.duts

        if self.__required_sniffer():
            if hasattr(self, "wshark"):
                self.logger.debug("Close wshark pipes")
                import psutil
                from pkg_resources import parse_version

                # Note: the psutil has changed the API at around version 3.0 but user likely has
                # the older version installed unless it has specifically installed via pip.
                if parse_version(psutil.__version__) < parse_version('3.0.0'):
                    self.logger.warning("NOTE: your psutil version %s is likely too old,"
                                        " please update!", psutil.__version__)

                dumpcaps = []
                for process in self.wshark.liveLoggingCapture.running_processes:
                    children = psutil.Process(process.pid).children(recursive=True)
                    for child in children:
                        if child.name() in ('dumpcap', 'tshark-bin', 'dumpcap-bin'):
                            dumpcaps.append(child)
                self.__stop_sniffer()
                for child in dumpcaps:
                    try:
                        child.kill()
                        child.wait(timeout=2)
                    except (OSError, psutil.NoSuchProcess, psutil.TimeoutExpired):
                        pass

        self.logger.debug("Stop external services if any")
        self.__stop_external_services()

    def is_my_dut(self, k):
        """
        :return: Boolean
        """
        if self.args.my_duts:
            myduts = self.args.my_duts.split(',')
            if str(k) in myduts:
                return True
            return False
        else:
            return True

    def __wait_for_exec_ext_dut_cmd(self, k, command):
        """
        Wait for Enter to be pressed when dut has executed command.

        :param k: Dut to command
        :param command: command to send
        :return: Nothing
        :raises: EnvironmentError if command failed.
        """

        if self.args.pause_when_external_dut:
            nick = self.get_dut_nick(k)
            print("Press [ENTER] when %s execute command '%s'" % (nick, command))
            resp = sys.stdin.readline().strip()
            if resp != '':
                raise EnvironmentError("%s fail command" % nick)

    def get_dut_versions(self):
        """
        Get nname results and set them to duts.

        :return: Nothing
        """
        resps = self.command('*', "nname")
        for i, resp in enumerate(resps):
            self.duts[i].version = resp.parsed

    def get_dut_nick(self, dut_index):
        """
        Get nick of dut index k

        :param dut_index: index of dut
        :return: string
        """
        nick = str(dut_index)
        index_in_duts = dut_index in self.config["requirements"]["duts"]
        nick_in_indexed_reqs = "nick" in self.config["requirements"]["duts"][dut_index]
        if index_in_duts and nick_in_indexed_reqs:
            return self.config["requirements"]["duts"][dut_index]['nick']
        return nick

    def get_dut_index(self, nick):
        """
        Get index of dut with nickname nick

        :param nick: string
        :return: integer > 1
        """
        for dut_index, dut in enumerate(self.resource_configuration.get_dut_configuration()):
            nickname = dut.get("nick")
            if nickname and nickname == nick:
                return dut_index+1
        raise ValueError("Cannot find DUT by nick '%s'" % nick)

    def get_dut(self, k):
        """
        Get dut object

        :param k: index or nickname of dut.
        :return: Dut
        """
        dut_index = k
        if isinstance(k, str):
            dut_index = self.get_dut_index(k)

        if dut_index > len(self.duts) or dut_index < 1:
            self.logger.error("Invalid DUT number")
            raise ValueError("Invalid DUT number when calling get_dut(%i)" % (dut_index))

        return self.duts[dut_index-1]

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
        response is dummy
        :param report_cmd_fail: If True (default), exception is thrown on command execution error.
        :return: CliResponse object
        """
        ret = None
        if not report_cmd_fail:
            expected_retcode = None
        if k == '*':
            ret = self.__send_cmd_to_all(cmd, wait=wait, expected_retcode=expected_retcode,
                                         timeout=timeout, asynchronous=asynchronous,
                                         report_cmd_fail=report_cmd_fail)
        else:
            ret = self.__execute_command(k, cmd, wait=wait, expected_retcode=expected_retcode,
                                         timeout=timeout, asynchronous=asynchronous,
                                         report_cmd_fail=report_cmd_fail)
        return ret

    def wait_for_async_response(self, cmd, async_resp):
        """
        Wait for the given asynchronous response to be ready and then parse it.

        :param cmd: The asynchronous command that was sent to DUT.
        :param async_resp: The asynchronous response returned by the preceding command call.
        :return: CliResponse object
        """
        if not isinstance(async_resp, CliAsyncResponse):
            self.logger.error("Not an asynchronous response")
            raise AttributeError("%s is not an instance of CliAsyncResponse" % (async_resp))

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
            parsed = self._parser_manager.parse(cmd.split(' ')[0].strip(), resp)
            if parsed is not None:
                resp.parsed = parsed
                if parsed.keys():
                    self.logger.info(parsed)
        return resp

    # Private functions

    # send commands to all duts
    def __send_cmd_to_all(self, cmd, wait=True, expected_retcode=0, timeout=50, asynchronous=False,
                          report_cmd_fail=True):
        """
        Send command to all duts.

        :return: list of CliResponses
        """
        resps = []
        for i in self.get_dut_range():
            resps.append(
                self.__execute_command(i, cmd, wait=wait, expected_retcode=expected_retcode,
                                       timeout=timeout, asynchronous=asynchronous,
                                       report_cmd_fail=report_cmd_fail))
        return resps

    # internal command sender
    def __execute_command(self, k, cmd, wait=True, expected_retcode=0, timeout=50,
                          asynchronous=False, report_cmd_fail=True):
        """
        Internal command sender.
        """

        if isinstance(k, str):
            dut_index = self.get_dut_index(k)
            return self.__execute_command(dut_index, cmd, wait, expected_retcode, timeout,
                                          asynchronous, report_cmd_fail)

        if k > len(self.duts) or k < 1:
            self.logger.error("Invalid DUT number")
            raise ValueError("Invalid DUT number when calling executeCommand(%i)" % k)

        if not self.is_my_dut(k):
            self.__wait_for_exec_ext_dut_cmd(k, cmd)
            return CliResponse()

        try:
            #construct command object to be execute
            timestamp = time.time()
            req = CliRequest(cmd, timestamp=timestamp, wait=wait,
                             expected_retcode=expected_retcode, timeout=timeout,
                             asynchronous=asynchronous, dut_index=k)
            #execute command
            try:
                req.response = self.duts[k-1].execute_command(req)
            except (TestStepFail, TestStepError, TestStepTimeout) as error:
                if not report_cmd_fail:
                    self.logger.error("An error occured when executing command on dut %s", k)
                    self.logger.debug("reportCmdFail is set to False, don't raise.")
                    self.logger.error("Supressed error: %s", error)
                    if req.response is None:
                        req.response = CliResponse()
                else:
                    raise

            if wait and not asynchronous:
                # There should be valid responses
                if expected_retcode is not None:
                    # reconfigure preliminary verdict
                    # print only first failure
                    if self.__preliminary_verdict is None:
                        #init first preliminary when calling first time
                        self.__preliminary_verdict = req.response.retcode == req.expected_retcode
                        if self.__preliminary_verdict is False:
                            self.logger.warning("command fails - set preliminaryVerdict as FAIL")
                    elif req.response.retcode != req.expected_retcode:
                        if self.__preliminary_verdict is True:
                            #if any command fails, it mean that TC fails
                            self.__preliminary_verdict = False
                            self.logger.warning("command fails - set preliminaryVerdict as FAIL")
                    # Raise expection if command fails
                    if req.response.retcode != req.expected_retcode:
                        self.command_fail(req)
                # Parse response
                parsed = self._parser_manager.parse(cmd.split(' ')[0].strip(), req.response)
                if parsed is not None:
                    req.response.parsed = parsed
                    if parsed.keys():
                        self.logger.info(parsed)
            return req.response

        except (KeyboardInterrupt, SystemExit):
            # shut down tc directly
            self.logger.warning("Keyboard/SystemExit request - shut down TC")
            self.command_fail(CliRequest(), "Aborted by user")

    def __prepare_exit(self):
        """
        Prepare for exiting run.

        :return: ReturnCode
        """
        if self.__retcode is None:
            if self.__preliminary_verdict:
                self.__retcode = ReturnCodes.RETCODE_SUCCESS
            else:
                self.__retcode = ReturnCodes.RETCODE_FAIL_NO_PRELIMINARY_VERDICT
        self.logger.debug("retcode: %s, preliminaryVerdict: %s", self.__retcode,
                          self.__preliminary_verdict)
        if self.__retcode == ReturnCodes.RETCODE_SUCCESS and \
                        self.__preliminary_verdict is not False:
            self.logger.info("Test '%s' PASS", self.get_test_name())
        else:
            self.logger.warning("Test '%s' FAIL, reason: %s",
                                self.get_test_name(),
                                self.__failreason)
        return self.__retcode

    def command_fail(self, req, fail_reason=None):
        """
        Command has failed.

        :raises: TestStepTimeout if dut timed out. TestStepFail in other cases. NameError if
        fail_reason was given.
        """

        self.logger.error('Test step fails!')

        if fail_reason:
            raise NameError(fail_reason)
        if req.response:
            if req.response.lines:
                self.logger.debug("Last command response from D%s:", req.dut_index)
                self.logger.debug('\n'.join(req.response.lines))

            if req.response.timeout:
                raise TestStepTimeout("dut"+str(req.dut_index)+" TIMEOUT, cmd: '"+req.cmd+"'")
            else:
                reason = "dut"+str(req.dut_index) + " cmd: '"+req.cmd+"',"
                if req.response.retcode == -5:
                    reason += " unknown cmd"
                elif req.response.retcode == -2:
                    reason += " invalid params"
                elif req.response.retcode == -3:
                    reason += " not implemented"
                elif req.response.retcode == -4:
                    reason += " cb missing"
                else:
                    reason += "retcode: "+str(req.response.retcode)
                raise TestStepFail(reason)
        raise TestStepFail("command FAIL by unexpected reason")
