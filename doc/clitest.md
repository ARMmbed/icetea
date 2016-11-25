# clitest

`clitest` is the entry-point for test execution.

## Installation

You can install `clitest` with all required dependencies easily with this command:

`/> python setup.py install`

If everything goes well you can start tests from any location. The test cases must be located under the `./testcases` subfolder, OR you can set the testcase root folder manually with `clitest` option: `--tcdir`.

### Dependecies

To use `clitest`, make sure that you have the following tools available in your computer. All the pip modules should be automatically installed.

* Python (2.7<)
* pip (python package manager)
    * download: https://bootstrap.pypa.io/get-pip.py
    * python get-pip.py
* pip modules
    * pyserial (`pip install pyserial` or https://pypi.python.org/pypi/pyserial)
    * jsonmerge (`pip install jsonmerge`)
    * pyshark (`pip install pyshark`)
    * yattag (`pip install yattag`)
    * prettytable (`pip install prettytable`)
    * requests (`pip install requests`)
    * coverage (`pip install coverage`)
    * mock version 1.0.1  (`pip install mock==1.0.1`)
    * psutil (`pip install psutil`)
    * coloredlogs (`pip install coloredlogs`)

## Folder structure

```
/mbed-clitest> tree
├───doc         // these documents
├───examples    // some test case examples
├───log         // test execution logs, when running clitest directly from GIT repository root
├───mbed_clitest    // clitest -libraries
│   ├───DeviceConnectors  // DUT connectors
│   ├───ExtApps           // test required external modules
│   └───Extensions        // default extensions, which are loaded automatically
├───test         // unit tests
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
├ test.py
/my-testcases> clitest --tc test3
...
/my-testcases> clitest --tcdir folder2 --tc test22
...
```

## Development

Install `clitest` in development mode:

`/> python setup.py develop`

This allows you to modify the source code and debug easily.

## Command line parameters

```
/>clitest
usage: clitest [-h]
               [--list | --listsuites | --tc TC | --suite SUITE | --clean | --version]
               [--status STATUS] [--group GROUP] [--testtype TESTTYPE]
               [--subtype SUBTYPE] [--component COMPONENT] [--jobId JOBID]
               [--gitUrl GITURL] [--branch BRANCH] [--commitId COMMITID]
               [--buildDate BUILDDATE] [--buildUrl BUILDURL]
               [--campaign CAMPAIGN] [--tcdir TCDIR] [--suitedir SUITEDIR]
               [--env_cfg ENV_CFG] [--repeat REPEAT] [--stop_on_failure]
               [--color] [--ignore_invalid_params] [--cm CM] [--check_version]
               [--log LOG] [-s] [-v] [-w] [--reset] [--bin BIN]
               [--tc_cfg TC_CFG] [--type {hardware,process}] [--putty]
               [--skip_setup] [--skip_case] [--skip_teardown] [--valgrind]
               [--valgrind_tool {memcheck,callgrind,massif}]
               [--valgrind_extra_params VALGRIND_EXTRA_PARAMS]
               [--valgrind_text | --valgrind_console]
               [--valgrind_track_origins] [--my_duts MY_DUTS] [--pause_ext]
               [--nobuf NOBUF] [--gdb GDB | --gdbs GDBS | --vgdb VGDB]
               [--gdbs-port GDBS_PORT] [--pre-cmds PRE_CMDS]
               [--baudrate BAUDRATE] [--serial_timeout SERIAL_TIMEOUT]
               [--serial_xonxoff] [--serial_rtscts]
               [--serial_ch_size SERIAL_CH_SIZE]
               [--serial_ch_delay CH_MODE_CH_DELAY] [--kill_putty]
               [--forceflash] [--interface INTERFACE]

Test Framework for Command line interface

optional arguments:
  -h, --help            show this help message and exit
  --list                List of available testcases (nothing else)
  --listsuites          List of available suites
  --tc TC               execute testcase. Give test index, name, list of
                        indices/names, or all to execute all testcases
  --suite SUITE         Run tests from suite json file <suite>
  --clean               Clean old logs
  --version             Show version
  --status STATUS       Run all testcases with status <status>
  --group GROUP         Run all testcases that have all items in
                        <group/subgroup> or <group,group2> in their group
                        path.
  --testtype TESTTYPE   Run all testcases with type <testtype>
  --subtype SUBTYPE     Run all testcases with subtype <subtype
  --component COMPONENT
                        Run All Testcases with component <component>
  --jobId JOBID         Job Unique ID
  --gitUrl GITURL       Set application used git url for results
  --branch BRANCH       Set used build branch for results
  --commitId COMMITID   Set used commit ID for results
  --buildDate BUILDDATE
                        Set build date
  --buildUrl BUILDURL   Set build url for results
  --campaign CAMPAIGN   Set campaign name for results
  --tcdir TCDIR         Search for testcases in directory <path>
  --suitedir SUITEDIR   Search for suites in directory <path>
  --env_cfg ENV_CFG     Use user specific environment configuration file
  --repeat REPEAT       Repeat testcases N times
  --stop_on_failure     Stop testruns/repeation on first failed TC
  --color               Indicates if console logs are printed plain or with
                        colours. Default is False for plainlogs.
  --ignore_invalid_params
                        Disables checks for invalid parameters.
  --cm CM               name of module that is to be used to sendresults to a
                        cloud service.
  --check_version       Enables version check for test cases.
  --valgrind_text       Output as Text. Default: xml format
  --valgrind_console    Output as Text to console. Default: xml format
  --gdb GDB             Run specific process DUT with gdb (debugger). e.g.
                        --gdb 1
  --gdbs GDBS           Run specific process DUT with gdbserver (debugger).
                        e.g. --gdbs 1
  --vgdb VGDB           Run specific process DUT with vgdb (debugger under
                        valgrind). e.g. --vgdb 1

--tc arguments:
  --log LOG             Store logs to specific path. Filename will be
                        <path>/<testcase>_D<dutNumber>.log
  -s, --silent          Silent mode, only prints results
  -v, --verbose         increase output verbosity (print dut traces)
  -w                    Store results to a cloud service
  --reset               reset device before executing test cases
  --bin BIN             Used specific binary for DUTs, when process DUT is in
                        use
  --tc_cfg TC_CFG       Testcase Configuration file
  --type {hardware,process}
                        Overrides DUT type.
  --putty               Open putty after TC executed
  --skip_setup          Skip TC setUp phase
  --skip_case           Skip TC body phase
  --skip_teardown       Skip TC tearDown phase
  --valgrind            Analyse nodes with valgrind (linux only)
  --valgrind_tool {memcheck,callgrind,massif}
                        Valgrind tool to use.
  --valgrind_extra_params VALGRIND_EXTRA_PARAMS
                        Additional command line parameters to valgrind.
  --valgrind_track_origins
                        Show origins of undefined values. Default: false; Used
                        only if the Valigrind tool is memcheck
  --my_duts MY_DUTS     Use only some of duts. e.g. --my_duts 1,3
  --pause_ext           Pause when external device command happens
  --nobuf NOBUF         do not use stdio buffers in node process
  --gdbs-port GDBS_PORT
                        select gdbs port
  --pre-cmds PRE_CMDS   Send extra commands right after DUT connection
  --baudrate BAUDRATE   Use user defined serial baudrate (when serial device
                        is in use)
  --serial_timeout SERIAL_TIMEOUT
                        User defined serial timeout (default 0.01)
  --serial_xonxoff      Use software flow control
  --serial_rtscts       Use Hardware flow control
  --serial_ch_size SERIAL_CH_SIZE
                        use chunck mode with size N when writing to serial
                        port. (default N=-1: use pre-defined mode, N=0:
                        normal, N<0: chunk-mode with size N
  --serial_ch_delay CH_MODE_CH_DELAY
                        User defined delay between characters. Used only when
                        serial_ch_size>0. (default 0.01)
  --kill_putty          Kill old putty/kitty processes
  --forceflash          Force flashing of hardware device if binary is given.
                        Defaults to False
  --interface INTERFACE
                        Network interface used in tests, unless the testcase
                        specifies which one to use. Defaults to eth0


```

## Bash command completion

Initial support for bash command completion is provided in file `bash_completion/clitest`

You can include this file from your `.bashrc` or `.bash_profile` files like this:

~~~
if [ -f ~/src/mbed-clites/bash_completion/clitest ]; then
  source ~/src/mbed-clites/bash_completion/clitest
fi
~~~

