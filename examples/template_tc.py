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

'''
    Sample test case

    This Sample test case purpose is to show how to implement new test cases with mbedtest framework.
    Framework itself manages Test Bench with given parameters ( Bench.__init__(...) ). With those parameters,
    user can manage all TC related and required details, like what is TC name, status and type, what is purpose,
    how many devices it needs etc..

    Test Bench parameters can be overridden by calling "--tc_cfg <json-file>" -parameter.
    Also some individual configs can be overridden by command line parameters, like:
    duts type (--type <type>)

    All Test functions are "happy-day-functions" -by default which should pass in every time.
    If function fails it raises TestStepError or TestStepFail exception and start doing tear down phases and finally end
    test case execution with FAILURE -status (retcode != 0).

'''
# Import Bench Class
from mbed_test.bench import Bench

# All TC related stuff should be inside Testcase class
class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="template",               # short name for testcase, have to be unique, e.g. "mbedtest-sample"
                       title="Smoke sample test",   # short title

                       # Implementation Status
                       # "released"         TC is verified and are ready to be execute
                       # "development"      TC is in development and not yet ready for testing
                       # "maintenance"      TC is ready, but some why (e.g. DUT interface changes) it cannot be executed for now
                       # "broken"           Some why this TC is not working correctly, but not because of DUT. E.g. some major framework changes
                       # "unknown"          Unknown status
                       status="unknown",            # allowed values: released, development, maintenance, broken, unknown

                       # Test Case type
                       # "installation"     (just in case)
                       # "compatibility"    Verify compatibility, e.g. two different versions of DUTs
                       # "smoke"            Verify just very basic situation
                       # "regression"
                       # "acceptance"
                       # "functional"
                       # "stability"
                       # "destructive"
                       # "performance"
                       # "reliability"
                       # "functional"
                       type="acceptance",                # allowed values: installation, compatibility, smoke, regression, acceptance, alpha, beta, destructive, performance
                       # Allowed type -specific sub-types
                       # type: acceptance - sub-type: certification
                       #
                       sub_type="certification",
                       purpose="Demostrate FW TC API",  # test case purpose
                       specification_href="http://.....", #+ chapter
                       component=["thread"],  # component under test, e.g. thread, 6lowpan, mbed-client
                       feature=[],            # list of features under test
                       # Compatibility related configurations
                       # This section can be normally ignored, because all cases should be automation compatibles
                       compatible={
                           "automation": {
                               # by default all cases are automation compatible, this one is no (just for demo purpose)
                               "value": False,
                               # Reason why this is not automation compatible
                               "reason": "This is just dummy sample"
                            },
                           "hw": {
                               "value": True,
                               # there will be more information later
                           },
                           "framework":{
                               "name": "mbedtest",
                               # Version of framework required. This will be checked if you run mbedtest with --check_version
                               "version": ">1.0.0"
                               # Allowed values in semantic version format. See semver.org.
                           }
                       },

                       # This part can exists when execution should be skipped every time,
                       # of course there should be reason for that
                       # execution={
                       #    "skip": {
                       #         "value":  False,
                       #         "reason": "This is just dummy sample"}},

                       # Test case requirements
                       requirements={
                           # Device Under Test related configurations
                           "duts": {
                               # default requirements for all nodes
                               '*': {
                                    "count":10,          # Test required 10 DUTs
                                    "type": "hardware",   # allowed values: hardware(default), process
                                    "allowed_platforms": [
                                        "K64F"
                                        #,"NRF51_DK",... any mbed enabled platforms which support required test application
                                    ],
                                    "application":{
                                        # Application name and version requirements
                                        # mbedtest -verified that cliapp contains this kind of software by sending nname -command
                                        "name":"generalTestApplication",
                                        "version": "1.0",
                                        # Required node -binary (absolute/relative):
                                        # process: this process will be launched inside Bench
                                        # hardware: this file need to be flashed on board, not used directly by mbedtest
                                        "bin": "test/dut/dummyDut", # this is relative path
                                        "init_cli_cmds": [], # overwrite default dut init commands, list of commands to run
                                        "post_cli_cmds": [], # overwrite default dut post commands, list of commands to run
                                    },
                                    # Specify location: x = 0.0, y = 10.0 (units)
                                    # @note: can be overriden in dut-specific sections below
                                    "location": [0.0, 10.0],
                               },
                               # specific values for node 1
                               "1": {
                                   "nick": 'leader'       #Specify nick name for DUT 1
                                   # @note: all default requirements can be overridden in there..
                                   # "application":{
                                   #    "bin":"generalTestApplication.exe", "version": "1.2"
                                   # },
                               },
                               # specific values for node 2
                               "2": {
                                   # variables to use here:
                                   # {n}  = duts total count
                                   # {i}  = dut index
                                   "nick": 'router'
                               },
                               # Specify requirements for multiple dut's. e.g. 3-10
                               # variables to use here
                               # {n}  = duts total count
                               # {i}  = dut index
                               # {pi} = math.pi
                               # {xy} = x-axis: -> 0, y-axis -> 1
                               # you can also set math inside location,
                               #  e.g. "location: ["cos(%n/7*$n*2*$pi)*50", "sin($n/7*$n*2*$pi)*50"]
                               #  -> put 7 nodes to a circle, which distance is 50 meter
                               "3..10": { "nick": "Router{i}", "location": ["{n}", "{n}*{i}*{pi}"]}
                           }
                           # External applications which should be started before TC setUp and
                           # will be killed in end of test
                           # ,"external": {
                           #    "apps": [
                           #        {
                           #            # Some applications have their own wrapper classes, which implement methods
                           #            # and properties for use in test cases. These applications can be run along with
                           #            # the test case by just giving the name field, possible values can be found
                           #            # in ExtApps folder.
                           #            # These applications might have additional configuration parameters dependent
                           #            # on the environment, these have to be defined in env_cfg.json.
                           #            "name": "DeviceServer"
                           #        },
                           #        {
                           #            # Other applications require a configuration field as well, containing the
                           #            # application command and executable path
                           #            "name": "lighting",
                           #            "config": {
                           #                "cmd": "runLighting.bat",
                           #                "path": "../../lighting/bin"
                           #            }
                           #        }
                           #    ]
                           #}
                       }
        )

    def setUp(self):
        # All 'preconditions' for test case execution should be here
        self.logger.info("Test case setup phase started")

    def case(self):
        # Test case logic should be here
        self.logger.info("Test case started!")

    def tearDown(self):
        # All required post-conditions should be here. Cleanup, delete temporary files, shut down interfaces etc.
        self.logger.info("Test case teardown started!")
