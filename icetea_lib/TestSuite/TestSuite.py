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

import json
import os
import sys

from icetea_lib.ResultList import ResultList
from icetea_lib.TestSuite.TestcaseContainer import TestStatus, DummyContainer
from icetea_lib.TestSuite.TestcaseList import TestcaseList
from icetea_lib.TestSuite.TestcaseFilter import TestcaseFilter


class SuiteException(Exception):
    """
    Raised when something goes wrong with suite creation
    or other operations performed here.
    """
    pass


class TestSuite(object):
    def __init__(self, logger=None, cloud_module=None, args=None):
        self.logger = logger
        if logger is None:
            import logging
            self.logger = logging.getLogger("TestSuite")
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())
                self.logger.setLevel(logging.INFO)
        self.args = args
        self.cloud_module = cloud_module
        self._testcases = []
        self._default_configs = {}
        self.status = TestStatus.PENDING
        self._results = ResultList()
        self._create_tc_list()

    def __len__(self):
        return len(self._testcases)

    def get_testcases(self):
        """
        Return internal list of TestcaseContainers
        """
        return self._testcases

    def get_tcnames(self):
        """
        Return list of names of all test cases in this Suite.

        :return: list
        """
        return [tc.get_name() for tc in self._testcases]

    def run(self):
        """
        Test runner
        """
        self.status = TestStatus.RUNNING
        self.logger.info("Starting suite.")
        i = 0
        repeats = int(self.args.repeat) if self.args.repeat and int(self.args.repeat) >= 2 else 1
        repeat = 1
        self.logger.debug("Test suite repeats: %i", repeats)
        while repeat <= repeats:

            self.logger.info("Starting repeat %i of %i", repeat, repeats)
            repeat += 1
            for test in self._testcases:
                self.logger.debug("Starting next test case: %s", test.get_name())
                iterations = self.get_default_configs().get('iteration', 1)
                if iterations == 0:
                    continue
                iteration = 0
                while iteration < iterations:
                    self.logger.info("Iteration %i of %i", iteration + 1, iterations)
                    retries = self.get_default_configs().get("retryCount", 0)
                    self.logger.debug("Test case retries: %i", retries)
                    retryreason = self.get_default_configs().get("retryReason", "inconclusive")
                    iteration += 1
                    if self.args.forceflash_once:
                        self.args.forceflash = i == 0
                        self.logger.debug("Forceflash_once set: Forceflash is %s",
                                          self.args.forceflash)
                        i += 1
                    result, retries, repeat, iteration = self._run_testcase(test, retries,
                                                                            repeat,
                                                                            repeats,
                                                                            iteration,
                                                                            iterations,
                                                                            retryreason)
                    if result:
                        self._upload_result(result)
                if result and result.get_verdict() != 'pass' and self.args.stop_on_failure:
                    break
        self.status = TestStatus.FINISHED
        i += 1
        return self._results

    def _run_testcase(self, test, retries, repeat, repeats, iteration, iterations, retryreason):
        """
        Internal runner for handling a single test case run in the suite.
        Repeats and iterations are handled outside this function.

        :param test: TestcaseContainer to be run
        :param retries: Amount of retries desired
        :param repeat: Current repeat index
        :param repeats: Total amount of repeats
        :param iteration: Current iteration index
        :param iterations: Total number of iterations
        :param retryreason: suite related parameter for which test verdicts to retry.
        :return: (Result, retries(int), repeat(int), iteration(int))
        """
        result = None
        while True:
            try:
                self.logger.debug("Starting test case run.")
                result = test.run(forceflash=self.args.forceflash)
                result.retries_left = retries
            except KeyboardInterrupt:
                self.logger.info("User aborted test run")
                iteration = iterations
                repeat = repeats + 1
                break
            if result is not None:
                # Test had required attributes and ran succesfully or was skipped.
                # Note that a fail *during* a testcase run will still be reported.
                self._results.append(result)
                self._build_result_metainfo(result)
                if self.args.stop_on_failure and result.get_verdict() != 'pass':
                    # Stopping run on failure,
                    self.logger.info("Test case %s failed or was inconclusive, "
                                     "stopping run.\n", test.get_name())
                    repeat = repeats + 1
                    iteration = iterations + 1
                    break
                if result.get_verdict() == 'pass':
                    self.logger.info("Test case %s passed.\n", test.get_name())
                    break
                if result.get_verdict() == 'skip':
                    iteration = iterations
                    result.retries_left = 0
                    self.logger.info("Test case %s skipped.\n", test.get_name())
                    break
                elif retries > 0:
                    if retryreason == "includeFailures" or (retryreason == "inconclusive"
                                                            and result.inconclusive):
                        self.logger.error("Testcase %s failed, %d "
                                          "retries left.\n", test.get_name(), retries)
                        retries -= 1
                        self._upload_result(result)
                        continue
                    else:
                        result.retries_left = 0
                        break
                else:
                    self.logger.error("Test case %s failed, No retries left.\n",
                                      test.get_name())
                    break
        return result, retries, repeat, iteration

    def _build_result_metainfo(self, result):
        if hasattr(self, "args"):
            if hasattr(self.args, "branch") and self.args.branch:
                result.build_branch = self.args.branch
            if hasattr(self.args, "commitId") and self.args.commitId:
                result.buildcommit = self.args.commitId
            if hasattr(self.args, "gitUrl") and self.args.gitUrl:
                result.build_git_url = self.args.gitUrl
            if hasattr(self.args, "buildUrl") and self.args.buildUrl:
                result.build_url = self.args.buildUrl
            if hasattr(self.args, "campaign") and self.args.campaign:
                result.campaign = self.args.campaign
            if hasattr(self.args, "jobId") and self.args.jobId:
                result.job_id = self.args.jobId
            if hasattr(self.args, "toolchain") and self.args.toolchain:
                result.toolchain = self.args.toolchain
            if hasattr(self.args, "buildDate") and self.args.buildDate:
                result.build_date = self.args.buildDate

    def _upload_result(self, result):
        """
        Upload result to cloud.

        :param result: Result object
        :return: Nothing
        """
        if self.cloud_module:
            self.logger.debug("Uploading results to DB.")
            response_data = self.cloud_module.send_result(result)
            if response_data:
                data = response_data
                self.logger.info("Results sent to the server. ID: %s", data.get('_id'))


    def get_default_configs(self):
        """
        Get suite default configs
        """
        return self._default_configs

    def get_results(self):
        """
        Return results
        """
        return self._results

    def list_testcases(self):
        """
        List all test cases in this Suite in a neat table.

        :return: PrettyTable
        """
        testcases = []
        try:
            if self.args.json:
                self._create_json_objects(testcases)
                return json.dumps(testcases)
            else:
                self._create_rows_for_table(testcases)
                from prettytable import PrettyTable
                table = PrettyTable(
                    ["Index", "Name", "Status", "Type", "Subtype", "Group", "Component",
                     "Feature"])
                table.align["Index"] = "l"
                for row in testcases:
                    table.add_row(row)
                return table
        except TypeError:
            self.logger.error("Error, print_list_testcases: error during iteration.")
            return

    def _create_json_objects(self, testcases):
        for testcase in self._testcases:
            info = testcase.get_infodict()
            grp = info.get('group')
            if grp:
                group = os.sep.join(info.get('group').split(os.sep)[1:])
                if not group:
                    group = "no group"
            else:
                group = "no group"
            case = {}
            for key in info.keys():
                if key == "group":
                    case["group"] = group
                else:
                    case[key] = info[key]
            testcases.append(case)
        return testcases

    def _create_rows_for_table(self, rows):
        index = 0
        for testcase in self._testcases:
            info = testcase.get_infodict()
            try:
                index += 1
                grp = info.get('group')
                if grp:
                    group = os.sep.join(info.get('group').split(os.sep)[1:])
                    if not group:
                        group = "no group"
                else:
                    group = "no group"
                rows.append([index, info.get('name'), info.get('status'),
                             info.get('type'), info.get('subtype'),
                             group, info.get('comp'), info.get('feature')])
            except KeyError:
                self.logger.error("Error, printListTestcases: Testcase list item with "
                                  "index %d missing attributes.", index)

    def update_testcases(self):
        """
        Update test cases of this Suite from cloud.

        :return: Nothing
        """
        if not self.cloud_module:
            self.logger.error("Cloud module has not been initialized! "
                              "Skipping testcase update.")
            return False
        else:
            for testcase in self._testcases:
                try:
                    tc_instance = testcase.get_instance()
                    self.cloud_module.update_testcase(tc_instance.config)
                except Exception as err:  # pylint: disable=broad-except
                    self.logger.error(err)
                    self.logger.debug("Invalid TC: " + testcase.tcname)

    @staticmethod
    def get_suite_files(path):
        """
        Static method for finding all suite files in path.

        :param path: Search path
        :return: List of json files.
        """
        return_list = []
        if not isinstance(path, str):
            return return_list
        if not os.path.exists(path):
            return return_list
        for _, _, files in os.walk(path):
            for fil in sorted(files):
                _, extension = os.path.splitext(fil)
                if extension != '.json':
                    continue
                return_list.append(fil)
        return return_list

    def _create_tc_list(self):
        """
        Parses testcase metadata from suite file or from testcase list in args.
        Sets TestSuite status to 'parsed' to indicate that it has not yet been prepared.

        :raises: SuiteException
        """
        suite = None
        if self.args.suite:
            if os.path.exists(os.path.abspath(self.args.suite)):
                # If suite can be found using just the suite argument, we use that.
                suitedir, filename = os.path.split(os.path.abspath(self.args.suite))
            elif os.path.exists(self.args.suitedir):
                suitedir = self.args.suitedir
                # We presume that this is just the filename, or a path relative to the suitedir.
                filename = self.args.suite
            else:
                raise SuiteException("Suite creation from file failed. Unable to determine suite "
                                     "directory. Check --suitedir and --suite.")
            suite = self._load_suite_file(filename, suitedir)
            if not suite:
                raise SuiteException("Suite creation from file failed. "
                                     "Check your suite file format, path and access rights.")
            self._default_configs = suite.get("default", {})
            tcnames = []
            for i, testcase in enumerate(suite.get("testcases")):
                tcnames.append(str(testcase.get("name")))
            testcases = self._get_suite_tcs(self.args.tcdir, tcnames)
            if not testcases:
                raise SuiteException("Suite creation failed: Unable to find or filter testcases.")
            self._testcases = testcases
            self._print_search_errors()
            if len(testcases) != len(suite.get("testcases")):
                raise SuiteException("Suite creation from file failed: "
                                     "Number of requested testcases does not match "
                                     "amount of found testcases.")

            for i, testcase in enumerate(suite.get("testcases")):
                suiteconfig = testcase.get("config")
                self._testcases.get(i).set_suiteconfig(suiteconfig)
        else:
            tclist = self._load_suite_list()
            if tclist is False:
                raise SuiteException("Suite creation failed.")
            self._testcases = tclist
            if self.args.tc and self.args.tc != "all":
                self._print_search_errors()
            elif self._testcases.search_errors:
                self.logger.error("Failed import the following modules during test case search:")
                for item in self._testcases.search_errors:
                    self.logger.error("%s: %s", item["module"], item["error"])
        self.logger.info("Suite creation complete.")
        self._prepare_suite()

    def _print_search_errors(self):
        for testcase in self._testcases:
            if isinstance(testcase, DummyContainer):
                self.logger.error("Some test cases were not found.")
                for item in self._testcases.search_errors:
                    self.logger.error("%s: %s", item["module"], item["error"])

    def _prepare_suite(self):
        """
        Prepares parsed testcases for running.

        :raises: SyntaxError, SuiteException
        """
        for i, testcase in enumerate(self._testcases):
            try:
                self._prepare_testcase(testcase)
            except (TypeError, ImportError, ValueError) as err:
                raise SuiteException("Test case preparation failed for "
                                     "test case {}: {}".format(i, err))
            except SyntaxError:
                if self.args.list:
                    pass
                else:
                    raise
            testcase.status = TestStatus.READY
        self.logger.info("Test cases prepared.")
        self.status = TestStatus.READY

    def _get_suite_tcs(self, tcdir, testcases):
        """
        Generate a TestcaseList from a Suite.

        :param tcdir: Test case directory
        :param testcases: Names of testcases.
        :return: TestcaseList or None
        """
        if not os.path.isdir(tcdir):
            self.logger.error("Test case directory does not exist!")
            return None
        self.logger.info("Importing testcases for filtering")
        abs_tcpath = os.path.abspath(tcdir)
        sys.path.append(abs_tcpath)
        tclist = TestcaseList(logger=self.logger)
        tclist.import_from_path(abs_tcpath)
        if not tclist:
            self.logger.error("Error, runSuite: "
                              "Could not find any python files in given testcase dirpath")
            return None
        try:
            filt = TestcaseFilter().tc(testcases)
        except (TypeError, IndexError):
            self.logger.error("Error: Failed to create testcase filter for suite.")
            return None
        self.logger.info("Filtering testcases")
        if testcases == "all":
            testcases = None
        final_tclist = tclist.filter(filt, testcases)
        if not final_tclist:
            self.logger.error("Error, create_suite: "
                              "Specified testcases not found in %s.", abs_tcpath)
            return None
        return final_tclist

    def _prepare_testcase(self, testcase):
        """
        Run some preparatory commands on a test case to prep it for running.

        :param testcase: TestcaseContainer
        :return: Nothing
        """
        testcase.validate_tc_instance()
        testcase.merge_tc_config(self._default_configs)
        if testcase.get_suiteconfig():
            testcase.merge_tc_config(testcase.get_suiteconfig())
        testcase.set_final_config()
        testcase.validate_tc_instance()

    def _load_suite_file(self, name, suitedir):
        """
        Load a suite file from json to dict.

        :param name: Name of suite
        :param suitedir: Path to suite
        :return: Dictionary or None
        """
        self.logger.info("Loading suite from file")
        if not isinstance(name, str):
            self.logger.error("Error, load_suite: Suite name not a string")
            return None
        filename = name if name.split('.')[-1] == 'json' else name + '.json'
        filepath = os.path.join(suitedir, filename)

        suite = None
        if not os.path.exists(filepath):
            if self.cloud_module:
                suite = self.cloud_module.get_suite(name)
            else:
                self.logger.error("Error, load_suite_file: "
                                  "Suite file not found and cloud module not defined.")
                return None
            if not suite:
                self.logger.error("Error, load_suite_file: "
                                  "Suite file not found locally or in cloud.")
            return suite
        try:
            with open(filepath) as fil:
                suite = json.load(fil)
                return suite
        except IOError:
            self.logger.error("Error, load_suite_file: "
                              "Test suite %s cannot be read.", name)
        except ValueError:
            self.logger.error("Error, load_suite_file: "
                              "Could not load test suite. No JSON object could be decoded.")
        return None

    def _load_suite_list(self):
        """
        Generate a TestcaseList from command line filters.

        :return: TestcaseList or False
        """
        self.logger.info("Generating suite from command line.")
        args = self.args
        filt = TestcaseFilter()
        testcase = args.tc if args.tc else "all"
        try:
            filt = TestcaseFilter().tc(testcase)
            filt.status(args.status).group(args.group).testtype(args.testtype)
            filt.subtype(args.subtype).component(args.component).feature(args.feature)
        except (TypeError, IndexError):
            self.logger.exception("Filter creation failed.")
            return False

        self.logger.info("Importing testcases for filtering")
        if not os.path.isdir(args.tcdir):
            self.logger.error("Test case directory does not exist!")
            return False
        abs_tcpath = os.path.abspath(args.tcdir)
        sys.path.append(abs_tcpath)
        tclist = TestcaseList(self.logger)
        tclist.import_from_path(abs_tcpath)
        if not tclist:
            self.logger.error("Could not find any python files in given path")
            return False
        self.logger.info("Filtering testcases")
        if filt.get_filter()["list"] is not False:
            if isinstance(filt.get_filter()["list"], list):
                testcases = filt.get_filter()["list"]
            else:
                testcases = None
        else:
            testcases = None
        final_tclist = tclist.filter(filt, testcases)
        if not final_tclist:
            self.logger.error("Error, create_suite: "
                              "Specified testcases not found in %s.", abs_tcpath)
        return final_tclist
