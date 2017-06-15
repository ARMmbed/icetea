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

import argparse
import os
import uuid

parser = argparse.ArgumentParser()

def get_parser():
    parser = argparse.ArgumentParser(description='Test Framework for Command line interface')
    return parser

def get_base_arguments(parser):
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--list', action='store_true',  help='List of available testcases (nothing else)', default=False)
    group.add_argument('--listsuites', action='store_true', help='List of available suites', default=False)
    group.add_argument('--tc',  help='execute testcase. Give test index, name, list of indices/names, or all to execute all testcases', default=False)
    group.add_argument('--suite', default=False, help='Run tests from suite json file <suite>')
    group.add_argument('--clean', action='store_true', default=False, help='Clean old logs')
    group.add_argument('--version', action='store_true', default= False, help='Show version')
    #End mutually exlusive arguments
    parser.add_argument('--status', default=False, help='Run all testcases with status <status>')
    parser.add_argument('--group', default=False, help='Run all testcases that have all items in <group/subgroup> or <group,group2> in their group path.')
    parser.add_argument('--testtype', default=False, help='Run all testcases with type <testtype>')
    parser.add_argument('--subtype', default=False, help="Run all testcases with subtype <subtype")
    parser.add_argument('--component', default=False, help='Run All Testcases with component <component>')

    # JobId is BUILD_TAG (from Jenkins job), or generated UUID or command line argument value
    parser.add_argument('--jobId', default=os.environ.get('BUILD_TAG', str(uuid.uuid1())), help='Job Unique ID')
    parser.add_argument('--gitUrl', default=os.environ.get('ghprbAuthorRepoGitUrl', ''), help='Set application used git url for results')
    parser.add_argument('--branch', default=os.environ.get('GIT_BRANCH', 'master'), help='Set used build branch for results')
    parser.add_argument('--commitId', default=os.environ.get('ghprbActualCommit', ''), help='Set used commit ID for results')
    parser.add_argument('--buildDate', default='', help='Set build date')
    parser.add_argument('--buildUrl', default=os.environ.get('BUILD_URL', ''), help='Set build url for results')
    parser.add_argument('--campaign', default=os.environ.get('JOB_NAME', ''), help='Set campaign name for results')
    parser.add_argument('--tcdir', help='Search for testcases in directory <path>', default='./testcases')
    parser.add_argument('--suitedir', help='Search for suites in directory <path>', default='./testcases/suites')
    parser.add_argument('--env_cfg', help='Use user specific environment configuration file', default= '')
    parser.add_argument('--repeat', help='Repeat testcases N times', default=1)
    parser.add_argument('--stop_on_failure', help='Stop testruns/repeation on first failed TC', default=False, action="store_true")
    parser.add_argument('--color', default=False, action="store_true",
                        help='Indicates if console logs are printed plain'
                             ' or with colours. Default is False for plain'
                             'logs.')
    parser.add_argument('--ignore_invalid_params', default=False, action="store_true", help="Disables checks for invalid parameters.")

    parser.add_argument('--cm', default=None, help='name of module that is to be used to send'
                                                                              'results to a cloud service.')
    parser.add_argument("--check_version", default=False, action="store_true", help="Enables version check for test cases.")
    return parser

