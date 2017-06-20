"""
Copyright 2016 ARM Limited

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

import pkgutil
import os
import gc
import sys
import traceback
import datetime
import platform
import importlib
#The above are all part of the standard library. If one or more are missing,
#it's very likely a broken installation.
import json
import time
import mbed_test.LogManager as LogManager
from mbed_test.arguments import get_parser
from mbed_test.arguments import get_base_arguments
from mbed_test.arguments import get_tc_arguments
from mbed_test.tools import loadClass
from mbed_test.arguments import get_parser
from mbed_test.arguments import get_base_arguments
from mbed_test.arguments import get_tc_arguments
from mbed_test.bench import ReturnCodes
from mbed_test.ReportGenerator import PrintReport
from mbed_test.ReportGenerator import getSummary
from inspect import isclass
from jsonmerge import merge
import pkg_resources
import semver


class ExitCodes:
    EXIT_SUCCESS = 0
    EXIT_ERROR = 1
    EXIT_FAIL = 2


class mbedtestManager(object):
    def __init__(self):
        self.ACCEPTED_FILTER_KEYS = ['tc_name', 'tc_group', 'tc_status', 'tc_type', 'tc_subtype', 'tc_list', 'tc_comp']

        if platform.system() == 'Linux' or platform.system() == 'Darwin':
            #This little line takes the path to the current module and chops the filename off.
            #mbedtest/lib is added to path
            self.libpath = '/'.join(os.path.abspath(sys.modules[__name__].__file__).split('/')[:-1])
            #The advantage is that we don't have to care where the lib directory is,
            #as long as it's the same directory where mbedtestManagement.py resides.
            #Of course, to import mbedtestManagement itself requires that the lib
            #directory is in the python path or is importable some other way.
            #This solution may be os-specific and is pretty much just a hack until
            #a proper package is built.
            sys.path.append(self.libpath)

            #There is an issue that some lib/ExtApps modules want '..' to be on the
            #path, and not '../lib', because the assumption was that '..' would always
            #be the working directory and that thus possible to import lib.module
            #mbedtest added to path
            #TODO: get rid of this and change lib.module imports in Extapps and every testcase
            libpath2 = '/'.join(self.libpath.split('/')[:-1])
            sys.path.append(libpath2)

            self.ps = '/' #path slash type
        elif platform.system() == 'Windows':
            self.libpath = '\\'.join(os.path.abspath(sys.modules[__name__].__file__).split('\\')[:-1])
            sys.path.append(self.libpath)
            libpath2 = '\\'.join(self.libpath.split('\\')[:-1])
            sys.path.append(libpath2)
            self.ps = '\\' #path slash type

        #Check that the required modules are installed.
        required_modules = [ 'prettytable', 'requests', 'yattag', 'jsonmerge', 'xmltodict']

        self.args = self.parseArguments()

        LogManager.init_base_logging(self.args.log, verbose=self.args.verbose, silent=self.args.silent, color=self.args.color, list=self.args.list)
        self.logger = LogManager.get_logger("mbedtest")

        missingModules = []
        missingCount = 0
        for mod in required_modules:
            if not pkgutil.find_loader(mod):
                missingCount += 1
                missingModules.append(mod)
        if missingCount > 0:
            self.logger.error("Missing modules: " + ', '.join(missingModules))
            if platform.system() == 'Linux':
                self.logger.info("Install using: sudo pip install " + ' '.join(missingModules))
            elif platform.system() == 'Windows':
                self.logger.info("Install using: pip install " + ' '.join(missingModules))
            elif platform.system() == 'Darwin':
                self.logger.info("Install using: pip install " + ' '.join(missingModules))
            sys.exit(0)

        with open(os.path.join(self.libpath, 'tc_schema.json')) as data_file:
            self.tc_meta_schema = json.load(data_file)

    def getLocalTestcases(self, tcpath):
        """
        crawl given path for .py files
        """
        i = 0
        returnList = []
        if not isinstance(tcpath, str):
            self.logger.error("Error: testcase path is not string")
            sys.exit(0)

        #path is absolute
        tcpath = os.path.abspath(tcpath)
        scanDir = tcpath.split(self.ps)[-1]
        if len(tcpath.split(self.ps)) > 1:
            stripDir = self.ps.join(tcpath.split(self.ps)[:-1]) + self.ps
        else:
            stripDir = ''

        for root, dirs, files in os.walk(tcpath):
            for file in sorted(files):
                basename,extension = os.path.splitext( file )
                moduleroot = ''
                modulename = ''
                module = None
                tc_instance = None
                if ( basename == '__init__' ) or extension != '.py':
                    continue
                moduleroot = root.replace(stripDir,'', 1)
                modulename = moduleroot.replace(self.ps,".") +'.'+basename
                returnList.append((modulename, moduleroot, root+self.ps+file))
                i += 1
        if i == 0:
            self.logger.error("Error: No files found in given path: %s" % tcpath)
        return returnList

    def parseLocalTestcases(self, tc_list, verbose):
        """
        parse list produced by getLocalTestcases()
        """
        returnList = []
        if not isinstance(tc_list, list):
            self.logger.error("Error, parseLocalTestcases: Given argument not a list.")
            return returnList
        i = 0
        for tc in tc_list:
            i += 1
            try:
                #modulename, moduleroot, filepath
                parsedCases = self.parseLocalTest(modulename=tc[0], moduleroot=tc[1], filepath=tc[2], verbose=verbose)
                returnList.extend(parsedCases)
            except (IndexError, TypeError, ValueError):
                self.logger.error("Error, parseLocalTestcases: Malformed list item. Skipping item " + str(i))
                self.logger.debug("tc: "+str(tc))
                if verbose:
                    traceback.print_exc()
        return returnList

    def parseLocalTest(self, modulename, moduleroot, filepath, verbose):
        """
        called by parseLocalTestcases() to parse a module and find its testcases.
        It will return a list of the testcases available in this module.
        A valid testcase class is class which is either:
            * named 'Testcase'
            * contain a class constant 'IS_TEST' set to True
        """
        if not isinstance(modulename, str):
            self.logger.error("Error, parseLocalTestcases: modulename not a string.")
            raise TypeError("modulename should be a string")

        if len(modulename) == 0:
            self.logger.error("Error, parseLocalTestcases: modulename is an empty string.")
            raise ValueError("modulename shouldn't be empty")

        # test_cases will hold all tests found in this module
        test_cases = []

        # simple helper which build a failing test
        make_failing_test_case = lambda path, reason: {
            'tc_name':modulename.split('.')[-1],    # test bench name
            'tc_path': path,                        # Testcases.subdir.test.Testcase
            'tc_status':'fail',
            'tc_type':reason,
            'tc_subtype':'',
            'tc_group': moduleroot,                 # testcases/subdir
            'tc_file': filepath,                    # path to test.py
            'tc_comp': ["None"],
            'tc_fail': reason
        }

        # try to load module and look if there is any class which are a test case
        try:
            module = importlib.import_module(modulename)
        except Exception as e:
            # impossible to load the module, mark it as failed and return
            self.logger.debug(traceback.format_exc())
            test_cases.append(make_failing_test_case(modulename, 'Invalid TC (%s)' % e))
            return test_cases

        # iterate over all classes in the module and try to find test cases
        for test_class_name, test_class in module.__dict__.iteritems():
            if not isclass(test_class):
                continue
            # if a class as the constant flag IS_TEST set to true or is named Testcase,
            # fulfill test description and add it to the list
            if getattr(test_class, "IS_TEST", False) == True or test_class_name == "Testcase" :
                try:
                    test_case = test_class()
                except:
                    # impossible to build this test case, mark it as failed and continue to iterate over
                    # other testcases
                    test_cases.append(make_failing_test_case(modulename + "." + test_class_name, "Init exception"))
                    continue

                test_cases.append({
                    'tc_name': test_case.getTestName(),                # name of the test
                    'tc_path': modulename + "." + test_class_name,     # fully qualified name of the testclass
                    'tc_status': test_case.status() if test_case.status() else '',
                    'tc_type': test_case.type() if test_case.type() else '',
                    'tc_subtype': test_case.subtype() if test_case.subtype() else '',
                    'tc_group': moduleroot,
                    'tc_file': filepath,                               # path to the file which hold this test
                    'tc_comp': test_case.getTestComponent() if test_case.getTestComponent() else ["None"],
                    'tc_fail':''
                })

        return test_cases

    def printListTestcases(self, testcases):
        """
        print relevant information from a list of parsed testcases
        """
        self.logger.info("TCs:")
        index = 0
        depth = 0

        from prettytable import PrettyTable

        x = PrettyTable(["Index", "Name", "Status", "Type", "Subtype", "Group", "Component"])
        #x = PrettyTable(["Index", "Name", "File", "Status", "Type", "Subtype", "Group", "Component"])
        x.align["Index"] = "l"
        #x.padding_width = 1
        #x.border = False
        try:
            for tc in testcases:
                try:
                    index +=1
                    group = self.ps.join(tc['tc_group'].split(self.ps)[1:])
                    #filename = tc['tc_file'].split(self.ps)[-1]
                    x.add_row([index, tc['tc_name'], tc['tc_status'], tc['tc_type'], tc['tc_subtype'], group, tc['tc_comp']])
                    #x.add_row([index, tc['tc_name'], filename, tc['tc_status'], tc['tc_type'], tc['tc_subtype'], group, tc['tc_comp']])
                except KeyError:
                    self.logger.error("Error, printListTestcases: Testcase list item with index %d missing attributes."  %index)
        except TypeError:
            if index == 0:
                self.logger.error("Error, printListTestcases: given parameter not iterable.")
            else:
                self.logger.error("Error, printListTestcases: error during iteration.")
            return
        print(x)

    def loadTestcase(self, modulename, verbose=False):
        '''
        :param modulename: testcase to be load
        :param verbose: print exceptions when loading class
        :return: testcase instance
        raise TypeError exception when modulename is not string
        raise ImportError exception when cannot load testcase
        '''
        if not isinstance(modulename, str):
            raise TypeError("Error, runTest: modulename not a string.")
        module = loadClass(modulename, verbose)

        if module == None:
            raise ImportError("Error, runTest: loadClass returned NoneType for modulename: %s"%modulename)

        return module()

    def runTest(self, modulename, silent = True, cloud = False, verbose=False, defaultConf=None, tc_file=None):
        """
        called by runTestcases() to run single testcase
        """
        try:
            tc_instance = self.loadTestcase(modulename, verbose)
            if self.validateTestCaseMetadata(tc_instance):
                raise SyntaxError("Invalid TC '%s' metadata", modulename)
        except TypeError as err:
            self.logger.error("Error, runTest: Testcase %s modulename was incorrect!" % modulename)
            if verbose:
                traceback.print_exc()
            raise err
        except ImportError as err:
            self.logger.error("Error, runTest: Testcase %s Initialization threw an exception!" % modulename)
            if verbose:
                traceback.print_exc()
            raise err

        # todo: handle TC specific arguments
        parser = get_tc_arguments( get_base_arguments( get_parser() ) )
        args, unknown = parser.parse_known_args()
        if len(unknown) > 0:
            for para in unknown:
                self.logger.warn("mbed test received unknown parameter {}".format(para))
            if not args.ignore_invalid_params:
                self.logger.error("Unknown parameters received, exiting. To ignore this add --ignore_invalid_params flag.")
                parser.print_help()
                sys.exit(ExitCodes.EXIT_ERROR)
        tc_instance.setArgs(args)
        # Merge tc config and suite config if one is provided
        if defaultConf:
            tc_conf = tc_instance.getConfig()
            try:
                if len(defaultConf["requirements"]["duts"]) > 1:
                    for key in defaultConf["requirements"]["duts"]:
                        if isinstance(key, int):
                            val = defaultConf["requirements"]["duts"].pop(key)
                            defaultConf["requirements"]["duts"][str(key)] = val
            except KeyError:
                pass
            merged_conf = merge(tc_conf, defaultConf)
            tc_instance.setConfig(merged_conf)

        result = self._check_version(tc_instance)
        if result is not None:
            return result

        # Skip the TC IF NOT defined on the command line
        if tc_instance.skip(): #and not self.args.tc:
            info = tc_instance.skip_info()
            if info.get('only_type') or info.get('only_platform'):
                type_r = info.get('only_type')
                if type_r:
                    try:
                        dut_type = tc_instance.config['requirements']['duts']['*']['type']
                    except KeyError:
                        dut_type = None
                    if (dut_type == type_r or self.args.type == type_r):
                        self.logger.info("TC '%s' will be skipped because of '%s'" % (
                            tc_instance.getTestName(), (tc_instance.skipReason())))
                        # TODO: retcodes are being updated. find the right retcode.
                        result = tc_instance.getResult()
                        result.setVerdict(verdict='skip', retcode=-1, duration=0)
                        del tc_instance
                        return result
                        # TODO: Check for platform restriction
            else:
                self.logger.info("TC '%s' will be skipped because of '%s'" % (
                tc_instance.getTestName(), (tc_instance.skipReason())))
                # TODO: retcodes are being updated. find the right retcode.
                result = tc_instance.getResult()
                result.setVerdict(verdict='skip', retcode=-1, duration=0)
                del tc_instance
                return result

        if silent:
            self.logger.info( tc_instance.getTestName().ljust(32) )
        else:
            self.logger.info("")
            self.logger.info("START TEST CASE EXECUTION: '%s'" % tc_instance.getTestName())
            self.logger.info("")
        #meta = tc_instance.getMetadata()

        a = datetime.datetime.now()
        try:
            retcode = tc_instance.run()
        except:
            if verbose: traceback.print_exc()
            retcode = -9999
        b = datetime.datetime.now()

        result = tc_instance.getResult(tc_file = tc_file)

        # Force garbage collection
        gc.collect()
        #cleanup Testcase
        tc_instance = None

        LogManager.finish_testcase_logging()

        if result.retcode == ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER:
            print("Press CTRL + C again if you want to abort test run")
            try:
                time.sleep(5)
            except KeyboardInterrupt as e:
                raise e
        elif result.retcode == ReturnCodes.RETCODE_FAIL_INITIALIZE_BENCH:
            print("Exception while trying to initialize TC")

        c = b - a
        duration = c.total_seconds()

        result.setVerdict(
            verdict = 'pass' if retcode ==0 else 'fail',
            retcode = retcode,
            duration = duration )

        if cloud:
            response_data = cloud.sendResult(result)
            if response_data:
                data = response_data
                id = data['_id']
                self.logger.info("Results sent to the server. ID: {}".format(id))
            else:
                self.logger.info("Server didn't respond or client initialization has failed.")

        return result




    def runTestcases(self, testcases, silent = True, cloud = False, verbose=False):
        """
        run testcases from list of parsed, filtered testcases
        """
        results = []
        result = -1
        i = 0
        try:
            from ReportGenerator import ReportGenerator
            from ReportGenerator import StoreReport
            from junit import Junit
        except ImportError:
            self.logger.error("Error: missing library modules(ReportGenerator/StoreReport.")
            sys.exit(0)

        #make suite
        #self.runSuite(suite, cloud, silent, tcdir verbose)
        try:
            for test in testcases:
                i+=1
                result = None
                try:
                    if test['tc_fail']:
                        result = self.getFailResult(test)
                    else:
                        if 'tc_file' in test:
                            result = self.runTest(modulename=test['tc_path'], silent=silent, cloud=cloud, verbose=verbose, tc_file=test['tc_file'])
                        else:
                            result = self.runTest(modulename=test['tc_path'], silent=silent, cloud=cloud, verbose=verbose)
                except KeyError:
                    self.logger.error("Error, runTestcases: testcase path('tc_path') missing for case: %s"%str(i))
                    if(verbose):traceback.print_exc()
                except SyntaxError:
                    self.logger.error("Error, runTestcases: testcase %d doesn't have valid meta data: %s"%(i,str(test)))
                    if(verbose):traceback.print_exc()
                except TypeError:
                    self.logger.error("Error, runTestcases: testcase %d doesn't have required attributes: %s"%(i,str(test)))
                    if(verbose):traceback.print_exc()
                except KeyboardInterrupt:
                    self.logger.info("User aborted test run")
                    break
                if result != None:
                    #Test had required attributes and ran succesfully or was skipped.
                    #Note that a fail *during* a testcase run will still be reported.
                    results.append(result)
                    if self.args.stop_on_failure and result.getVerdict() != 'pass':
                        break
            report = ReportGenerator('Test Results',
                { 'Build': '', 'Branch': self.args.branch,
                }, results )
            result_filename = os.path.join(LogManager.get_base_dir(), "result.html")
            StoreReport( report, result_filename)
            # Create junit file
            Junit(results).save(os.path.join(LogManager.get_base_dir(), "result.junit.xml"))
            # Copy results junit file to root log folder
            Junit(results).save(os.path.join(LogManager.get_base_dir(), "../result.junit.xml"))
        except TypeError:
            self.logger.error("Error, runTestcases: given parameter not iterable.")
        return results

    def getFailResult(self, tc):
        from mbed_test.Result import Result
        result = Result()
        result.setTcMetadata({'name':tc['tc_name']})
        result.setVerdict("fail", -1)
        result.fail_reason = tc['tc_fail']
        return result

    def runSingleTestcase(self, tc, silent = True, cloud = False):
        """
        run single testcase given by index from --list
        """
        if 'tc_file' in tc:
            results = [self.runTest(modulename=tc, silent=silent, cloud=cloud, tc_file=tc['tc_file'])]
        else:
            results = [self.runTest(modulename=tc, silent=silent, cloud=cloud)]
        return results

    def createFilter(self, tc=False, status=False, group=False, testtype=False, subtype=False, component=False):
        """
        create a filter for filterTestcases()
        """
        outFilter = {}
        outFilter['tc_list'] = False
        outFilter['tc_name'] = False
        outFilter['tc_status'] = False
        outFilter['tc_group'] = False
        outFilter['tc_type'] = False
        outFilter['tc_subtype'] = False
        outFilter['tc_comp'] = False


        if status:
            if not isinstance(status, str):
                self.logger.error("Error, createFilter: status argument not a string")
                return -1
            else:
                outFilter['tc_status'] = status
        if group:
            if not isinstance(group, str):
                self.logger.error("Error, createFilter: group argument not a string")
                return -1
            else:
                outFilter['tc_group'] = group
        if testtype:
            if not isinstance(testtype, str):
                self.logger.error("Error, createFilter: type argument not a string")
                return -1
            else:
                outFilter['tc_type'] = testtype
        if subtype:
            if not isinstance(subtype, str):
                self.logger.error("Error, createFilter: type argument not a string")
                return -1
            else:
                outFilter['tc_subtype'] = subtype
        if component:
            if not isinstance(component, str):
                self.logger.error("Error, createFilter: component argument not a string")
                return -1
            else:
                outFilter['tc_comp'] = [component]

        # tc can be:
        #int, tuple, list or str(any of the above)
        if isinstance(tc, str):
            # Wildcard chjeck
            if tc == 'all':
                outFilter['tc_name'] = 'all'
                return outFilter

            from ast import literal_eval as le
            pFilter = []
            try:
                pFilter = le(tc)
            except (ValueError, SyntaxError):
                # tc wasn't immediately parseable.
                # This can mean that it was a list/tuple with a string, which gets
                # interpreted as a variable, which causes a malformed string exception.
                # Therefore, need to split and evaluate each part of the list separately
                pass

            if pFilter == []:
                # we get bad names/indexes if we leave parentheses.
                # A dictionary will not add anything to pFilter.
                tc = tc.strip('([])')
                for item in tc.split(','):
                    try:
                        # Transforms string into other python type
                        # Troublesome if someone names a testcase in the form of a valid python type...
                        le_item = le(item)
                        pFilter.append(le_item)
                    except (ValueError, SyntaxError):
                        # It's just a string, but it's also a name(maybe).
                        # Hopefully we're on a filesystem that allows files with identical paths
                        pFilter.append(item)
                if len(pFilter) == 1:
                    #It was a single string.
                    outFilter['tc_name'] = pFilter[0]
                    return outFilter
                elif len(pFilter) == 0:
                    pass

            tc = pFilter

        if isinstance(tc, int) and tc:
            if tc < 1:
                self.logger.error("Error, createFilter: non-positive integer " + str(tc))
                return -1
            else:
                outFilter['tc_list'] = [tc-1]
        elif isinstance(tc, dict):
            for key in tc.keys():
                if key not in self.ACCEPTED_FILTER_KEYS:
                    self.logger.error("Error, createFilter: Incorrect filter key given: " + str(key))
                    return -1
                if not isinstance(tc[key], str):
                    self.logger.error("Error, createFilter: Filter value not string: %s:%s" %(key, str(tc[key])))
                    return -1
            for key in tc.keys():
                if key in outFilter.keys():
                    self.logger.error("Error, createFilter: dictionary had key that was already provided. Skipping.")
                    continue
                outFilter[key] = tc[key]
        elif isinstance(tc, list) or isinstance(tc, tuple):
            if len(tc) < 1:
                self.logger.error("Error, createFilter: Index list empty.")
                return -1
            for i in tc:
                if not isinstance(i, int) and not isinstance(i, str):
                    self.logger.error("Error, createFilter: Index list has invalid member: %s" % str(tc))
                    return -1
            outFilter['tc_list'] = [x-1 for x in tc if isinstance(x, int)]
            outFilter['tc_list'].extend([x for x in tc if isinstance(x, str)])
        elif tc == None:
            pass
        else:
            # In case someone calls with NoneType or anything else
            if tc:
                self.logger.warning("Warning, createFilter: tc argument is unacceptable type. Proceeding anyway.")

        count = False
        for key in outFilter.keys():
            if outFilter[key]:
                count = True
                break
        else:
            return -1

        return outFilter

    def filterTestcases(self, testcases, caseFilter):
        """
        filter testcases to by index list, name, group, status or type
        """
        valid = False
        if not isinstance(caseFilter, dict):
            self.logger.error("Error, filterTestcases: caseFilter not a dictionary.")
            sys.exit(0)
        for key in caseFilter.keys():
            if key not in self.ACCEPTED_FILTER_KEYS:
                '''
                    Rather than removing the unacceptable key and continuing, the program exits.
                    This is so that the user can fix the input *before* running potentially dozens of testcases.
                '''
                self.logger.error("Error, filterTestcases: unacceptable key: %s" %key)
                sys.exit(0)
            if caseFilter[key]:
                valid = True
        if not valid:
            self.logger.error("Error, filterTestcases: Nothing in filter. Nothing to filter with.")
            sys.exit(0)

        if not isinstance(testcases, list):
            self.logger.error("Error, filterTestcases: testcases list not a list instance.")
            sys.exit(0)
        if len(testcases) == 0:
            self.logger.error("Error, filterTestcases: testcases list empty.")
            sys.exit(0)

        # Select testcases by list of indices
        templist = []
        if 'tc_list' in caseFilter.keys() and caseFilter['tc_list']:
            for index in caseFilter['tc_list']:
                if isinstance(index, int):
                    if index < len(testcases) and not index < 0:
                        templist.append(testcases[index])
                    elif index > len(testcases):
                        self.logger.error("Error, filterTestcases: index list contained too large integer: %s"%caseFilter['tc_list'])
                        sys.exit(0)
                    else:
                        self.logger.error("Error, filterTestcases: index list contained non-positive integer: %s"%caseFilter['tc_list'])
                        sys.exit(0)
                elif isinstance(index, str):
                    for tc in testcases:
                        if tc['tc_name'] == index:
                            templist.append(tc)
                            break
                else:
                    self.logger.error("Error, filterTestcases: index list contained non-integer: '%s'" % caseFilter['tc_list'])
                    sys.exit(0)
        else:
            templist = testcases

        remove = []

        if 'tc_group' in caseFilter.keys() and caseFilter['tc_group']:
            group = caseFilter['tc_group'].split(self.ps)
            group = [x for x in group if len(x)] # Remove empty members
            if len(group) == 1:
                group = caseFilter['tc_group'].split(',')
            for tc in templist:
                tcgroup = tc['tc_group'].split(self.ps)
                for member in group:
                    if member not in tcgroup:
                        remove.append(templist.index(tc))
                        break

        for x in remove[::-1]: templist.pop(x)
        remove = []

        keys = ['tc_status', 'tc_type', 'tc_subtype', 'tc_comp', 'tc_name']
        for key in keys:
            if key in caseFilter.keys() and caseFilter[key]:
                # Possible that string comparison can cause encoding comparison error.
                # TODO: Add encoding check and handling at some future point. Maybe.
                # In the case where the caseFilter is 'all', the step is skipped and all
                # testcases are included
                if key == 'tc_name' and caseFilter[key] == 'all':
                    continue
                for tc in templist:
                    if tc[key] != caseFilter[key]:
                        remove.append(templist.index(tc))
                for x in remove[::-1]: templist.pop(x)
                remove = []

        return templist

    def runSuite(self, suite, cloud = False, silent = True, tcdir='./testcases', verbose = False):
        results = []
        if not isinstance(suite, dict):
            self.logger.error("Error, runSuite: suite is not a dictionary.")
            return results
        if not 'testcases' in suite.keys() or len(suite['testcases']) == 0:
            self.logger.error("Error, runSuite: Nothing to run.")
            return results
        #import pprint
        #pprint.pprint(suite['testcases'])
        for suite_tc in suite['testcases']:
            #print suite_tc.keys()
            if "name" not in suite_tc.keys():
                self.logger.error("Error, runSuite: Listed testcase lacks name.")
                return results

        abs_tcpath = os.path.abspath(tcdir)
        absolutePath = self.ps.join(abs_tcpath.split(self.ps)[:-1])
        sys.path.append(absolutePath)

        tcs_local = self.getLocalTestcases(tcpath=abs_tcpath)

        if len(tcs_local) == 0:
            self.logger.error("Error, runSuite: Could not find any python files in given testcase dirpath")
            return results

        tc = [str(x['name']) for x in suite['testcases']]
        filt = self.createFilter(tc=tc)
        if filt == -1:
            self.logger.error("Error: Failed to create testcase filter for suite.")
            return -1
        tcs_parsed = self.parseLocalTestcases(tc_list=tcs_local, verbose=verbose)
        if len(tcs_parsed) == 0:
            self.logger.error("Error, runSuite: List of parsed testcases is empty.")
            return results
        tcs_filtered = self.filterTestcases(testcases=tcs_parsed, caseFilter=filt)
        if len(tcs_filtered) == 0:
            self.logger.error("Error, runSuite: Specified testcases not found in {}.".format(abs_tcpath))
            return results

        suite_timeout = suite['suiteTimeout'] if 'suiteTimeout' in suite.keys() else 0 #default value?
        default = suite['default'] if 'default' in suite.keys() else False
        names = [x['name'] for x in suite['testcases']]

        #Get default configuration from suite if it exists
        try:
            default_conf = suite['default']
        except KeyError:
            self.logger.info("No default configuration for testcases found.")
            default_conf = None
            pass

        for tc in tcs_filtered:
            index = names.index(tc['tc_name']) if tc['tc_name'] in names else -1
            if index < 0:
                self.logger.error("Error, runSuite: suite testcase \"%s\" not found in testcase dir."%tc['tc_name'])
                continue
            names.pop(index)
            suite_tc = suite['testcases'][index]
            suite['testcases'].pop(index)
            iterations = suite_tc['iteration'] if 'iteration' in suite_tc.keys() else 1
            configs = suite_tc.get("config")

            if configs and default_conf:
                final_conf = merge(default_conf, configs)
            elif configs and not default_conf:
                final_conf = configs
            elif default_conf and not configs:
                final_conf = default_conf
            else:
                final_conf = None

            if iterations == 0:
                continue
            iteration = 0
            timeout = suite_tc['timeout'] if 'timeout' in suite_tc.keys() else suite_timeout
            while iteration < iterations:
                retries = suite_tc['retries'] if 'retries' in suite_tc.keys() else 0
                iteration += 1
                while True:
                    #Q: How to pass timeout? A: Awaiting implementation.
                    #Q: How to pass default settings?
                    self.logger.info("Starting iteration %d of %d for \"%s\""%(iteration, iterations, tc['tc_name']))
                    if 'tc_file' in tc:
                        result = self.runTest(tc['tc_path'], silent, cloud, verbose, defaultConf=final_conf, tc_file=tc['tc_file'])
                    else:
                        result = self.runTest(tc['tc_path'], silent, cloud, verbose, defaultConf=final_conf)
                    results.append(result)
                    if result.retcode == 0: #Pass
                        break
                    elif retries > 0:
                        self.logger.error("Testcase %s failed. %d retries left"%(tc['tc_name'], retries))
                        retries -= 1
                        continue
                    else:
                        self.logger.error("Testcase %s failed. No retries left."%(tc['tc_name']))
                        break
        return results

    def _check_version(self, tc_instance):
        if tc_instance.config["compatible"]["framework"]["name"] and self.args.check_version:
            framework = tc_instance.config["compatible"]["framework"]

            if framework["version"] and framework["name"] == "mbedtest":
                ver_string = framework["version"]
                framework_version = pkg_resources.require("mbed-test")[0].version
            if ver_string[0].isdigit():
                if int(framework_version[0]) > 0 and ver_string[0] == "0":
                    result = self.__wrong_version(tc_instance, ver_string, "B1 Testcase not suitable for version >1.0.0. Installed version: {}".format(framework_version))
                    return result

                if framework_version != ver_string:
                    result = self.__wrong_version(tc_instance, ver_string, "Testcase suitable only for mbedtest version {}".format(ver_string))
                    return result
            else:
                if ver_string[1].isdigit():
                    if int(framework_version[0]) > 0 and ver_string[1] == "0":
                        result = self.__wrong_version(tc_instance, ver_string, "B2 Testcase not suitable for version >1.0.0. Installed version: {}".format(framework_version))
                        return result
                elif ver_string[2].isdigit():
                    if int(framework_version[0]) > 0 and ver_string[2] == "0":
                        result = self.__wrong_version(tc_instance, ver_string, "B3 Testcase not suitable for version >1.0.0. Installed version: {}".format(framework_version))
                        return result
                if not semver.match(framework_version, ver_string):
                    result = self.__wrong_version(tc_instance, ver_string)
                    return result
        else:
            return None

    def __wrong_version(self, tc_instance, ver_string, msg=None):
        msg = msg if msg else "Version {} of mbed-test required.".format(ver_string)
        self.logger.info("TC %s will be skipped because of '%s'" % (tc_instance.getTestName(), msg))
        result = tc_instance.getResult()
        result.skip_reason = msg
        result.setVerdict(verdict='skip', retcode=-1, duration=0)
        del tc_instance
        return result



    def listSuites(self, suitedir="./testcases/suites", cloud=False):
        suites = []
        suites.extend(self.getSuites(suitedir))
        #no suitedir, or no suites -> append cloud.get_campaigns()

        if cloud:
            suites.extend(cloud.get_campaign_names())
        if not len(suites):
            self.logger.error("Error, listSuites: No suites found locally or in cloud.")
            return

        from prettytable import PrettyTable
        x = PrettyTable(["Testcase suites"])
        for s in suites:
            x.add_row([s])
        print(x)

    def getSuites(self, path="./testcases/suites"):
        i = 0
        returnList = []
        if not isinstance(path, str):
            self.logger.error("Error, getSuites: Suite dirpath not a string.")
            return returnList
        if not os.path.exists(path):
            self.logger.error("Error, getSuites: Given suite dirpath does not exist.")
            return returnList
        for root,dirs,files in os.walk(path):
            for file in sorted(files):
                basename, extension = os.path.splitext( file )
                if extension != '.json':
                    continue
                returnList.append(file)

        return returnList

    def loadSuite(self, name, path="./testcases/suites", cloud=False):
        if not isinstance(name, str):
            self.logger.error("Error, loadSuite: Suite name not a string")
            return None
        filename = name if name.split('.')[-1] == 'json' else name + '.json'
        suitepath = os.path.abspath(os.path.join(path, filename))
        suite = None

        if not os.path.exists(suitepath):
            if cloud:
                suite = cloud.get_suite(name)
            if not suite:
                self.logger.error("Error, loadSuite: Suite file not found locally or in cloud.")
                return None
            else:
                return suite
        try:
            with open(suitepath) as file:
                suite = json.load(file)
        except IOError:
            self.logger.error("Error, loadSuite: Test suite %s cannot be read."%name)
            return None
        except (ValueError):
            self.logger.error("Error, loadSuite: Could not load test suite. No JSON object could be decoded.")
            return None

        return suite

    def run(self, args=None):
        """
        Runs the set of tests within the given path.
        If called with listing = True, only calls printListTestcases()
        Can use filter to narrow down list of testcases. Filter can be a string(filename, testcase name, * wildcard), integer, stringified dict or stringified list of indexes.
        """
        retcodeSummary = ExitCodes.EXIT_SUCCESS
        args = args or self.args

        if args.version:
            import pkg_resources  # part of setuptools
            version = pkg_resources.require("mbed-test")[0].version
            print(version)
            sys.exit(0)

        if args.clean:
            self.cleanLogs(silent=args.silent)
            return retcodeSummary

        cloud = False
        if args.cloud:
            from cloud import Cloud
            try:
                node_name=os.environ.get('NODE_NAME', '')
                host=os.environ.get('MBED_CLITEST_CLOUD_HOST', 'localhost:3000')
                if args.cm:
                    cloudModule = args.cm
                else:
                    cloudModule = os.environ.get("MBED_CLITEST_CLOUD_PROVIDER", '')
                ind = host.rfind(":")
                if ind != -1:
                    try:
                        port = int(host[ind + 1:])
                        host = host[:ind]
                    except ValueError:
                        self.logger.info(
                            "Port not found in environment variable MBED_CLITEST_CLOUD_PROVIDER, assuming default")
                        port = 3000
                else:
                    self.logger.info(
                        "Port not found in environment variable MBED_CLITEST_CLOUD_PROVIDER, assuming default")
                    port = 3000
                cloud = Cloud(host=host, port=port, module=cloudModule)
                self.logger.info("Initialized cloud module for host {}".format(host))
            except Exception as e:
                self.logger.error("Cloud module could not be initialized: {}".format(e))
                cloud = False

        if args.listsuites:
            retcodeSummary = self.listSuites(args.suitedir, cloud)
            return retcodeSummary

        if args.suite:
            try:
                from ReportGenerator import ReportGenerator
                from ReportGenerator import StoreReport
                from junit import Junit
            except ImportError:
                self.logger.error("Error: missing library modules(ReportGenerator/StoreReport.")
                sys.exit(0)
            suite = self.loadSuite(args.suite, args.suitedir, cloud)
            if suite:
                tc = [str(x['name']) for x in suite['testcases']]
                results = self.runSuite(suite, cloud, args.silent, args.tcdir, args.verbose)
                report = ReportGenerator('Test Results',
                    { 'Build': '', 'Branch': args.branch,
                    }, results )
                s = getSummary(results)
                if s['fail'] != 0:
                    retcodeSummary = ExitCodes.EXIT_FAIL

                StoreReport( report, os.path.join(LogManager.get_base_dir(), 'result.html'))
                Junit(results).save(os.path.join(LogManager.get_base_dir(), "result.junit.xml"))
                PrintReport( results )
                return retcodeSummary
            else:
                self.logger.error("Error: Suite invalid.")
                return ExitCodes.EXIT_ERROR
        '''
        filtering arguments
            args.tc: testcase name, index or wildcard(all)
            args.status: testcase status
            args.group: testcase group selection
            args.testtype: testcase type
        '''
        filt = self.createFilter(tc=args.tc, status=args.status, group=args.group, testtype=args.testtype, subtype=args.subtype, component=args.component)
        if filt == -1:
            if args.list:
                filt = {'tc_list': False, 'tc_name': 'all', 'tc_status': False, 'tc_group': False, 'tc_type': False}
            else:
                if not args.silent:
                    self.logger.error("Error: Failed to create testcase filter. No arguments given.")
                parser = get_tc_arguments( get_base_arguments( get_parser()))
                parser.print_help()
                return ExitCodes.EXIT_ERROR

        abs_tcpath = os.path.abspath(args.tcdir)
        tcs_local = self.getLocalTestcases(tcpath=abs_tcpath)
        if len(tcs_local) == 0:
            self.logger.error("Could not find any python files in given path")
            return ExitCodes.EXIT_ERROR

        absolutePath = self.ps.join(abs_tcpath.split(self.ps)[:-1])
        sys.path.append(absolutePath)
        tcs_parsed = self.parseLocalTestcases(tc_list=tcs_local, verbose=args.verbose)
        if tcs_parsed == []:
            self.logger.error("Error: List of parsed testcases is empty.")
            return ExitCodes.EXIT_ERROR
        tcs_filtered = self.filterTestcases(testcases=tcs_parsed, caseFilter=filt)

        if len(tcs_filtered) == 0:
            self.logger.error("Error, runSuite: Specified testcases not found in {}.".format(abs_tcpath))
            return ExitCodes.EXIT_ERROR

        if args.list:
            if args.cloud:
                self.updateTestcases(cloud=cloud, testcases=tcs_filtered, verbose=args.verbose)
            else:
                self.printListTestcases(testcases=tcs_filtered)
            return retcodeSummary
        results = []
        if args.repeat > 1:
            cases = list(tcs_filtered)
            for n in xrange(1, int(args.repeat)):
                tcs_filtered.extend(cases)
        #for n in xrange(0,int(args.repeat)):
        r = self.runTestcases(testcases=tcs_filtered, cloud=cloud, silent=args.silent,verbose=args.verbose)
        results += r
        s = getSummary(r)
        if s["fail"] != 0:
            retcodeSummary = ExitCodes.EXIT_FAIL

        PrintReport( results )

        return retcodeSummary

    def validateTestCaseMetadata(self, tc):
        from jsonschema import validate, ValidationError, SchemaError
        try:
            validate(tc.config, self.tc_meta_schema)
        except ValidationError  as err:
            print("Metadata validation failed! Please fix your TC Metadata!")
            print(tc.config)
            print(err)
            return 1
        except SchemaError as err:
            print("Schema error")
            sys.exit(1)
        return 0

    def updateTestcases(self, cloud, testcases, verbose):

        for tc in testcases:
            try:
                tc_instance = self.loadTestcase(tc['tc_path'], verbose=False)
                if cloud and self.validateTestCaseMetadata(tc_instance)==0:
                    cloud.updateTestcase( tc_instance.config )
            except Exception as err:
                print(err)
                print("Invalid TC: "+tc['tc_path'])

    def parseArguments(self):
        if not pkgutil.find_loader('mbed_test.arguments'):
            self.logger.error("Missing module:mbed_test/arguments")
            sys.exit(0)

        parser = get_base_arguments( get_parser() )
        parser = get_tc_arguments( parser )
        args, unknown = parser.parse_known_args()
        return args

    def clean_onerror(self, fn, path, excinfo):
        self.logger.error("%s encountered error when processing %s: %s" % (fn. path, excinfo))

    def cleanLogs(self, silent=False):
        import shutil
        try:
            shutil.rmtree('log', ignore_errors=silent, onerror=None if silent else self.clean_onerror)
        except:
            pass
