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

import os
from os.path import join, abspath, dirname
import sys
import traceback
import json
from pprint import pformat
import subprocess
from jsonmerge import merge
import logging
# Internal libraries
import mbed_clitest.LogManager as LogManager
from mbed_clitest.tools import loadClass, strintkey_to_intkey
from mbed_clitest.CliRequest import *
from mbed_clitest.CliResponse import *
from mbed_clitest.CliResponseParser import *

from mbed_clitest.Searcher import *
from mbed_clitest.TestStepError import TestStepError, TestStepFail, TestStepTimeout
from mbed_clitest.arguments import get_parser
from mbed_clitest.arguments import get_base_arguments
from mbed_clitest.arguments import get_tc_arguments
from mbed_clitest.Result import Result

from mbed_clitest.GenericProcess import GenericProcess
from mbed_clitest.ExtApps import ExtApps
from mbed_clitest.Extensions import Extensions
from mbed_clitest.GitTool import get_git_info

from mbed_clitest.ResourceProvider.ResourceProvider import ResourceProvider
import pkg_resources

class ReturnCodes:
    RETCODE_SUCCESS                             = 0
    RETCODE_FAIL_SETUP_BENCH                   = 1000
    RETCODE_FAIL_SETUP_TC                      = 1001
    RETCODE_FAIL_MISSING_DUTS                   = 1002
    RETCODE_FAIL_UNDEFINED_REQUIRED_DUTS_COUNT  = 1003
    RETCODE_FAIL_DUT_CONNECTION_FAIL            = 1004
    RETCODE_FAIL_TC_EXCEPTION                   = 1005
    RETCODE_FAIL_TEARDOWN_TC                    = 1006
    RETCODE_FAIL_INITIALIZE_BENCH               = 1007
    RETCODE_FAIL_NO_PRELIMINARY_VERDICT         = 1010
    RETCODE_FAIL_TEARDOWN_BENCH                 = 1011
    RETCODE_FAIL_ABORTED_BY_USER                = 1012

class NodeEndPoint(object):
    def __init__(self, bench, deviceId):
        self.bench = bench
        self.id = deviceId

    def command(self, cmd, expectedRetcode = 0):
        return self.bench.command(self.id, cmd, expectedRetcode = expectedRetcode)


