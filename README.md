# mbed test framework

*mbed test* is a test framework that allows you to execute commands via the command line interface (for example in a device).

The interface between the test framework and a device can be for example UART, process or simulator. You can also connect to any other interface.

A more detailed description of the *mbed test* concept is available [here](doc/README.md).

## Installation

### Required dependencies:
Linux:
* python-dev and python-lxml `sudo apt-get install python-dev python-lxml`

First, clone this repository to the desired location, and install the test framework as follows:

```
git clone https://github.com/ARMmbed/mbed-test.git
cd mbed-test
python setup.py install
```

In order to run test cases with hardware in Linux without sudo rights:

```
sudo usermod -a -G dialout username
Log out & log in back to Linux
```

This command will add the user 'username' to the 'dialout' group and grant the required permissions to the USB ports.

## Usage

To print the help page:

`mbedtest --help`

To list all local testcases from the `./testcases` subfolder:

`mbedtest --list`

## Test Case API

To execute a single command line:

` executeCommand(<dut>, <cmd>, (<arguments>) ) `

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

To print available parameters:

`mbedtest --help`

To run a single test case from the examples folder:

`mbedtest --tc sample_process_multidut_testcase --tcdir examples`

To run all existing test cases from the `testcases` folder:

`mbedtest --tc all`


## Running unit tests with *mbed test*

To build a test application for DUT and execute the test:

```
make
coverage run -m unittest discover -s test
```

To generate a coverage report:

```
coverage html --include "mbed_test/*"
```

#Dependencies

Unit tests depend on mock, preferably version 1.0.1, version 2.0.0 is known to fail

```
pip install mock==1.0.1
```
 
## License

See the [license](LICENSE) agreement.
