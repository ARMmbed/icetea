## Icetea test framework

*Icetea* is an [Mbed](https://www.mbed.com) test framework written
with python. It is generally used to verify the ARM mbed
IoT Device Platform provides the operating system and cloud services.

When testing [`Mbed OS`](https://www.mbed.com/en/platform/mbed-os/)
*Icetea* allows you to execute commands remotely via
the command line interface in board (`DUT`).
The interface between the test framework and `DUT` can be
for example UART, sockets or for example stdio (process `DUT`).

More detailed documentation and information on deeper details of
the framework is available
[here in rst format](https://github.com/ARMmbed/icetea/tree/master/doc-source).
and [here in markdown format](https://github.com/ARMmbed/icetea/tree/master/doc).

### Installation

`> pip install icetea`

#### Prerequisites
Icetea supports Linux (Ubuntu preferred), Windows and OS X. Our main target is Linux.
We support both python 2.7 and 3. Some OS specific prerequisites below:

* Linux
    * python-dev and python-lxml
        `sudo apt-get install python-dev python-lxml`
    * In order to run test cases with hardware in Linux without sudo rights:
        ```
        sudo usermod -a -G dialout username
        Log out & log in back to Linux
        ```
        This command will add the user 'username' to the 'dialout' group and
        grant the required permissions to the USB ports.
* OS X
    * [XCode developer tools](http://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/)
    * [MacPorts](https://www.macports.org/install.php)
    * lxml as described
    [here](http://lxml.de/installation.html#installation):
        `STATIC_DEPS=true sudo pip install lxml`

* Windows
    * python-lxml installation is problematic on Windows since
    it usually requires build tools. It can however be installed
    from pre-built binaries.
        * Download binary for you system from the internet.
        * Navigate to the directory where you downloaded the
        binary and install it with `pip install <insert_file_name>`

#### Optional

* If you wish to decorate your console log with all kinds of colors,
install the coloredlogs module using pip. `pip install coloredlogs`
    * There have been issues with coloredlogs installation on Windows.
     We might switch to a different module at some point to enable
     colored logging on Windows as well.

### Usage

To print the help page:

`icetea --help`

To list all local testcases from the examples subfolder:

`icetea --list --tcdir examples`

To print Icetea version:

`icetea --version`

#### Typical use

All of the commands described below might also need other options,
depending on the test case.

**Running test cases using the tc argument**

`> icetea --tc <test case name> --tcdir <test case search path>`

To run all existing test cases from the `examples` folder:

`> icetea --tc all --tcdir examples`

**Running an example test case with hardware**

In this example we assume that a compatible board has been connected
to the computer and an application binary for said board is available.

`> icetea --tc test_cmdline --tcdir examples --type hardware --bin <path to a binary>`

**Using metadata filters**

To run all test cases with testtype regression in the metadata:

`> icetea --testtype regression --tcdir <test case search path>`

The following metadata filters are available:
* test type (--testtype)
* test subtype (--subtype)
* feature (--feature)
* test case name (--tc)
* tested component (--component)
* test case folder (--group)

For further details see our documentation linked
at [the top](#icetea-test-framework) of this document.

**Running a premade suite**
Icetea supports a simple suite file that describes a suite of test cases
in json format.

`> icetea --suite <suite file name> --tcdir <test case search path> --suitedir <path to suite directory>`

**Enabling debug level logging**
Add -v or -vv to the command.

#### Creating a test case
Test case creation is further described in the documentation linked at
[the top](#icetea-test-framework). An example test case is shown below:

```
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

from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_cmdline",
                       title="Smoke test for command line interface",
                       status="released",
                       purpose="Verify Command Line Interface",
                       component=["cmdline"],
                       type="smoke",
                       requirements={
                           "duts": {
                               '*': {
                                    "count": 1,
                                    "type": "hardware",
                                    "allowed_platforms": ['K64F']
                               }
                           }
                       }
                       )

    def setup(self):
        # nothing for now
        self.device = self.get_node_endpoint(1)


    def case(self):
        self.command(1, "echo hello world", timeout=5)
        self.device.command("help")

    def teardown(self):
        # nothing for now
        pass
```

#### Debugging

To debug dut 1 locally with [GDB](https://www.gnu.org/software/gdb/):

**Note:** You have to install [gdb](https://www.gnu.org/software/gdb/) first (`apt-get install gdb`)

```
> icetea --tc test_cmdline --tcdir examples --type process --gdb 1 --bin ./test/dut/dummyDut
> sudo gdb ./CliNode 3460
```

To debug dut 1 remotely with GDB server:

```
> icetea --tc test_cmdline --tcdir examples --type process --gdbs 1 --bin  ./test/dut/dummyDut
> gdb  ./test/dut/dummyDut --eval-command="target remote localhost:2345"
```

To analyze memory leaks with valgrind:

**Note:** You have to install [valgrind](http://valgrind.org) first (`apt-get install valgrind`)
```
> icetea --tc test_cmdline --tcdir examples --type process --valgrind --valgrind_tool memcheck --bin  ./test/dut/dummyDut
```

### License

See the [license](https://github.com/ARMmbed/icetea/blob/master/LICENSE) agreement.
