# Icetea

`icetea` is the entry-point for test execution.

## Installation

You can install `Icetea` with all required python dependencies
easily with this command:

`/> python setup.py install`

If everything goes well you can start tests from any location.
The test cases must be located under the `./testcases` subfolder,
OR you can set the testcase
root folder manually with `Icetea` option: `--tcdir`.

### Dependencies

To use `Icetea`, make sure that you have the following tools
available in your computer. Python modules should be automatically
installed by `Icetea` installation.

* Python (2.7<)
* pip (python package manager)
 * download: https://bootstrap.pypa.io/get-pip.py
 * python get-pip.py
* pip modules
 * pyserial version > 2.5(`pip install pyserial>2.5`
 or https://pypi.python.org/pypi/pyserial)
 * jsonmerge (`pip install jsonmerge`)
 * pyshark (`pip install pyshark`)
 * yattag (`pip install yattag`)
 * prettytable (`pip install prettytable`)
 * requests (`pip install requests`)
 * coverage (`pip install coverage`), for unit tests.
 * mock  (`pip install mock`), for unit tests.
 * coloredlogs (`pip install coloredlogs`), optional
 * semver (`pip install semver`)
 * six (`pip install six`)
 * mbed-ls (`pip install mbed-ls`)
 * netifaces (`pip install netifaces`), for unit tests
 * pydash (`pip install pydash`)
 * transitions (`pip install transitions`)
 * Mbed-flasher (`pip install mbed-flasher`)

## Folder structure

```
/icetea> tree
├───doc         // these documents
├───doc-source  // these documents in rst format
├───examples    // some test case examples
├───log         // test execution logs, when running Icetea directly from GIT repository root
├───icetea_lib  // Icetea -libraries
│   ├───DeviceConnectors  // DUT connectors
│   ├───ExtApps           // test required external modules
│   ├───Extensions        // default extensions, which is loaded automatically
│   ├───build             // build object implementation
│   ├───Events            // Event system implementation
│   ├───Reports           // Reporters
│   ├───TestBench         // Test bench implementation
│   ├───Plugins           // Plugin implementation and default plugins
│   ├───Randomize         // Random seed generator implementation
│   ├───ResourceProvider  // Allocators and ResourceProvider
│   ├───TestSuite         // Test runner implementation
└───test         // unit tests
```

## Example

```
/my-testcases> tree
├───testcases
│   ├───folder
│   │   ├ test3.py
│   ├ test1.py
│   └ test2.py
├───folder2
│   ├ test22.py
└ test.py
/my-testcases> icetea --tc test3
...
/my-testcases> icetea --tcdir folder2 --tc test22
...
```

## Development

Install `Icetea` in development mode:

`/> python setup.py develop`

This allows you to modify the source code and debug easily.

## Command line parameters
Command line parameters can be given both over the command line
as well as from a configuration file. The file must be a text file,
which is formatted with one or more parameters per line,
and it can be given to Icetea with command line
parameter --cfg_file. Example configuration file is available in
[examples.](../examples/example_cli_config_file)

**Note**: If you put --cfg_file argument inside a file used as
--cfg_file, don't try to load the same file.
This will cause infinite recursion.
We try to check if the file names match and delete the new --cfg_file
argument if they match, but the check might not be foolproof.

Supported cli parameters are described below:

| Name | Description | Allowed values | Default values | Additional info |
| --- | --- | --- | --- | --- |
| -h | Show help message and exit |  |  |  |
| --listsuites | List all suites found in location set to suitedir (see --suitedir) | | |  |
| --list | List all test cases found in test case search path (see --tcdir) | | |  |
| --json | Print test case list as json instead of a table. Json contains all tc metadata. | | False |  |
| --export | Export listed test cases into a suite file.  | File path | None |  |
| --tc | Filter test cases by test case name. | Test case name as string. If you want to provide several test cases, separate them with a comma. |  |  |
| --suite | Name of suite to run |  |  |  |
| --version | Print Icetea version and exit|  |  |  |
| --clean | Empty the log directory before starting run (see --log) |  | False |  |
| --status | Filter test cases by test status |  |  |  |
| --group | Filter test cases by test group (folder) |  |  |  |
| --testtype | Filter test cases by test type | See [test case api description](tc_api.md) |  |  |
| --subtype | Filter test cases by test subtype | See [test case api description](tc_api.md) |  |  |
| --component | Filter test cases by test component-under-test  |  |  |  |
| --feature | Filter test cases by test feature|  |  |  |
| --platform_filter | Filter test cases by allowed platforms|  |  |  |
| --jobId | job unique id|  |  |  |
| --gitUrl | Set application used git url for results |  |  |  |
| --branch | Set used build branch for results |  |  |  |
| --commitId | Set used commit ID for results |  |  |  |
| --buildDate | Set build date |  |  |  |
| --toolchain | Set toolchain for results |  |  |  |
| --buildUrl | Set build url for results |  |  |  |
| --campaign | Set campaign name for results |  |  |  |
| --tcdir | Test case search directory | Any valid directory path | ./testcases |  |
| --suitedir | Test suite search directory | Any valid directory path | ./testcases/suites |  |
| --env_cfg | Use user specific environment configuration file | Valid file name or path |  |  |
| --repeat | Run test cases N times | Integer | 1 |  |
| --stop_on_failure | Stop run on first failed test case |  |  |  |
| --plugin_path | Path to a python file containing desired plugins |  |  |  |
| --failure_return_value | Set Icetea to return a failing code to caller if one or more tests fail during the run. Otherwise return value will always be 0 |  |  |  |
| --ignore_invalid_params | Ignore parameters MIcetea cannot parse instead of stopping the run (for backwards compatibility) |  |  |  |
| --parallel_flash | Enable parallel flashing of devices |  |  |  |
| --disable_log_truncate | Disable long log lines truncating. Over 10000 characters long lines are truncated by default. |  |  |  |
| --cfg_file | Read command line parameters from file | Any valid path to a configuration file |  |  |
| --log | Store logs to a specific path. Filename will be <path>/<testcase>_D<dutNumber>.log | Any valid directory | ./log |  |
| -s, --silent | Enable silent-mode (only results will be printed to console) |  |  |  |
| -v | Enable debug-level logs in console |  |  |  |
| -w | Store results to the cloud |  |  |  |
| --with_logs | Send bench.log file to the cloud when -w is used. |  |  |  |
| --reset | Reset device before executing test cases | Hard, soft or can be left empty | If left empty defaults to soft |  |
| --iface | Used NW sniffer interface name |  |  |  |
| --bin | Used binary for DUTs when process/hardware is used. NOTE: Does not affect duts which specify their own binaries | Valid file name or path |  |  |
| --tc_cfg | Test case configuration file | Valid file name or path |  |  |
| --ch | Use specific rf channel |  |  |  |
| --type | Overrides DUT type | hardware, process, serial or mbed |  |  |
| --platform_name | Overides used platform. Must be found in allowed_platforms in dut configuration if allowed_platforms is defined and non-empty |  |  |  |
| --putty | Open putty after TC executed |  |  |  |
| --skip_setup | Skip test case setup phase |  |  |  |
| --skip_case | Skip test case case function|  |  |  |
| --skip_teardown | Skip test case teardown phase |  |  |  |
| --valgrind | Analyze nodes with valgrind (linux only) |  |  |  |
| --valgrind_tool | Valgrind tool to use | memcheck, callgrind, massif |  |  |
| --valgrind_extra_params | Additional command line parameters for Valgrind |  |  |  |
| --valgrind_text | Output as text.|  |  | Mutually exclusive with --valgrind_console |
| --valgrind_console | Output as text to console.|  |  | Mutually exclusive with --valgrind_text |
| --valgrind_track_origins | Show origins of undefined values. |  |  | Used only if the Valgrind tool is memcheck |
| --use_sniffer | Use network sniffer |  |  |  |
| --my_duts | Use only some of the duts | Dut index numbers separated by commas |  |  |
| --pause_ext | Pause when external device command happens |  |  |  |
| --gdb | Run specific node with gdb debugger| Integer |  | Mutually exclusive with --gdbs and --vgdb |
| --gdbs | Run specific node with gdb server | Integer |  | Mutually exclusive with --gdb and --vgdb  |
| --vgdb | Run specific node with vgdb (debugger under Valgrind) | Integer |  | Mutually exclusive with --gdb and --gdbs  |
| --gdbs-port | Select gdbs port | Integer |  | 2345 |
| --pre-cmds | Send extra commands right after dut connection |  |  |  |
| --post-cmds | Send extra commands right before terminating dut connection |  |  |  |
| --baudrate | Use user defined serial baudrate when serial device is in use. | Integer |  |  |
| --serial_timeout | User defined serial timeout | Float | 0.01 |  |
| --serial_xonxoff | Use software flow control |  |  | |
| --serial_rtscts | Use hardware flow control |  |  | |
| --serial_ch_size | Use chunk mode with size N when writing to serial port  | Integer, -1 for pre-defined mode, N=0 for normal mode, N>0 chunk mode with size N |  |  |
| --serial_ch_delay | Use defined delay between characters. Used only when serial_ch_size > 0  | Float | 0.01 |  |
| --kill_putty | Kill old putty/kitty processes |  |  |  |
| --forceflash | Force flashing of hardware devices if binary is given. |  |  | Mutually exclusive with forceflash_once |
| --forceflash_once | Force flashing of hardware devices if binary is given, but only once. |  |  | Mutually exclusive with forceflash |
| --skip_flash | Skip flashing duts. |  |  |  |
| --sync_start | Make sure dut applications have started using 'echo' command. | Boolean | False |  |

## Results

Icetea creates the following kinds of results after execution:

### junit
  * common xml format suitable for use with Jenkins
  [test_results_analyzer](https://github.com/jenkinsci/test-results-analyzer-plugin) -plugin (for example)
  * location: `log/<timestamp>/result.junit.xml`
  * format is:
    ```
    <testsuite failures="0" tests="1" errors="0" skipped="0">
        <testcase classname="<test-name>.<platform>" name="<toolchain>" time="12.626"></testcase>
    </testsuite>
    ```
#### NOTE
The JUnit file is generated slightly differently
from the other reports due to CI.
If the run used the Icetea retry mechanism to retry failed or
inconclusive test cases, only the final attempt is displayed
in the JUnit report. The failed tries are displayed in the other
reports as normal. This functionality can be configured using the
retryReason parameter in the suite.
See [suite api](suite_api.md) for more info.

### html result summary
  * simple summary view of results
  * location: `log/<timestamp>/result.html`
  * features collapsible test case containers with links to
  relevant logs
   * **Note**: Some of the logs are only visible under
   the first test case, since they are common for all test cases
   run during the execution.

### console results
```
    +--------------+---------+-------------+-------------+-----------+----------+---------+
    | Testcase     | Verdict | Fail Reason | Skip Reason | Platforms | Duration | Retried |
    +--------------+---------+-------------+-------------+-----------+----------+---------+
    | test_cmdline |   pass  |             |             |  process  | 0.946598 |    No   |
    +--------------+---------+-------------+-------------+-----------+----------+---------+
    +----------------------------+----------------+
    |          Summary           |                |
    +----------------------------+----------------+
    |       Final Verdict        |      PASS      |
    |           count            |       1        |
    |          passrate          |    100.00 %    |
    | passrate excluding retries |    100.00 %    |
    |            pass            |       1        |
    |          Duration          | 0:00:00.946598 |
    +----------------------------+----------------+

```

## Bash command completion

Initial support for bash command completion is
provided in file `bash_completion/icetea`

You can include this file from your `.bashrc` or `.bash_profile`
files like this:

~~~
if [ -f ~/src/icetea/bash_completion/icetea ]; then
  source ~/src/icetea/bash_completion/icetea
fi
~~~


## Exit codes
IceteaManager can return four different
kinds of return codes to the command line.
These are EXIT_SUCCESS (0), EXIT_ERROR (1),
EXIT_FAIL(2) and EXIT_INCONC(3).

EXIT_SUCCESS is the default return code when the test run
completed successfully, even if there were failed testcases.
This behaviour can be modified
by setting the --failure_return_value flag. This will cause Icetea
to return EXIT_FAIL if one or more testcase in the run failed.
When using the --failure_return_value flag and
at least one inconclusive result was collected
and no failed results were found, the return code
will be set to EXIT_INCONC.
Inconclusive results are generated by errors that are not
related to the actual test case, such as environment or
configuration errors.

If an error was encountered during the test run and
the error caused the execution to cease, EXIT_ERROR is returned.
