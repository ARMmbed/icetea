# Command-line test framework

*IcedTea* is an [mbed](www.mbed.com) test framework written
with python 2.7. It is generally used to verify the ARM mbed
IoT Device Platform provides the operating system and cloud services.

When testing [`mbed OS`](https://www.mbed.com/en/platform/mbed-os/)
*IcedTea* allows you to execute commands remotely via
the command line interface in board (`DUT`).
The interface between the test framework and `DUT` can be
for example UART, sockets or for example stdio (process `DUT`).

A more detailed description of the *IcedTea* concept is
available [here](doc/README.md).

## Installation

`> python setup.py install`

When installing IcedTea, installing to a
[virtualenv](https://virtualenv.pypa.io/en/stable/installation/) is
a good idea.

### Required dependencies:

* In case you want to use **local mbed devices**
  * [mbed-ls](https://github.com/armmbed/mbed-ls)
    * To enumerate connected boards
  * [mbed-flasher](https://github.com/ARMmbed/mbed-flasher)
    * to flash devices automatically
  * Both of these should be installed automatically by
  IcedTea installation.

**OS specific:**

Linux:
* python-dev and python-lxml
`sudo apt-get install python-dev python-lxml`

OS X:
* [XCode developer tools](http://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/)
* lxml as described
[here](http://lxml.de/installation.html#installation):
`STATIC_DEPS=true sudo pip install lxml`

Windows:
* python-lxml installation is problematic on Windows since
it usually requires build tools. It can however be installed
from pre-built binaries.
    * Download binary for you system from the internet.
    * Navigate to the directory where you downloaded the
    binary and install it with `pip install <insert_file_name>`

### Optional dependencies

* If you wish to decorate your console log with all kinds of colors,
install the coloredlogs module using pip. `pip install coloredlogs`
    * There have been issues with coloredlogs installation on Windows.
     We might switch to a different module at some point to enable
     colored logging on Windows as well.
* [valgrind](http://valgrind.org)
* [gdb](https://www.gnu.org/software/gdb/)


### Installation step-by-step

```
git clone https://github.com/ARMmbed/icedtea.git
cd icedtea
python setup.py install
```

**Linux**

In order to run test cases with hardware in Linux without sudo rights:

```
sudo usermod -a -G dialout username
Log out & log in back to Linux
```

This command will add the user 'username' to the 'dialout' group and
grant the required permissions to the USB ports.

## Usage

To print the help page:

`icedtea --help`

All cli parameters are described in [icedtea.md](doc/icedtea.md)

To list all local testcases from the `./testcases` subfolder:

`icedtea --list`

## Test Case API

To execute a single command line:

` execute_command(<dut>, <cmd>, (<arguments>) ) `

or alias `command(...)`


```
dut[number]             #dut index (1..)
dut[string]             #dut nick name, or '*' to execute command in all duts
cmd[string]             #command to be executed
arguments[dictionary]   #optional argument list
        wait = <boolean>           # whether retcode is expected before continue next command. True (default) or False
        expectedRetcode = <int>    # expected return code (default=0)
        timeout=<int>              # timeout, if no retcode receive
```

## Examples

**Note:** Following examples uses [`dummyDut`](test/dut/dummyDut.c)
application. It works in unix systems.
To run following examples please compile `dummyDut` first using make:
`> make -C test/dut`.

To print available parameters:

`> icedtea --help`

To run a single test case with the process dut:

`> icedtea --tc test_cmdline --tcdir examples --type process --bin ./test/dut/dummyDut`

To run all existing test cases from the `examples` folder:

`> icedtea --tc all --tcdir examples --type process --bin ./test/dut/dummyDut`

To debug dut locally with [GDB](https://www.gnu.org/software/gdb/):

**Note:** You have to install [gdb](https://www.gnu.org/software/gdb/) first (`apt-get install gdb`)

```
> icedtea --tc test_cmdline --tcdir examples --type process --gdb 1 --bin ./test/dut/dummyDut
> sudo gdb ./CliNode 3460
```

To debug dut remotely with GDB server:

```
> icedtea --tc test_cmdline --tcdir examples --type process --gdbs 1 --bin  ./test/dut/dummyDut
> gdb  ./test/dut/dummyDut --eval-command="target remote localhost:2345"
```

To analyse memory leaks with valgrind:

**Note:** You have to install [valgrind](http://valgrind.org) first (`apt-get install valgrind`)
```
> icedtea --tc test_cmdline --tcdir examples --type process --valgrind --valgrind_tool memcheck --bin  ./test/dut/dummyDut
```

## Running unit tests with *IcedTea*

To build a test application for DUT and execute the test:

```
> make
> coverage run -m unittest discover -s test
```

To generate a coverage report (excluding plugins):

```
> coverage html --include "icedtea_lib/*" --omit "icedtea_lib/Plugin/plugins/*"
```

To run unit tests for plugins that ship with IcedTea:

```
> coverage run -m unittest discover -s icedtea_lib/Plugin/plugins/plugin_tests
```

To generate a coverage reports for plugin unit tests run:

```
> coverage html --include "icedtea_lib/Plugin/plugins/*" --omit "icedtea_lib/Plugin/plugins/plugin_tests/*"
```

### Dependencies

Unit tests depend on mock, coverage and netifaces.

```
> pip install mock
> pip install netifaces
> pip install coverage
```

## License

See the [license](LICENSE) agreement.