def get_tc_arguments(parser):

    group2 = parser.add_argument_group('--tc arguments')
    group2.add_argument('--log', default="./log", help='Store logs to specific path. Filename will be <path>/<testcase>_D<dutNumber>.log')
    group2.add_argument('-s', '--silent', action='store_true', dest='silent', default=False, help='Silent mode, only prints results')
    group2.add_argument('-v', "--verbose", dest='verbose', default=False, help="increase output verbosity (print dut traces)", action="store_true")
    group2.add_argument('-w', action='store_true', dest='cloud', default=False, help='Store results to a cloud service')
    group2.add_argument('--reset', dest='reset', action='store_true', default=False, help='reset device before executing test cases')
    group2.add_argument('--bin', help="Used specific binary for DUTs, when process DUT is in use")
    group2.add_argument('--tc_cfg', help='Testcase Configuration file')
    group2.add_argument('--type', help='Overrides DUT type.', choices=['hardware', 'process'])
    group2.add_argument('--putty', dest='putty', action='store_true', default=False, help='Open putty after TC executed')
    group2.add_argument('--skip_setup',   action='store_true', default=False, help='Skip TC setUp phase')
    group2.add_argument('--skip_case', action='store_true', default=False, help='Skip TC body phase')
    group2.add_argument('--skip_teardown', action='store_true', default=False, help='Skip TC tearDown phase')
    group2.add_argument('--valgrind', action='store_true', default=False, help='Analyse nodes with valgrind (linux only)')
    group2.add_argument('--valgrind_tool', help='Valgrind tool to use.', choices=['memcheck', 'callgrind', 'massif'])
    group2.add_argument('--valgrind_extra_params', default='', help='Additional command line parameters to valgrind.')

    # only one of the --valgrind_text or --valgrind_console is allowed
    valgrind_group = parser.add_mutually_exclusive_group()
    valgrind_group.add_argument('--valgrind_text', action='store_true', default=False, help='Output as Text. Default: xml format' )
    valgrind_group.add_argument('--valgrind_console', dest='valgrind_console', action='store_true', default=False, help='Output as Text to console. Default: xml format' )

    group2.add_argument('--valgrind_track_origins', action='store_true', default=False, help='Show origins of undefined values. Default: false; Used only if the Valigrind tool is memcheck' )
    group2.add_argument('--my_duts', dest="my_duts", help='Use only some of duts. e.g. --my_duts 1,3')
    group2.add_argument('--pause_ext', action='store_true', dest="pause_when_external_dut", default=False, help='Pause when external device command happens')

    group2.add_argument('--nobuf', help='do not use stdio buffers in node process')

    # only one of the --gdb, --gdbs or --vgdb is allowed
    gdb_group = parser.add_mutually_exclusive_group()
    gdb_group.add_argument('--gdb', type=int, help='Run specific process DUT with gdb (debugger). e.g. --gdb 1')
    gdb_group.add_argument('--gdbs', type=int, help='Run specific process DUT with gdbserver (debugger). e.g. --gdbs 1')
    gdb_group.add_argument('--vgdb', type=int, help='Run specific process DUT with vgdb (debugger under valgrind). e.g. --vgdb 1')

    group2.add_argument('--gdbs-port', dest='gdbs_port', type=int, default=2345, help='select gdbs port')

    group2.add_argument('--pre-cmds', dest='pre_cmds', help='Send extra commands right after DUT connection')
    group2.add_argument('--baudrate', dest='baudrate', type=int, help='Use user defined serial baudrate (when serial device is in use)')
    group2.add_argument('--serial_timeout', type=float, default=0.01, help='User defined serial timeout (default 0.01)')
    group2.add_argument('--serial_xonxoff', action='store_true', default=False, help='Use software flow control')
    group2.add_argument('--serial_rtscts', action='store_true', default=False, help='Use Hardware flow control')
    group2.add_argument('--serial_ch_size',  type=int, default=-1, help='use chunck mode with size N when writing to serial port. (default N=-1: use pre-defined mode, N=0: normal, N<0: chunk-mode with size N')
    group2.add_argument('--serial_ch_delay', dest='ch_mode_ch_delay', type=float, help='User defined delay between characters. Used only when serial_ch_size>0. (default 0.01)')

    group2.add_argument('--kill_putty', action='store_true', help='Kill old putty/kitty processes')
    group2.add_argument('--forceflash', action='store_true', default=False, help='Force flashing of hardware device if binary is given. Defaults to False')

    group2.add_argument('--interface', dest='interface', default='eth0', help='Network interface used in tests, unless the testcase '
                                                              'specifies which one to use. Defaults to eth0')

    return parser
