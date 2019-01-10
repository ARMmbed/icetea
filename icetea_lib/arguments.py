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

Arguments.py contains the cli argument parser configuration for Icetea.
"""

import argparse
import os
import uuid


def get_parser():
    """
    Get a new ArgumentParser.

    :return: ArgumentParser
    """
    parser = argparse.ArgumentParser(description='Test Framework for Command line interface')
    return parser


def get_base_arguments(parser):
    """
    Append base arguments icetea run arguments to parser.

    :param parser: argument parser
    :return: ArgumentParser
    """
    thisfilepath = os.path.abspath(os.path.dirname(__file__))
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--list',
                       action='store_true',
                       help='List of available testcases(nothing else)',
                       default=False)
    group.add_argument('--listsuites',
                       action='store_true',
                       help='List of available suites',
                       default=False)
    group.add_argument('--tc',
                       help='execute testcase. Give test index, name, list of indices/'
                            'names, or all to execute all testcases',
                       default=False)
    group.add_argument('--suite',
                       default=False,
                       help='Run tests from suite json file <suite>. Can be absolute path to '
                            'suite file or path relative to --suitedir.')
    group.add_argument('--version',
                       action='store_true',
                       default=False,
                       help='Show version')


    # Filters
    filter_group = parser.add_argument_group("Filter arguments", "Arguments used for filtering "
                                                                 "tc:s")
    filter_group.add_argument('--status', default=False,
                              help='Run all testcases with status <status>')
    filter_group.add_argument('--group',
                              default=False,
                              help='Run all testcases that have all items '
                                   'in <group/subgroup> or <group,group2> in their group path.')
    filter_group.add_argument('--testtype',
                              default=False,
                              help='Run all testcases with type <testtype>')
    filter_group.add_argument('--subtype',
                              default=False,
                              help="Run all testcases with subtype <subtype")
    filter_group.add_argument('--component',
                              default=False,
                              help='Run all testcases with component <component>')
    filter_group.add_argument('--feature',
                              default=False,
                              help='Run all testcases with feature <feature>')
    filter_group.add_argument("--platform_filter",
                              default=False,
                              help="Run all testcases that allow platform <platform_filter>")

    # JobId is BUILD_TAG (from Jenkins job), or generated UUID or command line argument value
    info_group = parser.add_argument_group("Run information", "Information of run, such as job "
                                                              "id and git or build information.")
    info_group.add_argument('--jobId',
                            default=os.environ.get('BUILD_TAG', str(uuid.uuid1())),
                            help='Job Unique ID')
    info_group.add_argument('--gitUrl',
                            default=os.environ.get('ghprbAuthorRepoGitUrl', None),
                            help='Set application used git url for results')
    info_group.add_argument('--branch',
                            default=os.environ.get('GIT_BRANCH', 'master'),
                            help='Set used build branch for results')
    info_group.add_argument('--commitId',
                            default=os.environ.get('ghprbActualCommit', None),
                            help='Set used commit ID for results')
    info_group.add_argument('--buildDate',
                            default=None,
                            help='Set build date')
    info_group.add_argument('--toolchain',
                            default=None,
                            help='Set toolchain for results')
    info_group.add_argument('--buildUrl',
                            default=os.environ.get('BUILD_URL', None),
                            help='Set build url for results')
    info_group.add_argument('--campaign',
                            default=os.environ.get('JOB_NAME', None),
                            help='Set campaign name for results')

    # Directories and paths
    directories = parser.add_argument_group("Paths", "Directory and file paths for various "
                                                     "Icetea features.")
    directories.add_argument('--tcdir',
                             help='Search for testcases in directory <path>',
                             default='./testcases')
    directories.add_argument('--suitedir',
                             help='Search for suites in directory <path>',
                             default='./testcases/suites')
    directories.add_argument("--cfg_file",
                             type=open,
                             default=None,
                             help="Load cli parameters from file. "
                                  "This will overwrite parameters given before --cfg_file, but "
                                  "results of this will be overwritten by "
                                  "parameters given after this one",
                             action=LoadFromFile)

    directories.add_argument('--plugin_path',
                             default=os.path.abspath(
                                 os.path.join(thisfilepath,
                                              "Plugin/plugins/plugins_to_load")),
                             help="location of file called plugins_to_load, "
                                  "where custom plugins are imported from.")

    # Allocator group
    alloc_group = parser.add_argument_group("Allocator", "Control allocation of resources for "
                                                         "tests.")
    alloc_group.add_argument("--allocator",
                             default="LocalAllocator",
                             help="Allocator to be used for allocating resources. "
                                  "Default is LocalAllocator")
    alloc_group.add_argument("--allocator_cfg",
                            help="File that contains configuration for used allocator.",
                            default=None)

    # Other arguments
    parser.add_argument('--env_cfg',
                        help='Use user specific environment configuration file',
                        default='')
    parser.add_argument('--repeat',
                        help='Repeat testcases N times',
                        default=1)
    parser.add_argument('--stop_on_failure',
                        help='Stop testruns/repeation on first failed TC',
                        default=False,
                        action="store_true")
    parser.add_argument('--clean',
                        action='store_true',
                        default=False,
                        help='Clean old logs')

    parser.add_argument('--connector',
                        default=None,
                        help='Connector credentials for selecting and/or generating endpoint '
                             'certificates. Format should be domain[:token] where token is '
                             'optional. Eg. --connector this_is_some_domain:this_is_my_token')
    parser.add_argument('--failure_return_value',
                        default=False,
                        action="store_true",
                        help='Sets Icetea to return a failing code to caller if '
                             'one or more tests fail during the run. Default is False')
    parser.add_argument('--color',
                        default=False,
                        action="store_true",
                        help='Indicates if console logs are printed plain'
                             ' or with colours. Default is False for plain'
                             'logs.')
    parser.add_argument("--check_version",
                        default=False,
                        action="store_true",
                        help="Enables version checks for test cases.")
    parser.add_argument('--ignore_invalid_params',
                        default=False,
                        action="store_true",
                        help="Disables checks for invalid parameters.")
    parser.add_argument('--parallel_flash',
                        default=False,
                        action="store_true",
                        help="Enables parallel flash.")
    parser.add_argument('--disable_log_truncate',
                        default=False,
                        action="store_true",
                        help="Disable long log line truncating. Over 10000"
                             "characters long lines are truncated by default.")
    parser.add_argument('--cm',
                        default="opentmi_client",
                        help='name of module that is to be used to send results to a cloud '
                             'service.')
    parser.add_argument("--json", action="store_true", default=False,
                        help="Output results of --list as json instead of a table.")
    parser.add_argument("--export", default=None, metavar="SUITE_FILE_NAME",
                        help="Export list into suite template file.")
    return parser


def get_tc_arguments(parser):
    """
    Append test case arguments to parser.

    :param parser: ArgumentParser
    :return: ArgumentParser
    """
    group2 = parser.add_argument_group('Test case arguments')
    group2.add_argument('--log',
                        default=os.path.abspath("./log"),
                        help='Store logs to specific path. Filename will be '
                             '<path>/<testcase>_D<dutNumber>.log')
    group2.add_argument('-s', '--silent',
                        action='store_true',
                        dest='silent',
                        default=False,
                        help='Silent mode, only prints results')
    group2.add_argument('-v', "--verbose",
                        dest='verbose',
                        default=False,
                        help="increase output verbosity (print dut traces)",
                        action="store_true")
    group2.add_argument('-w',
                        action='store_true',
                        dest='cloud',
                        default=False,
                        help='Store results to a cloud service.')

    group2.add_argument('--with_logs',
                        action='store_true',
                        dest='with_logs',
                        default=False,
                        help="Store bench.log to cloud db after run.")
    group2.add_argument('--reset',
                        dest='reset',
                        action='store',
                        nargs='?',
                        const=True,
                        help='reset device before executing test cases')
    group2.add_argument('--iface',
                        help="Used NW sniffer interface name")
    group2.add_argument('--bin',
                        help="Used specific binary for DUTs, when process is in use. "
                             "NOTE: Does not affect duts which specify their own binaries.")
    group2.add_argument('--tc_cfg',
                        help='Testcase Configuration file')
    group2.add_argument('--type',
                        help='Overrides DUT type.',
                        choices=['hardware', 'process'])
    group2.add_argument('--platform_name',
                        help='Overrides used platform. Must be found in allowed_platforms in '
                             'dut configuration if allowed_platforms is defined and non-empty.',
                        default=None)
    group2.add_argument('--putty',
                        dest='putty',
                        action='store_true',
                        default=False,
                        help='Open putty after TC executed')
    group2.add_argument('--skip_setup',
                        action='store_true',
                        default=False,
                        help='Skip TC setUp phase')
    group2.add_argument('--skip_case',
                        action='store_true',
                        default=False,
                        help='Skip TC body phase')
    group2.add_argument('--skip_teardown',
                        action='store_true',
                        default=False,
                        help='Skip TC tearDown phase')
    group2.add_argument('--valgrind',
                        action='store_true',
                        default=False,
                        help='Analyse nodes with valgrind (linux only)')
    group2.add_argument('--valgrind_tool',
                        help='Valgrind tool to use.',
                        choices=['memcheck', 'callgrind', 'massif'])
    group2.add_argument('--valgrind_extra_params',
                        default='',
                        help='Additional command line parameters to valgrind.')

    # only one of the --valgrind_text or --valgrind_console is allowed
    valgrind_group = parser.add_mutually_exclusive_group()
    valgrind_group.add_argument('--valgrind_text',
                                action='store_true',
                                default=False,
                                help='Output as Text. Default: xml format')
    valgrind_group.add_argument('--valgrind_console',
                                dest='valgrind_console',
                                action='store_true',
                                default=False,
                                help='Output as Text to console. Default: xml format')

    group2.add_argument('--valgrind_track_origins',
                        action='store_true',
                        default=False,
                        help='Show origins of undefined values. Default: false; '
                             'Used only if the Valgrind tool is memcheck')

    group2.add_argument('--use_sniffer',
                        dest='use_sniffer',
                        action='store_true',
                        default=False,
                        help='Use Sniffer')
    group2.add_argument('--my_duts',
                        dest="my_duts",
                        help='Use only some of duts. e.g. --my_duts 1,3')
    group2.add_argument('--pause_ext',
                        action='store_true',
                        dest="pause_when_external_dut",
                        default=False,
                        help='Pause when external device command happens')

    # only one of the --gdb, --gdbs or --vgdb is allowed
    gdb_group = parser.add_mutually_exclusive_group()
    gdb_group.add_argument('--gdb',
                           type=int,
                           help='Run specific process node with gdb (debugger). e.g. --gdb 1')
    gdb_group.add_argument('--gdbs',
                           type=int,
                           help='Run specific process node with gdbserver '
                                '(debugger). e.g. --gdbs 1')
    gdb_group.add_argument('--vgdb',
                           type=int,
                           help='Run specific process node with vgdb '
                                '(debugger under valgrind). e.g. --vgdb 1')

    group2.add_argument('--gdbs-port',
                        dest='gdbs_port',
                        type=int,
                        default=2345,
                        help='select gdbs port')
    group2.add_argument('--pre-cmds',
                        dest='pre_cmds',
                        help='Send extra commands right after DUT connection')
    group2.add_argument('--post-cmds',
                        dest='post_cmds',
                        help='Send extra commands right before terminating dut connection.')
    group2.add_argument('--baudrate',
                        dest='baudrate',
                        type=int,
                        help='Use user defined serial baudrate (when serial device is in use)')
    group2.add_argument('--serial_timeout',
                        type=float,
                        default=0.01,
                        help='User defined serial timeout (default 0.01)')
    group2.add_argument('--serial_xonxoff',
                        action='store_true',
                        default=False,
                        help='Use software flow control')
    group2.add_argument('--serial_rtscts',
                        action='store_true',
                        default=False,
                        help='Use Hardware flow control')
    group2.add_argument('--serial_ch_size',
                        type=int,
                        default=-1,
                        help='use chunck mode with size N when writing to serial port. '
                             '(default N=-1: '
                             'use pre-defined mode, N=0: normal, N<0: chunk-mode with size N')
    group2.add_argument('--serial_ch_delay',
                        dest='ch_mode_ch_delay',
                        type=float,
                        help='User defined delay between characters. '
                             'Used only when serial_ch_size>0. (default 0.01)')
    group2.add_argument('--nobuf', help="Do not use stdio buffers in node process.")
    group2.add_argument('--kill_putty',
                        action='store_true',
                        help='Kill old putty/kitty processes')

    # only one of the --forceflash, --forceflash_once is allowed
    forceflash_group = parser.add_mutually_exclusive_group()
    forceflash_group.add_argument('--forceflash',
                                  action='store_true',
                                  default=False,
                                  help='Force flashing of hardware device if binary is given. '
                                       'Defaults to False')
    forceflash_group.add_argument('--forceflash_once',
                                  action='store_true',
                                  default=False,
                                  help='Force flashing of hardware device if '
                                       'binary is given, but only once. Defaults to False')

    group2.add_argument('--interface',
                        dest='interface',
                        default='eth0',
                        help='Network interface used in tests, unless the testcase specifies '
                             'which one to use. Defaults to eth0')
    group2.add_argument("--skip_flash",
                        default=False,
                        action="store_true",
                        help="Skip flashing hardware devices during this run.")

    return parser


class Abspathify(argparse.Action):  #pylint: disable=too-few-public-methods
    """
    Action to convert paths to absolute paths.
    """
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, os.path.abspath(values))


class LoadFromFile(argparse.Action):  #pylint: disable=too-few-public-methods
    """
    Action to load more arguments into parser from a file.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        with values as fil:
            data = fil.read().split()
            if "--cfg_file" in data:
                index = data.index("--cfg_file")
                if data[index+1] == fil.name:
                    del data[index+1]
                    del data[index]
            parser.parse_args(data, namespace)
