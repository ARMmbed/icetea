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

IceteaManager module. Contains IceteaManager class and some helpers.
IceteaManager is the handler of the entire run. It determines return codes
for the caller and handles processing of arguments as well as triggers the run with the
correct parameters etc.
"""

# Ignore "Use % formatting in logging functions and pass the % parameters as arguments"
# Also ignore "class has no __init__ method" and "Too few public methods" warnings
# Disable Old-style class warning and "Unnecessary parens after 'print' kwd" warning
# pylint: disable=W1202,W0232,R0903,C1001,C0325

import json
import sys
import shutil
import os
import six

import icetea_lib.LogManager as LogManager
from icetea_lib.ResourceProvider.ResourceProvider import ResourceProvider
from icetea_lib.TestSuite.TestSuite import TestSuite, SuiteException
from icetea_lib.TestSuite.TestcaseContainer import TestStatus
from icetea_lib.ResultList import ResultList
from icetea_lib.arguments import get_base_arguments, get_parser, get_tc_arguments
from icetea_lib.tools.tools import Singleton, get_fw_version
from icetea_lib.cloud import Cloud
from icetea_lib.Plugin.PluginManager import PluginManager


def _clean_onerror(func, path, excinfo):
    """
    Error handler for cleaner
    """
    print("%s encountered error when processing %s: %s" % (func, path, excinfo))


def _cleanlogs(silent=False, log_location="log"):
    """
    Cleans up Mbed-test default log directory.

    :param silent: Defaults to False
    :param log_location: Location of log files, defaults to "log"
    :return: Nothing
    """
    try:
        print("cleaning up Icetea log directory.")
        shutil.rmtree(log_location, ignore_errors=silent,
                      onerror=None if silent else _clean_onerror)
    except OSError as error:
        print(error)


class ExitCodes:
    """
    Console exit codes
    """
    EXIT_SUCCESS = 0
    EXIT_ERROR = 1
    EXIT_FAIL = 2
    EXIT_INCONC = 3


@six.add_metaclass(Singleton)
class TCMetaSchema(object):
    """
    Singleton metadata schema object.
    """
    __metaclass__ = Singleton

    def __init__(self, libpath="./icetea_lib"):
        with open(os.path.join(libpath, 'tc_schema.json')) as data_file:
            self._tc_meta_schema = json.load(data_file)

    def get_meta_schema(self):
        """
        Getter for tc meta schema.

        :return: tc_meta_schema
        """
        return self._tc_meta_schema


class IceteaManager(object):
    """
    IceteaManager class. This is the master of the entire run. The primary entry point into
    execution is the run method.
    """
    def __init__(self):
        """
        Constructor for IceteaManager. Appends libraries to sys.path, loads the test case
        metadata schema, parses arguments and initializes logging.
        """
        self.libpath = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
        sys.path.append(self.libpath)
        libpath2 = os.sep.join(self.libpath.split(os.sep)[:-1])
        sys.path.append(libpath2)
        # Initialize TCMetaSchema with correct libpath
        TCMetaSchema(self.libpath)
        self.args, self.unknown = IceteaManager._parse_arguments()
        # If called with --clean, clean up logs.
        if self.args.clean:
            _cleanlogs(silent=self.args.silent, log_location=self.args.log)

        LogManager.init_base_logging(self.args.log, verbose=self.args.verbose,
                                     silent=self.args.silent, color=self.args.color,
                                     no_file=(self.args.list or self.args.listsuites),
                                     truncate=not self.args.disable_log_truncate)

        self.logger = LogManager.get_logger("icetea")
        self.pluginmanager = None
        self.resourceprovider = ResourceProvider(self.args)
        self._init_pluginmanager()
        self.resourceprovider.set_pluginmanager(self.pluginmanager)

    @staticmethod
    def list_suites(suitedir="./testcases/suites", cloud=False):
        """
        Static method for listing suites from both local source and cloud.
        Uses PrettyTable to generate the table.

        :param suitedir: Local directory for suites.
        :param cloud: cloud module
        :return: PrettyTable object or None if no test cases were found
        """
        suites = []
        suites.extend(TestSuite.get_suite_files(suitedir))

        # no suitedir, or no suites -> append cloud.get_campaigns()

        if cloud:
            names = cloud.get_campaign_names()
            if names:
                suites.append("------------------------------------")
                suites.append("FROM CLOUD:")
                suites.extend(names)
        if not suites:
            return None

        from prettytable import PrettyTable
        table = PrettyTable(["Testcase suites"])
        for suite in suites:
            table.add_row([suite])
        return table

    @staticmethod
    def _parse_arguments():
        """
        Static method for paring arguments
        """
        parser = get_base_arguments(get_parser())
        parser = get_tc_arguments(parser)
        args, unknown = parser.parse_known_args()
        return args, unknown

    def check_args(self):
        """
        Validates that a valid number of arguments were received and that all arguments were
        recognised.

        :return: True or False.
        """
        parser = get_base_arguments(get_parser())
        parser = get_tc_arguments(parser)
        # Disable "Do not use len(SEQ) as condition value"
        # pylint: disable=C1801
        if len(sys.argv) < 2:
            self.logger.error("Icetea called with no arguments! ")
            parser.print_help()
            return False
        elif not self.args.ignore_invalid_params and self.unknown:
            self.logger.error("Unknown parameters received, exiting. "
                              "To ignore this add --ignore_invalid_params flag.")
            self.logger.error("Following parameters were unknown: {}".format(self.unknown))
            parser.print_help()
            return False
        return True

    def _init_pluginmanager(self):
        """
        Initialize PluginManager and load run wide plugins.
        """
        self.pluginmanager = PluginManager(logger=self.logger)
        self.logger.debug("Registering execution wide plugins:")
        self.pluginmanager.load_default_run_plugins()
        self.pluginmanager.load_custom_run_plugins(self.args.plugin_path)
        self.logger.debug("Execution wide plugins loaded and registered.")

    def run(self, args=None):
        """
        Runs the set of tests within the given path.
        """
        # Disable "Too many branches" and "Too many return statemets" warnings
        # pylint: disable=R0912,R0911
        retcodesummary = ExitCodes.EXIT_SUCCESS
        self.args = args if args else self.args

        if not self.check_args():
            return retcodesummary

        if self.args.clean:
            if not self.args.tc and not self.args.suite:
                return retcodesummary

        # If called with --version print version and exit
        version = get_fw_version()
        if self.args.version and version:
            print(version)
            return retcodesummary
        elif self.args.version and not version:
            print("Unable to get version. Have you installed Icetea correctly?")
            return retcodesummary

        self.logger.info("Using Icetea version {}".format(version) if version
                         else "Unable to get Icetea version. Is Icetea installed?")

        # If cloud set, import cloud, get parameters from environment, initialize cloud
        cloud = self._init_cloud(self.args.cloud)

        # Check if called with listsuites. If so, print out suites either from cloud or from local
        if self.args.listsuites:
            table = self.list_suites(self.args.suitedir, cloud)
            if table is None:
                self.logger.error("No suites found!")
                retcodesummary = ExitCodes.EXIT_FAIL
            else:
                print(table)
            return retcodesummary

        try:
            testsuite = TestSuite(logger=self.logger, cloud_module=cloud, args=self.args)
        except SuiteException as error:
            self.logger.error("Something went wrong in suite creation! {}".format(error))
            retcodesummary = ExitCodes.EXIT_INCONC
            return retcodesummary

        if self.args.list:
            if self.args.cloud:
                testsuite.update_testcases()
            testcases = testsuite.list_testcases()
            print(testcases)
            return retcodesummary

        results = self.runtestsuite(testsuite=testsuite)

        if not results:
            retcodesummary = ExitCodes.EXIT_SUCCESS
        elif results.failure_count() and self.args.failure_return_value is True:
            retcodesummary = ExitCodes.EXIT_FAIL
        elif results.inconclusive_count() and self.args.failure_return_value is True:
            retcodesummary = ExitCodes.EXIT_INCONC

        return retcodesummary

    def runtestsuite(self, testsuite):
        """
        Runs a single test suite

        :param testsuite: TestSuite
        :return: ResultList
        """
        if testsuite.status == TestStatus.READY:
            results = testsuite.run()
        else:
            results = ResultList()
        # Disable "Expression is assigned to nothing" warning
        # pylint: disable=W0106
        [handler.flush() for handler in self.logger.handlers]
        results.save(heads={'Build': '', 'Branch': self.args.branch})
        sys.stdout.flush()
        self._cleanup_resourceprovider()
        return results

    # Disable "String statement has no effect" warning
    # pylint: disable=W0105
    """
        PRIVATE FUNCTIONS HERE
    """

    def _cleanup_resourceprovider(self):
        """
        Calls cleanup for ResourceProvider of this run.

        :return: Nothing
        """
        # Disable too broad exception warning
        # pylint: disable=W0703
        self.resourceprovider = ResourceProvider(self.args)
        try:
            self.resourceprovider.cleanup()
            self.logger.info("Cleanup done.")
        except Exception as error:
            self.logger.error("Cleanup failed! %s", error)

    def _init_cloud(self, cloud_arg):
        """
        Initializes Cloud module if cloud_arg is set.

        :param cloud_arg: taken from args.cloud
        :return: cloud module object instance
        """
        # Disable too broad exception warning
        # pylint: disable=W0703
        cloud = None
        if cloud_arg:
            try:
                if hasattr(self.args, "cm"):
                    cloud_module = self.args.cm if self.args.cm else None
                    self.logger.info("Creating cloud module {}.".format(cloud_module))
                else:
                    cloud_module = None

                cloud = Cloud(host=None, module=cloud_module, logger=self.logger, args=self.args)
            except Exception as error:
                self.logger.warning("Cloud module could not be initialized: {}".format(error))
                cloud = None
        return cloud