class Bench(CliResponseParser):

    __version = 0.5
    __env = {
        "extApps": {
            "puttyExe": "C:\Program Files (x86)\PuTTY\putty.exe",
            "kittyExe": "C:\Program Files (x86)\PuTTY\kitty.exe"
        }
    }

    # Test Bench constructor
    # kwargs contains keys, like name, required_duts, ...
    #
    # executeCommand returns CliResponse class
    #
    def __init__(self, **kwargs):
        CliResponseParser.__init__(self)
        self.__retcode = None
        self.__failReason = ""
        self.Name = ''
        self.__PreliminaryVerdict = None
        self.__externalServices = []
        self.__test_git_info= {}
        self.tshark_arguments = {}
        self.tshark_preferences = {}
        self.config = {}
        self.duts = []
        self.openPutty = self.open_node_terminal
        self.resource_provider = None
        self.logger = logging.getLogger()
        self.DEFAULT_BIN = "./../CliNode"
        self.integer_keys_found = None
        self.config = {
                "compatible": {
                    "framework": {
                        "name": "clitest",
                        "version": ">=0.4.0"
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
                    "duts": { "*": {
                        "application": {
                            "bin": self.DEFAULT_BIN
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
                self.integer_keys_found = False
                for key in kwargs["requirements"]["duts"]:
                    if isinstance(key, int):
                        self.integer_keys_found = True
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
        self.command = self.executeCommand
        self.__parseArguments()

    def getConfig(self):
        return self.config

    def setConfig(self, config):
        self.config = config

    def get_tc_abspath(self, tc_file = None):
        if not tc_file:
            return os.path.abspath(self.args.tcdir)
        else:
            return os.path.abspath(tc_file)

    def get_node_endpoint(self, id):
        if isinstance(id, basestring):
            id = self.get_dut_index(id)
        return NodeEndPoint(self, id)


    def get_time(self):
        return time.time() - self.starttime

    def __initialize(self):
        # Initialize log instances
        self.__initLogs()

        # Read cli given environment configuration file
        env_cfg = self.__readEnvironmentConfigurations()
        if not env_cfg:
            self.logger.error("Error when reading environment configuration. Aborting")
            return False
        # Read cli given TC configuration file and merge it
        self.__readExecutionConfigurations()

        # Create ResourceProvider object and resolve the resource requirements from configuration
        self.resource_provider = ResourceProvider(self.args)
        self.resource_provider.resolve_configuration(self.config)
        return True

    # Parse Command line arguments
    def __parseArguments(self):
        parser = get_tc_arguments( get_base_arguments( get_parser() ) )
        self.args, self.unknown = parser.parse_known_args()

    def setArgs(self, args):
        self.args = args

    def __removeHandlers(self, logger):
        while True:
            try:
                if isinstance(logger.handlers[0], logging.FileHandler):
                    logger.handlers[0].close()
                logger.removeHandler(logger.handlers[0])
            except:
                break

    # Initialize Logging library
    def __initLogs(self):
        LogManager.init_testcase_logging(self.getTestName(), self.args.verbose, self.args.silent, self.args.color)
        self.logger = LogManager.get_bench_logger()


    # Read Environment Configuration JSON file
    def __readEnvironmentConfigurations(self):
        data = None

        env_cfg_filename = self.args.env_cfg if self.args.env_cfg != '' else './env_cfg.json'
        if os.path.exists(env_cfg_filename):
            with open(env_cfg_filename) as data_file:
                data = json.load(data_file)
        elif self.args.env_cfg != '':
            self.logger.error('Environment file %s does not exist' % self.args.env_cfg)
            return False

        if data:
            self.__env = merge(self.__env, data)
        return True


    # Read Execution Configuration file
    def __readExecutionConfigurations(self):
        tc_cfg = None
        if self.args.tc_cfg:
            tc_cfg = self.args.tc_cfg
        #TODO: this bit is not compatible with clitestManagement's --tc argument.
        elif isinstance(self.args.tc, basestring) and os.path.exists(self.args.tc+'.json'):
            tc_cfg = self.args.tc +'.json'

        if tc_cfg:
            with open(tc_cfg) as data_file:
                try:
                    data = json.load(data_file)
                    strintkey_to_intkey(data) #Fix for merging keys 1 and "1"
                    self.config = merge(self.config, data)
                except Exception as e:
                    self.logger.error("Testcase configuration read from file (%s) failed!" % tc_cfg)
                    self.logger.error(e)
                    raise TestStepError("TC CFG read fail!")

        if self.args.type:
            self.config["requirements"]["duts"]["*"] = merge(self.config["requirements"]["duts"]["*"], { "type": self.args.type})

        if self.args.bin:
            self.config["requirements"]["duts"]["*"] = merge(self.config["requirements"]["duts"]["*"], { "application": {'bin': self.args.bin }})

        self.Name = self.config['name']

    def __extClassLoader(self, cp, type="ExtApps"):
        cp = "mbed_clitest."+type+"." + cp
        return loadClass(cp)

    def __loadExtensions(self):
        self.extensions = []
        benchpath = dirname(abspath(__file__))
        for root, dirs, files in os.walk(join(benchpath, "Extensions")):
            for file in sorted(files):
                basename, extension = os.path.splitext( file )
                if basename in Extensions:
                    self.logger.debug("Loading extension: %s" % basename)
                    extension = self.__extClassLoader( Extensions[basename], type="Extensions")
                    if extension is None:
                        raise AttributeError("Unable to load class %s" % Extensions[basename])
                    self.extensions.append( extension(bench=self) )



    # All required external services starting here
    def __startExternalServices(self):
        for app in self.config['requirements']['external']['apps']:
            # Check if we have an environment configuration for this app
            conf = app

            try:
                conf = merge(conf, self.__env["extApps"][app["name"]])
            except KeyError:
                self.logger.warning("Unable to merge configuration for app %s" % app["name"], exc_info = True if not self.args.silent else False)

            if 'name' in app and app['name'] in ExtApps:
                apptype = self.__extClassLoader(ExtApps[app['name']])
                if apptype is None:
                    raise AttributeError("Unable to load class %s" % ExtApps[app['name']])
                newapp = apptype(app['name'], conf=conf, bench=self)
                self.__externalServices.append(newapp)
                newapp.start()
                self.__dict__[app['name']] = newapp
                self.logger.info("done")
            else:
                conf_path = None
                conf_cmd = None
                try:
                    conf_path = conf["path"]
                except:
                    self.logger.warning("No path defined for app %s" % app["name"])

                try:
                    conf_cmd = conf["cmd"]
                except:
                    self.logger.warning("No command defined for app %s" % app["name"])
                appname = app['name'] if 'name' in app else 'generic'
                newapp = GenericProcess(name=appname, path=conf_path, cmd=conf_cmd)
                newapp.ignoreReturnCode = True
                self.__externalServices.append(newapp)
                newapp.start_process()

    # Stop all external services
    def __stopExternalServices(self):
        for service in self.__externalServices:
            self.logger.debug("Stopping application %s" % service.name)
            if service:
                service.stop()
            del service

    # Get Skip state
    def skip(self):
        try:
            return self.config['execution']['skip']['value']
        except:
            return None

    def skip_info(self):
        try:
            return self.config['execution']['skip']
        except:
            return None

    # Get Skip Reason
    def skipReason(self):
        try:
            return self.config['execution']['skip']['reason']
        except:
            return ''

    # Get TC implementation Status
    def status(self):
        try:
            return self.config['status']
        except:
            return None

    # Get Testcase Type
    def type(self):
        try:
            return self.config['type']
        except:
            return None

    def subtype(self):
        try:
            return self.config['subtype']
        except:
            return None

    # Get Test Bench Name
    def getTestName(self):
        try:
            return self.config["name"]
        except:
            return "unknown"

    def getFeaturesUnderTest(self):
        try:
            fea = self.config["feature"]
            if isinstance(fea, str):
                return [fea]
            return fea
        except:
            return []

    def getTestComponent(self):
        try:
            return self.config["component"]
        except:
            return ''

    # get TC metadata
    def getMetadata(self):
        return self.config

    def getResult(self, tc_file=None):
        result = Result()
        result.setTcMetadata( self.config )
        if self.resource_provider:
            result.dutCount = self.resource_provider.get_resource_configuration().count_duts()

            if self.resource_provider.get_resource_configuration().count_hardware() > 0:
                result.dutType = 'hw'
                # @todo need to link mbed-ls with clitest
                result.dutVendor = 'Atmel',
                result.dutModel = 'sam4eXplained'
                #result.dutSn = ''
            elif self.resource_provider.get_resource_configuration().count_process() > 0:
                result.dutType = 'process'

        if hasattr(self, "args"):
            if hasattr(self.args, "branch"): result.branch = self.args.branch
            if hasattr(self.args, "commitId"): result.commitId = self.args.commitId
            if hasattr(self.args, "gitUrl"): result.gitUrl = self.args.gitUrl
            if hasattr(self.args, "buildUrl"): result.buildUrl = self.args.buildUrl
            if hasattr(self.args, "campaign"): result.campaign = self.args.campaign
            if hasattr(self.args, "jobId"): result.jobId = self.args.jobId
        else:
            self.__parseArguments()

        if "commitid" in self.__test_git_info:
            result.commitId = self.__test_git_info['commitid']
        if "branch" in self.__test_git_info:
            result.branch = self.__test_git_info['branch']
        if "scm_link" in self.__test_git_info:
            result.gitUrl = self.__test_git_info['scm_link']
        result.tc_git_info = self.__test_git_info

        # regonize filepath and git information
        result.tc_git_info = get_git_info( self.get_tc_abspath(tc_file), verbose=self.args.verbose )
        self.logger.debug(result.tc_git_info)

        result.component = self.getTestComponent()
        if isinstance(result.component, str):
            result.component = [ result.component ]

        result.feature = self.getFeaturesUnderTest()

        result.logpath = os.path.abspath(LogManager.get_base_dir())

        if not self.skipReason() or self.args.tc:
            result.fail_reason = self.__failReason
        else:
            result.fail_reason = ''
        if not self.args.tc:
            result.skip_reason = self.skipReason()
        result.logfiles = LogManager.get_logfiles()

        result.retcode = self.__retcode

        return result

    def verifyTrace(self, k, expectedTraces, breakInFail = True):

        if isinstance(k, str):
            dutIndex = self.get_dut_index(k)
            return self.verifyTrace(dutIndex, expectedTraces, breakInFail)

        ok = True
        try:
            ok = verifyMessage(self.duts[k-1].traces, expectedTraces)
        except Exception as inst:
            ok = False
            if breakInFail:
                raise inst
        if ok == False and breakInFail:
            raise LookupError("Unexpected message found")
        return ok

    def verifyTraceSkipFail(self, k, expectedTraces, breakInFail = False):
        ok = True
        try:
            ok = verifyMessage(self.duts[k-1].traces, expectedTraces)
        except Exception as inst:
            ok = False
            if breakInFail:
                raise inst
        if ok == False and breakInFail:
            raise LookupError("Unexpected message found")
        return ok

    # Get Dut count
    def getDutCount(self):
        return len(self.duts)

    # Get range for self.duts -array
    def get_dut_range(self, i=0):
        return range(1+i, self.resource_provider.get_resource_configuration().count_duts()+i+1)

    def __getNetworkLogFilename(self):
        return LogManager.get_testcase_logfilename("network.nw.pcap")

    def reset_dut(self, k='*'):
        if( k == '*' ):
            for i in self.get_dut_range():
                if self.is_my_dut(i):
                    self.reset_dut(i)
            return
        method=None
        if self.args.reset == "hard" or self.args.reset == "soft":
            self.logger.debug("Sending reset {} to dut {}".format(self.args.reset, k-1))
            method = self.args.reset
        self.duts[k-1].reset(method)
        self.duts[k-1].initCLI()


    def is_hardware_in_use(self):
        return self.config["requirements"]["duts"]["*"]["type"] == "hardware"


    def __solve_requirements(self):
        dut_requirements = self.get_dut_requirements()
        for i, dut_requirement in enumerate(dut_requirements):
            self.config["requirements"]["duts"][i+1] = dut_requirement
        return dut_requirements

    # Internal function to Initialize cli dut's
    def __initDuts(self):

        # Initialize command line interface
        self.logger.info("---------------------")
        self.logger.info("Initialize DUT's connections")

        self.duts = self.resource_provider.initialize_duts(self.DEFAULT_BIN)

        if self.args.reset:
            self.reset_dut()

        # @TODO: Refactor this into some more sensible way
        for i in self.get_dut_range(-1):
            if self.is_my_dut(i+1):
                self.duts[i].Testcase = self.Name
                if not self.args.reset:
                    self.duts[i].initCLI()

        for i in self.get_dut_range(-1):
            if self.is_my_dut(i+1):
                self.logger.debug("DUT[%i]: %s" % (i, self.duts[i].comport))

    def delay(self, seconds):
        self.logger.debug( "Waiting for %i seconds" % seconds)
        if seconds < 30:
            time.sleep(seconds)
        else:
            while seconds > 10:
                self.logger.debug( "..Still waiting...%i seconds remain" % seconds)
                time.sleep(10)
                seconds = seconds - 10
            time.sleep(seconds)

    def waitForStableNetwork(self, delay=10):
        self.delay(delay)

    def get_node_index_by_address(self, address, addressType):
        for i in self.get_dut_range():
            dutAddress = self.duts[i-1].mesh0['address'][addressType]
            if dutAddress != None and dutAddress == address:
                return i;
        return None

    # pause test execution and continue after ENTER is pressed
    def pause(self):
        print("Press [ENTER] to continue")
        resp = sys.stdin.readline().strip()

    # input data from user
    def input_from_user(self, title=None):
        if title: print(title)
        print("Press [ENTER] to continue")
        resp = sys.stdin.readline().strip()
        if resp != '':
            return resp.strip()
        return ""

    # Open Putty (/or kitty if exists)
    # @param k, number 1.<max duts> or '*' to open putty to all devices
    # @param wait  wait while putty is closed before continue testing
    def open_node_terminal(self, k='*', wait=True):

        if k=='*':
            for i in self.get_dut_range():
                self.open_node_terminal(i, wait)
            return

        if not self.is_my_dut(k):
            return

        params = '-serial '+self.duts[k-1].comport + ' -sercfg '+str(self.duts[k-1].serialBaudrate)

        puttyExe = self.__env['extApps']['puttyExe']
        if os.path.exists(self.__env['extApps']['kittyExe']):
            puttyExe = self.__env['extApps']['kittyExe']

        if "kitty.exe" in puttyExe:
            params = params+' -title "'+self.duts[k-1].comport

            params += ' - '+ self.getTestName()
            params += ' | DUT'+str(k)+' '+self.get_dut_nick(k)+'"'
            params += ' -log "'+LogManager.get_testcase_logfilename('DUT%d.manual' % k) + '"'

        if os.path.exists(puttyExe):

            command = puttyExe+' '+params
            self.logger.info(command)
            if wait:
                if self.is_my_dut(k):
                    self.duts[k-1].Close()
                    process = subprocess.Popen(command)
                    time.sleep(2)
                    process.wait()
                    self.duts[k-1].Open()
            else:
                pid = subprocess.Popen(command, close_fds=True).pid
        else:
            self.logger.warning('putty not exists in path: %s' % puttyExe)

    def killProcess(self, apps_to_kill):
        for app in apps_to_kill:
            os.system("taskkill /F /im "+app)

    def __set_failure(self, retcode, reason):
        if self.__retcode == None or self.__retcode == 0:
            self.__retcode = retcode
            self.__failReason = reason
            self.logger.error("Test Case fails because of: %s", reason)
        else:
            self.logger.info("another fail reasons: %s"%reason)

    # run Test Bench and Test Case
    def run(self):

        skip_case = self.args.skip_case

        try:
            result = self.__initialize()
            if not result:
                self.__set_failure(ReturnCodes.RETCODE_FAIL_INITIALIZE_BENCH, "Exception while initialization")
                return self.__prepare_exit()
        except Exception as err:
            self.logger.error("Initialize causes exception", exc_info=True)
            self.__set_failure( ReturnCodes.RETCODE_FAIL_INITIALIZE_BENCH, "Exception while initialization")
            return self.__prepare_exit()
        if self.integer_keys_found:
            self.logger.warning("Integer keys found in configuration for DUT requirements. "
                             "Keys forced to strings for this run. "
                             "Please update your DUT requirements keys to strings.")

        self.logger.info("Start Test case '%s'" % self.getTestName())

        if self.args.verbose:
            self.logger.info("Environment configurations:")
            self.logger.info(pformat(self.__env))
            self.logger.info("TC configurations:")
            self.logger.info(pformat(self.config))

        try:
            self.logger.info("====setUpTestBench====")
            self.__setUpBench()
        except EnvironmentError as err:
            self.logger.error("setUpBench Throw environment error", exc_info=True if not self.args.silent else False)
            self.__tearDownBench()
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            return self.__prepare_exit()
        except TestStepTimeout as err:
            self.__tearDownBench()
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            return self.__prepare_exit()
        except TestStepFail as err:
            self.__tearDownBench()
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            return self.__prepare_exit()
        except NameError as err:
            self.logger.error("setUpBench Throw NameError exception")
            self.logger.error( err, exc_info=True if not self.args.silent else False )
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            self.__tearDownBench()
            return self.__prepare_exit()
        except (KeyboardInterrupt, SystemExit):
            # shut down tc directly
            self.logger.warning("Keyboard/SystemExit request - shut down TC")
            self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
            self.__tearDownBench()
            return self.__prepare_exit()
        except Exception as err:
            self.logger.error("setUpBench Throw exception", exc_info=True if not self.args.silent else False )
            self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_BENCH, str(err))
            self.__tearDownBench()
            return self.__prepare_exit()


        if not self.args.skip_setup:
            if hasattr(self, 'setUp'):
                try:
                    self.logger.info("------TC SET UP---------")
                    self.setUp()
                except TestStepTimeout as err:
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    self.__tearDownBench()
                    return self.__prepare_exit()
                except TestStepFail as err:
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    skip_case = True
                except TestStepError as err:
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    self.__tearDownBench()
                    if not self.args.silent:
                        err.detailedInfo()
                    return self.__prepare_exit()
                except KeyboardInterrupt:
                    self.logger.error("TC setUp aborted by user")
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
                    self.__tearDownBench()
                    return self.__prepare_exit()
                except Exception as err:
                    self.logger.error("TC setUp Throw exception")
                    self.logger.error( err, exc_info=True if not self.args.silent else False )
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_SETUP_TC, str(err))
                    self.__tearDownBench()
                    return self.__prepare_exit()
        else:
            self.logger.info("Skip TC setUp")

        if not skip_case:
            self.logger.info("------TC START---------")
            try:
                self.case()
                self.__retcode = ReturnCodes.RETCODE_SUCCESS
            except TestStepTimeout as err:
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
                self.__tearDownBench()
                return self.__prepare_exit()
            except TestStepFail as err:
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except TestStepError as err:
                self.logger.error(err, exc_info=True if not self.args.silent else False)
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
                if not self.args.silent:
                    err.detailedInfo()
            except NameError as err:
                self.logger.error( err, exc_info=True if not self.args.silent else False )
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except LookupError as err:
                self.logger.error( err, exc_info=True if not self.args.silent else False )
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except ValueError as err:
                self.logger.error( err, exc_info=True if not self.args.silent else False )
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
            except KeyboardInterrupt:
                self.logger.info("Test Case aborted by user")
                self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
            except Exception as err:
                self.logger.error("case Throw exception", exc_info=True if not self.args.silent else False )
                self.__set_failure(ReturnCodes.RETCODE_FAIL_TC_EXCEPTION, str(err))
                if not self.args.silent:
                    traceback.print_exc()

            self.logger.info("------TC END-----------")
            if self.__retcode == ReturnCodes.RETCODE_SUCCESS and self.__PreliminaryVerdict is not False:
                self.logger.debug("TC PASS")
            else:
                self.logger.debug("TC FAIL")
        else:
            self.logger.info("Skip TC case")


        if not self.args.skip_teardown:
            if hasattr(self, 'tearDown'):
                try:
                    self.logger.info("====TC TEAR DOWN====")
                    self.tearDown()
                except TestStepTimeout as err:
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    self.__tearDownBench()
                    return self.__prepare_exit()
                except TestStepFail as err:
                    self.__tearDownBench()
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    return self.__prepare_exit()
                except TestStepError as err:
                    self.logger.error(err, exc_info=True if not self.args.silent else False)
                    self.__tearDownBench()
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    if not self.args.silent:
                        err.detailedInfo()
                    return self.__prepare_exit()
                except KeyboardInterrupt:
                    self.logger.error("TC tearDown aborted by user")
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_ABORTED_BY_USER, "Aborted by user")
                    self.__tearDownBench()
                    return self.__prepare_exit()
                except Exception as err:
                    self.logger.error("tearDown Throw exception", exc_info=True if not self.args.silent else False )
                    self.__set_failure(ReturnCodes.RETCODE_FAIL_TEARDOWN_TC, str(err))
                    if not self.args.silent:
                        traceback.print_exc()
                    self.__tearDownBench()
                    return self.__prepare_exit()
        else:
            self.logger.info("Skip TC tearDown")

        # end
        self.__tearDownBench()

        if self.args.putty:
            self.open_node_terminal('*', wait=False)

        retcode = self.__prepare_exit()
        return retcode

    # Init test bench
    def __setUpBench(self):

        if self.args.kill_putty:
            self.logger.debug("Kill putty/kitty processes")
            self.killProcess(['kitty.exe', 'putty.exe'])

        self.__loadExtensions()

        if self.resource_provider.get_resource_configuration().count_duts() > 0:
            self.logger.info("====setUpTestBench====")

            self.__initDuts()

            self.starttime = time.time()

        else:
            self.logger.debug("This TC doesn't use DUT's at all :o")
            self.__PreliminaryVerdict = True

        # Start External services/applications
        self.__startExternalServices()
        self.__send_pre_commands(self.args.pre_cmds)

    def __send_pre_commands(self, cmds=""):
        # Execute DUT-specific pre-commands
        for k, conf in enumerate(self.resource_provider.get_resource_configuration().get_dut_configuration()):
            if "pre_cmds" in conf:
                for cmd in conf["pre_cmds"]:
                    self.executeCommand(k+1, cmd)
        if cmds and len(cmds) > 0:
            if cmds.startswith('file:'):
                # @todo
                #filename = cmds[5,]
                #self.logger.info("Reading pre-cmds file: %s"%filename)
                #data = {}
                #with open(filename) as cmd_file:
                #    data = json.load(cmd_file)
                raise NotImplementedError('"--pre-cmds" -option with file not supported')
            else:
                self.executeCommand('*', cmds)


    def __tearDownBench(self):
        self.logger.info("====tearDownTestBench====")

        try:
            # try to close node's by nicely by `exit` command
            # if it didn't work, kill it by OS process kill command
            # also close reading threads if any
            if self.duts:
                self.logger.debug("Close node connections")
                for i in self.get_dut_range(-1):
                    if self.is_my_dut(i+1):
                        try:
                            self.duts[i].Close(usePrepare = True)
                        except Exception as exc:
                            self.logger.error("Exception while closing dut %s!" % self.duts[i].dutName, exc_info=True if not self.args.silent else False)
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
        except Exception as err:
            self.logger.error("Exception while closing duts!", exc_info=True if not self.args.silent else False)

        self.logger.debug("delete duts")
        del self.duts



        self.resource_provider.cleanup()

        self.logger.debug("Stop external services if any")
        self.__stopExternalServices()

    def is_my_dut(self, k):
        if self.args.my_duts:
            myduts = self.args.my_duts.split(',')
            if str(k) in myduts:
                return True
            return False
        else:
            return True

    def __waitForExecuteExternalDutCommand(self, k, command):

        if self.args.pause_when_external_dut:
            nick = self.get_dut_nick(k)
            print("Press [ENTER] when %s execute command '%s'" % (nick, command))
            resp = sys.stdin.readline().strip()
            if resp != '':
                raise EnvironmentError("%s fail command" % nick)

    def get_dut_versions(self):
        resps = self.command('*', "nname")
        for i, resp in enumerate(resps):
            self.duts[i].version = resp.parsed

    def get_dut_nick(self, k):
        nick = str(k)
        if k in self.config["requirements"]["duts"] and 'nick' in self.config["requirements"]["duts"][k]:
            return self.config["requirements"]["duts"][k]['nick']
        return nick

    def get_dut_index(self, nick):
        for k,d in enumerate(self.resource_provider.get_resource_configuration().get_dut_configuration()):
            if "nick" in d and d["nick"] == nick:
                return k+1
        else:
            raise ValueError("Cannot find DUT by nick '%s'" % nick)


    ''' Do Command request for DUT
        \param k         index where command is sent, '*' -send command for all duts
        timeout   command timeout in seconds
        wait      for special cases when retcode is not wanted to wait
        expectedRetcode expecting this retcode, default: 0, can be None when it is ignored
        async       send command, but wait for response in parallel. When sending next command previous response will be wait
                    When using async mode, response is dummy
        reportCmdFail    If True (default), exception is thrown on command execution error.
    '''
    def executeCommand(self, k, cmd, wait = True, expectedRetcode = 0, timeout=50, async = False, reportCmdFail = True):
        ret = None
        if not reportCmdFail:
            expectedRetcode = None
            self.logger.warning("Deprecated usage of reportCmdFail")
        if( k == '*'):
            ret = self.__sendCmdToAll(cmd, wait=wait, expectedRetcode=expectedRetcode, timeout=timeout, async=async, reportCmdFail=reportCmdFail)
        else:
            ret = self.__executeCommand(k, cmd, wait=wait, expectedRetcode=expectedRetcode, timeout=timeout, async=async, reportCmdFail=reportCmdFail)
        return ret

    # Private functions

    # send commands to all duts
    def __sendCmdToAll(self, cmd, wait = True, expectedRetcode = 0, timeout=50, async=False, reportCmdFail = True):
        resps = []
        for i in self.get_dut_range():
            resps.append( self.__executeCommand(i, cmd,  wait=wait, expectedRetcode=expectedRetcode, timeout=timeout, async=async, reportCmdFail=reportCmdFail) )
        return resps

    def check_hang(self):
        pass

    # internal command sender
    def __executeCommand(self, k, cmd, wait = True, expectedRetcode = 0, timeout = 50, async = False, reportCmdFail = True):

        self.check_hang()

        if isinstance(k, str):
            dutIndex = self.get_dut_index(k)
            return self.__executeCommand(dutIndex, cmd, wait, expectedRetcode, timeout, async, reportCmdFail)

        if k > len(self.duts) or k < 1:
            self.logger.error("Invalid DUT number")
            raise ValueError("Invalid DUT number when calling executeCommand(%i)" % (k))

        if not self.is_my_dut(k):
            self.__waitForExecuteExternalDutCommand(k, cmd)
            return CliResponse()

        try:
            #construct command object to be execute
            timestamp = time.time()
            req = CliRequest(cmd, timestamp = timestamp, wait = wait, expectedRetcode = expectedRetcode, timeout = timeout, async = async, dutIndex = k)
            #execute command
            req.response =  self.duts[k-1].executeCommand(req)

            if wait and not async:
                # There should be valid responses
                if expectedRetcode is not None:
                    # reconfigure preliminary verdict
                    # print only first failure
                    if self.__PreliminaryVerdict is None:
                        #init first preliminary when calling first time
                        self.__PreliminaryVerdict = req.response.retcode == req.expectedRetcode
                        if self.__PreliminaryVerdict is False:
                            self.logger.warning("command fails - set preliminaryVerdict as FAIL")
                    elif req.response.retcode != req.expectedRetcode:
                        if self.__PreliminaryVerdict is True:
                            #if any command fails, it mean that TC fails
                            self.__PreliminaryVerdict = False
                            self.logger.warning("command fails - set preliminaryVerdict as FAIL")
                    # Raise expection if command fails
                    if req.response.retcode != req.expectedRetcode:
                        self.commandFail(req)
                # Parse response
                parsed = self.parse(cmd.split(' ')[0].strip(), req.response)
                if parsed is not None:
                    req.response.parsed = parsed
                    if len(parsed.keys()) > 0:
                        self.logger.info(parsed)
            return req.response

        except (KeyboardInterrupt, SystemExit):
            # shut down tc directly
            self.logger.warning("Keyboard/SystemExit request - shut down TC")
            self.commandFail(CliRequest(), "Aborted by user")

    def __prepare_exit(self):
        if self.__retcode is None:
            if self.__PreliminaryVerdict:
                self.__retcode = ReturnCodes.RETCODE_SUCCESS
            else:
                self.__retcode = ReturnCodes.RETCODE_FAIL_NO_PRELIMINARY_VERDICT
        self.logger.debug("retcode: %d, preliminaryVerdict: %s" % (self.__retcode, self.__PreliminaryVerdict))
        if self.__retcode == ReturnCodes.RETCODE_SUCCESS and self.__PreliminaryVerdict is not False:
            self.logger.info("Test '%s' PASS" % (self.getTestName()))
        else:
            self.logger.warning("Test '%s' FAIL, reason: %s" %( self.getTestName(), self.__failReason))

        return self.__retcode

    def commandFail(self, req, failReason = None):

        self.logger.error('Test step fails!')

        if failReason:
            raise NameError(failReason)
        if req.response:
            if len(req.response.lines) > 0:
                self.logger.debug("Last command response from D%s:" % req.dutIndex )
                self.logger.debug('\n'.join(req.response.lines))

            if req.response.timeout:
                raise TestStepTimeout("dut"+str(req.dutIndex)+" TIMEOUT, cmd: '"+req.cmd+"'")
            else:
                reason = "dut"+str(req.dutIndex)+" cmd: '"+req.cmd+"',"
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
