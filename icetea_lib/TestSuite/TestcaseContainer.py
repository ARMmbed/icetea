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

Testcase container class for TestSuite.
"""

import datetime
import traceback
import gc
import time
from inspect import isclass


from jsonschema import validate, ValidationError, SchemaError
from six import iteritems
from jsonmerge import merge
import semver

import icetea_lib.LogManager as LogManager
from icetea_lib.ReturnCodes import ReturnCodes
from icetea_lib.tools.tools import get_fw_version, import_module, load_class
from icetea_lib.arguments import get_parser, get_tc_arguments, get_base_arguments
from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList

# pylint: disable=too-many-arguments,useless-super-delegation,too-many-branches,too-many-statements
# pylint: disable=too-many-instance-attributes,protected-access


class TestStatus(object):  # pylint: disable=no-init,too-few-public-methods
    """
    Enumeration for test statuses.
    """
    PENDING = 4
    PREPARED = 3
    READY = 2
    RUNNING = 1
    FINISHED = 0


class TestcaseContainer(object):
    """
    Container for a single test case.
    """
    def __init__(self, logger=None):
        self.logger = logger
        self.status = None
        self.tcname = None
        self._instance = None
        self._modulename = None
        self._moduleroot = None
        self._final_configuration = {}
        self._meta_schema = None
        self._result = None
        self._filepath = None
        self._suiteconfig = {}
        self._infodict = {}
        if not logger:
            import logging
            self.logger = logging.getLogger("TCContainer")
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())
                self.logger.setLevel(logging.INFO)

    @staticmethod
    def find_testcases(modulename, moduleroot, tc_meta_schema, path=None, suiteconfig=None,
                       logger=None):
        """
        Static method for generating a list of TestcaseContainer objects from a module.

        :param modulename: Name of module to parse
        :param moduleroot: module root
        :param tc_meta_schema: Schema to use in validation
        :param path: Path to module file
        :param suiteconfig: Optional configuration dictionary from suite
        :param logger: Logger
        :return: list of TestcaseContainer instances
        """
        if not isinstance(modulename, str):
            raise TypeError("modulename should be a string")

        if len(modulename) == 0:  # pylint: disable=len-as-condition
            raise ValueError("modulename shouldn't be empty")

        # Try to import the module.
        try:
            module = import_module(modulename)
        except Exception as error:
            if logger:
                logger.debug("Error while importing module {}: {}".format(modulename, error))
            raise ImportError("Error importing module {}: {}".format(modulename, error))

        tclist = []

        for test_class_name, test_class in iteritems(module.__dict__):
            if not isclass(test_class):
                continue
            # if a class as the constant flag IS_TEST set to true or is named Testcase,
            # fulfill test description and add it to the list
            if getattr(test_class, "IS_TEST", False) or test_class_name == "Testcase":
                testcase = TestcaseContainer(logger=logger)
                test_case = test_class()
                testcase.generate_members(modulename, test_case, moduleroot, path,
                                          tc_meta_schema, test_class_name, suiteconfig)
                tclist.append(testcase)
        return tclist

    def __copy__(self):
        cont = TestcaseContainer.find_testcases(self._modulename, self._moduleroot,
                                                self._meta_schema, self._filepath,
                                                self._suiteconfig, self.logger)
        for testcase in cont:
            if self.tcname == testcase.tcname:
                return testcase
        return None

    def generate_members(self, modulename, tc_instance, moduleroot, path, meta_schema,
                         test_class_name, suiteconfig=None):
        """
        Setter and generator for internal variables.

        :param modulename: Name of the module
        :param tc_instance: Bench instance
        :param moduleroot: Root folder of the module
        :param path:  Path to module file
        :param meta_schema: Schema used for Validation
        :param test_class_name: Name of the class
        :param suiteconfig: Optional configuration dictionary from suite
        :return: Nothing, modifies objects content in place
        """
        self._modulename = modulename
        self.tcname = tc_instance.test_name
        self.status = TestStatus.PENDING
        self._instance = tc_instance
        self._final_configuration = {}
        self._moduleroot = moduleroot
        self._meta_schema = meta_schema
        self._result = None
        self._filepath = path
        self._suiteconfig = suiteconfig if suiteconfig else {}

        if tc_instance.get_test_component():
            comp = tc_instance.get_test_component()
        else:
            comp = ["None"]
        if tc_instance.get_features_under_test():
            feat = tc_instance.get_features_under_test()
        else:
            feat = ''
        if tc_instance.get_allowed_platforms():
            platforms = tc_instance.get_allowed_platforms()
        else:
            platforms = ''
        self._infodict = {
            'name': self.tcname,
            'path': modulename + "." + test_class_name,
            'status': tc_instance.status() if tc_instance.status() else '',
            'type': tc_instance.type() if tc_instance.type() else '',
            'subtype': tc_instance.subtype() if tc_instance.subtype() else '',
            'group': moduleroot,
            'file': self._filepath,  # path to the file which hold this test
            'comp': comp,
            'feature': feat,
            'allowed_platforms': platforms,
            'fail': ''
        }

    def get_infodict(self):
        """
        Getter for internal infodict variable.

        :return: dict
        """
        return self._infodict

    def get(self, field):
        """
        Gets value of property/configuration field.

        :param field: Name of configuration property to get
        :return: Value of configuration property field. None if not found.
        """
        return self.get_instance().config.get(field)

    def get_instance_config(self):
        """
        Get configuration currently set into the test instance.
        :return: dict
        """
        config = self.get_instance().config
        config["filepath"] = self._filepath
        return config

    def get_final_config(self):
        """
        Getter for final configuration of the test case from the _final_configuration variable.

        :return: dict
        """
        return self._final_configuration

    def get_suiteconfig(self):
        """
        Getter for the internal _suiteconfig variable.

        :return: dict
        """
        return self._suiteconfig

    def get_instance(self):
        """
        Getter for testcase Bench instance. If instance does not exist, it will be created.

        :return: Bench instance of this testcase.
        """
        return self._instance

    def get_result(self):
        """
        Get the internal Result object.

        :return: Result
        """
        return self._result

    def get_name(self):
        """
        Get the test case name.

        :return: str
        """
        return self.tcname

    def merge_tc_config(self, conf_to_merge):
        """
        Merges testcase configuration with dictionary conf_to_merge.

        :param conf_to_merge: Dictionary of configuration to
        merge with testcase default configuration
        :return: Nothing
        """
        self._final_configuration = merge(self._final_configuration, conf_to_merge)

    def set_suiteconfig(self, config):
        """
        Setter for suite config.

        :param config: dict
        :return: Nothing
        """
        self._suiteconfig = config

    def set_result(self, result):
        """
        Setter for result object.

        :param result: Result
        :return: Nothing
        """
        self._result = result

    def set_final_config(self):
        """
        Sets configuration for testcase instance from self._final_configuration field.
        """
        if self._instance:
            self._instance.set_config(self._final_configuration)

    def validate_tc_instance(self):
        """
        Validates this testcase instance metadata and fetches the tc configuration.

        :return Nothing
        :raises SyntaxError
        """
        if not self.validate_testcase_metadata(self.get_instance()):
            raise SyntaxError("Invalid TC metadata")
        self._final_configuration = self.get_instance().get_config()

    def validate_testcase_metadata(self, testcase):
        """
        Validate tc metadata. Returns True if validation succeeds or False if if fails.

        :param testcase: Bench
        :return: Boolean
        """
        try:
            validate(testcase.config, self._meta_schema)
        except ValidationError as err:
            self.logger.error("Metadata validation failed! Please fix your TC Metadata!")
            self.logger.debug(testcase.config)
            self.logger.error(err)
            return False
        except SchemaError as err:
            self.logger.error("Schema error")
            self.logger.error(err)
            return False
        return True

    def run(self, forceflash=False):
        """
        Runs the testcase associated with this container.

        :param forceflash: boolean, True if forceflash should be used
        :return: Result
        """
        if self.status == TestStatus.FINISHED:
            self.logger.debug("Creating new bench instance for repeat.")
            self._instance = self._create_new_bench_instance(self._modulename)
            self.set_final_config()
        self.status = TestStatus.RUNNING
        self.logger.debug("Starting test case %s", self.tcname)
        tc_instance = self.get_instance()

        result = self._check_skip(tc_instance)
        if result:
            self.logger.debug("Skipping test case %s", self.tcname)
            self._result = result
            self.status = TestStatus.FINISHED
            return result

        # Check if version checking is enabled in cli
        # and if the bench has the compatible key in it's config.
        result = self._check_version(tc_instance)
        if result is not None:
            self.logger.debug("Version check triggered, skipping test case %s", self.tcname)
            self._result = result
            self.status = TestStatus.FINISHED
            return result

        parser = get_tc_arguments(get_base_arguments(get_parser()))
        args, unknown = parser.parse_known_args()
        if unknown:
            for para in unknown:
                self.logger.warning("Icetea received unknown parameter %s", para)
            if not args.ignore_invalid_params:
                self.logger.error(
                    "Unknown parameters received, exiting. To ignore this add "
                    "--ignore_invalid_params flag.")
                parser.print_help()
                result = tc_instance.get_result()
                result.set_verdict(verdict="inconclusive", retcode=-1, duration=0)
                self.status = TestStatus.FINISHED
                return result

        args.forceflash = forceflash
        self.status = TestStatus.RUNNING
        tc_instance.args = args
        self.logger.info("")
        self.logger.info("START TEST CASE EXECUTION: '%s'", tc_instance.test_name)
        self.logger.info("")

        start_time = datetime.datetime.now()
        try:
            retcode = tc_instance.run()
            self.logger.debug("Test bench returned return code %d", retcode)
        except:  # pylint: disable=bare-except
            traceback.print_exc()
            retcode = -9999

        stop_time = datetime.datetime.now()

        if tc_instance.results:
            result = tc_instance.results
        else:
            result = tc_instance.get_result(tc_file=self._filepath)

        # Force garbage collection

        # cleanup Testcase
        tc_instance = None
        gc.collect()
        LogManager.finish_testcase_logging()
        self.status = TestStatus.FINISHED

        if isinstance(result, ResultList):
            self.logger.debug("Received a list of results from test bench.")
            return result

        if result.retcode == ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER:
            print("Press CTRL + C again if you want to abort test run")
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                self.status = TestStatus.FINISHED
                raise

        total_duration = stop_time - start_time
        duration = total_duration.total_seconds()
        self.logger.debug("Duration: %d seconds", duration)

        verdict = None
        if retcode == 0:
            verdict = "pass"
        elif retcode in ReturnCodes.INCONCLUSIVE_RETCODES:
            verdict = "inconclusive"
        elif retcode == ReturnCodes.RETCODE_SKIP:
            verdict = "skip"
        else:
            verdict = "fail"
        result.set_verdict(
            verdict=verdict,
            retcode=retcode,
            duration=duration)
        self._result = result

        return result

    def _create_new_bench_instance(self, modulename):
        """
        Create a new Bench instance of this test for repeat and retry purposes.

        :param modulename: Name of the original module.
        :return: Bench or None
        """
        module = import_module(modulename)

        for test_class_name, test_class in iteritems(module.__dict__):
            if not isclass(test_class):
                continue
            if getattr(test_class, "IS_TEST", False) is True or test_class_name == "Testcase":
                inst = test_class()
                if inst.test_name == self.tcname:
                    return inst
                else:
                    continue
        return None

    def _load_testcase(self, modulename, verbose=False):  # pylint: disable=no-self-use
        """
        :param modulename: testcase to be loaded
        :param verbose: print exceptions when loading class
        :return: testcase instance
        :raises TypeError exception when modulename is not string
        :raises ImportError exception when cannot load testcase
        """
        if not isinstance(modulename, str):
            raise TypeError("Error, runTest: modulename not a string.")
        try:
            module = load_class(modulename, verbose)
        except ValueError as error:
            raise ImportError("Error, load_testcase: loadClass raised ValueError: {}".format(error))

        if module is None:
            raise ImportError("Error, runTest: "
                              "loadClass returned NoneType for modulename: %s" % modulename)

        return module()

    def _check_skip(self, tc_instance):
        """
        Check if this tc should be skipped according to the configuration.

        :param tc_instance: Bench
        :return: False if no skip is needed, Result with the skip set otherwise.
        """
        # Skip the TC IF NOT defined on the command line
        if tc_instance.skip():
            info = tc_instance.skip_info()
            if info.get('only_type') or info.get('platforms'):
                # only_type cannot be properly checked here, se we proceed
                # and check the final configuration in Bench.
                return False
            self.logger.info("TC '%s' will be skipped because of '%s'", tc_instance.get_test_name(),
                             tc_instance.skip_reason())
            result = tc_instance.get_result()
            result.set_verdict(verdict='skip', retcode=-1, duration=0)
            del tc_instance
            self._result = result
            return result
        return False

    def _check_major_version(self, fw_version, version_string):  # pylint: disable=no-self-use
        """
        Check if major version matches.

        :param fw_version: semver string
        :param version_string: semver string
        :return: Boolean
        """
        if int(fw_version[0]) > 0 and version_string[0] == '0':
            return False
        elif int(fw_version[0]) > 0 and version_string[1] == '0':
            return False
        elif int(fw_version[0]) > 0 and version_string[2] == '0':
            return False
        return True

    def _check_version(self, tc_instance):
        """
        Check if version number is compatible with this version of Icetea.

        :param tc_instance: Bench
        :return: None or Result.
        """
        if tc_instance.config.get(
                "compatible") and tc_instance.config['compatible']['framework']['name']:
            framework = tc_instance.config['compatible']['framework']
            # Check if version requirement is available
            # and that the testcase is meant for this framework
            if framework['version'] and framework['name'] == "Icetea":
                ver_str = framework['version']
                fw_version = get_fw_version()
                try:
                    if not self._check_major_version(fw_version, ver_str):
                        result = self._wrong_version(tc_instance, ver_str,
                                                     "Testcase not suitable for version >1.0.0. "
                                                     "Please install Icetea {}".format(ver_str))
                        return result
                except ValueError:
                    # Unable to convert fw_version to integer, let's just proceed.
                    return None
                if ver_str[0].isdigit():
                    return self._wrong_version(
                        tc_instance, ver_str) if fw_version != ver_str else None

                # Handle case where the version is a version number without comparison operators
                if not semver.match(fw_version, ver_str):
                    result = self._wrong_version(tc_instance, ver_str)
                    return result
            return None
        else:
            return None

    def _wrong_version(self, tc_instance, ver_str, msg=None):
        """
        Helper for constructing a Result object for version checking.

        :param tc_instance: Bench, del is called for this before returning.
        :param ver_str: semver string.
        :param msg: message.
        :return: Result
        """
        msg = msg if msg else "Version {} of Icetea required".format(ver_str)
        self.logger.info("TC '%s' will be skipped because of '%s'", tc_instance.get_test_name(),
                         msg)
        result = tc_instance.get_result()
        result.skip_reason = msg
        result.set_verdict(verdict='skip', retcode=-1, duration=0)
        del tc_instance
        return result


class DummyContainer(TestcaseContainer):
    """
    Class DummyContainer

    subclasses TestcaseContainer, acts as a dummy object for listing test cases
    that were not found when importing test cases.

    """

    def __init__(self, logger=None):
        """
        Just initialize the super class.

        :param logger: logger to use.
        """
        super(DummyContainer, self).__init__(logger)

    @staticmethod
    def find_testcases(modulename, moduleroot, tc_meta_schema, path=None, suiteconfig=None,
                       logger=None):
        """
        Static method find_testcases. Returns a DummyContainer with attributes collected from
        function params.
        """
        dummycontainer = DummyContainer(logger)
        dummycontainer.tcname = modulename
        dummycontainer._modulename = modulename
        dummycontainer.status = TestStatus.PENDING
        dummycontainer._instance = None
        dummycontainer._final_configuration = {}
        dummycontainer._moduleroot = moduleroot
        dummycontainer._meta_schema = tc_meta_schema
        dummycontainer._result = None
        dummycontainer._filepath = path
        dummycontainer._suiteconfig = suiteconfig if suiteconfig else {}
        return dummycontainer

    def run(self, forceflash=False):
        """
        Just returns the Result object for this Dummy.
        """
        return self._result

    def get(self, field):
        return None

    def set_final_config(self):
        pass

    def set_result_verdict(self, reason):
        """
        Sets the inconclusive verdict for this DummyContainer with reason reason.

        :param reason: String reason for why this dummy exists.
        :return: Nothing
        """
        if not self._result:
            self._result = Result()

        self._result.set_verdict(verdict="inconclusive",
                                 retcode=ReturnCodes.RETCODE_FAIL_INCONCLUSIVE,
                                 duration=0)
        self._result.tc_metadata["name"] = self.tcname
        self._result.fail_reason = reason

    def validate_tc_instance(self):
        return True
