# Icetea setup and first time use guide
This document is a walkthrough to the core features of
Icetea test framework. The document will take you through
installation, running unit test for Icetea and running tests with
Icetea.

To run the steps outlined in this document, we expect the user
to have a Linux environment. For further support for Windows users
please refer to other documents in this repository.

## Pre-requisites
To use Icetea effectively, we expect the user and his/her setup
to fulfill the following requirements:
* Basic knowledge of Python programming.
* Python 2.7 environment running on a linux system.
* Pip installed.
* Gcc and make installed (for process devices).

### Hardware
If hardware is to be used, the following are added to the requirements:
* Mbed-ls installed. (will be installed by installation process)
* Mbed-flasher installed (will be installed by installation process)
* One K64F device connected to host (verify that
mbed-ls can detect the device).
* Valid binaries for the device or tools to compile with

## Terms and abbreviations
This document uses the following terms and abbreviations:

| Term | Meaning |
|---| --- |
| Icetea | Host side test framework, "the product". |
| CLI | Command line interface. |
| cliapp | Device side application, which provides a command line interface. |
| DUT | Device under test. |

## About Icetea
Icetea is a host side test framework written using Python
The biggest difference to other mbed OS related test frameworks,
such as greentea, is that the host side application is the driver
for the tests and controls the entire test execution phase.
Most case logic is also implemented in host side test scripts.

More details are available in the repository documentation.

### Test case example for Hardware and process
The basic structure, requirements and features of a test case are
described in this section using a simple example test case that we
will use later for verifying that Icetea works as expected.

```
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

The code above is an example of what a test case for Icetea looks like.
It is a copy from [test_cmdline.py](examples/test_cmdline.py).

The test case is implemented as a class that subclasses the Bench
class from [icetea_lib.bench](icetea_lib/bench.py) and implements
the init method as well as the case method. The two other methods
defined in this example test case are optional.

In the init method of your test case class, you should include a call
to the Bench.__init__() method as seen in the example test case.
The initialization method takes a multitude of arguments, described in
more detail in [tc_api.md](doc/tc_api.md). These arguments contain
the test case metadata and requirements. The ones that are most
relevant for this document are the test case name (parameter "name") and
the requirements-dictionary (parameter "requirements").

The test case name must be unique for each test case. This is one of
the most common methods for filtering test cases for running from
all available test cases. In this case, the name is set to "test_cmdline".

The requirements dictionary describes the required devices under test and
required external services. External services are an advanced feature
and they are not needed in this test case, so we only include the "duts"
key in our requirements. The value for that key is another dictionary
where we describe the required devices. Under key * we can describe
common requirements and the amount of devices required. We could also
include specific requirements for each dut or a range of duts, but
the * key should always be included, with at least the amount of
required devices (even if the count is 0).

In this test case we require 1 hardware device that is a K64F
as detected by mbed-ls.

### Test case example for REST Api
```
from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_http",
                       title="Test http methods",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       requirements={
                           "duts": {
                               '*': {  # requirements for all nodes
                                   "count": 0
                               }
                           }}
                       )

    def setup(self):
        pass

    def case(self):
        #Initialize the HttpApi with the path to the server you want to contact
        http = self.HttpApi("http://mbed.org")
        #Send get request to "http://mbed.org/", should respond with 200
        resp = http.get("/", expected=200, raiseException=True)

    def teardown(self):
        pass
```

This test case demonstrates the use of the inbuilt HTTP api that
can be used for testing applications and systems that contain
a HTTP server or service that the test can access with HTTP requests.
The test case in question can be found in [sample_http.py](examples/sample_http.py).

The HttpApi tool used here is a plugin that extends its functionality
to the test bench. The api can be found in [tools](icetea_lib/tools/HTTP).
The plugin system is documented in
[plugin_framework.md](doc/plugin_framework.md).

This is a simple sample test case that requires no duts (count needs to
be set to 0, but this might change in the future).

In the case we create the HttpApi object using self.HttpApi()
and provide the base server address. The api is designed to store the
base server address so that it is easy to call multiple endpoints
in the same service without needing to always provide the full address.
Once the object has been created, we send a get request to endpoint "/".
We expect to get 200 as the return code (the default also) and want to
raise an exception and fail the test if we don't
get the expected return code.

#### Setup and teardown
Setup and teardown are optional methods that the framework calls
after test bench initialization or after the test case has finished.
These methods can be included in a test case and they should perform
setup and teardown steps needed to either bring the tested system
to the desired state before starting the actual test case or to restore
the state of devices and systems tested to a known or valid state after
the test has finished.

In this example test case we have no special setup or teardown steps,
so all we do in the setup is get a reference to the device under test
in the setup step.

#### Case
The test case logic should be implemented in the case function. This
method needs to be present in the test case class and it should perform
all logic needed to run the test case and assert the results.

In this test case we first use the generic cli command interface of
Icetea to send the command "echo hello world" to device with index 1
(note, dut indexes start from 1 in Icetea). We include a 5 second timeout.
The command is successfull if we receive retcode: 0 from the dut during
this 5 second period after sending the command.
After the command has finished, we use the same command interface
through the device reference we stored earlier in the setup to
send the command "help" to the cli on the device. Here we have a 50s
timeout (which is the default).

These calls return a response object, which contains the traces received
during the command, possible parsed data from the response traces returned
by Icetea response parsers etc.

#### Pre- and post steps
The test bench (Bench class) implements some default pre- and post-steps
for each test case. These are only somewhat configurable by the user,
since they usually perform steps that are always required, such as
allocation of resources for the test, releasing of said resources,
reporting and many others.

The most common configurable step here are cli initialization commands.
Icetea runs a set of default commands for each dut it initializes.
These commands are
```
set --retcode true
echo off
set --vt100 off
```
After the test case teardown these commands are reverted.
```
echo on
set --vt100 on
set --retcode false
```

This set of commands is configurable using the init_cli_cmds and
post_cli_cmds keys in test case requirements.
See [tc_api.md](doc/tc_api.md) for more information.

## Developing your own cliapp
Icetea was originally designed with the assumption that the
tested application contains a command line interface. Icetea comes
with simple cliapp examples for both mbed OS 3 and 5. This document
also contains some guidelines and snippets for developing your own
cliapps.

### What is a cliapp?
Any application based on the command line interface can be a valid test
application. There are some basic requirements that Icetea expects
from a cliapp, such as a set of basic commands. These requirements are:
* Each tx/rx line must be terminated by <cr><lf> or at least <lf>.
* Following commands:
    * echo off (stop echoing)
    * echo on (start echoing)
    * set --vt100 off (stop using vt100 control characters)
    * set --vt100 on (use vt100 control characters)
    * set --retcode false (stop printing retcodes)
    * set --retcode true (print retcode after each command)
* Icetea assumes that a communication block is a single line
* Icetea assumes that a commands ends on a retcode print:
    * retcode 0\r\n

The commands described above are expected default behaviours at the
start and end of a test case and they can be ignored or modified
if your application does not implement these commands.

### Implementing commands
cmd_name.h:
```
#ifndef CMD_NAME_H_
#define CMD_NAME_H_

void cmd_name_init(void);

#endif
```
cmd_name.cpp:
```
#include "mbed-client-cli/ns_cmdline.h"
#define MAN_CMD_NAME "man for command"

void cmd_name_init(void)
{
    cmd_add("cmd_name", cmd_name, "cmd_name", MAN_CMD_NAME);
}

static int cmd_name(int argc, char *argv[])
{
    // implementation of the command
    return ret_code;
}
```
main.cpp:
```
#include "cmd_name.h"

/...

void init_cmds(void)
{
    cmd_name_init();
}
//...
```

### More examples and links
More examples for mbed os 3 and mbed os 5 are available in
[examples/cliapp/mbed-os3/](examples/cliapp/mbed-os3/source/main.cpp)
[examples/cliapp/mbed-os5/](examples/cliapp/mbed-os5/source/main.cpp)

Mbed client cli library:
https://github.com/ARMmbed/mbed-client-cli/

mbed OS
https://github.com/ARMmbed/mbed-os/

## Step-by-step for first runs
1. Install Icetea
    * Clone repository from github: https://github.com/armmbed/icetea
    * Follow installation instructions: https://github.com/ARMmbed/icetea#installation
2. Build Icetea documentation:
    *   Install Sphinx `pip install sphinx`
    *   Build the documentation `sphinx-build -b html doc-source doc/html`
    *   HTML docs can now be found from [doc/html/index.html](doc/html/index.html)
3. Install coverage and mock
    * pip install coverage mock
4. Run unit tests for Icetea
    * coverage run unittest discover -s test
    * coverage run unittest discover -s icetea_lib/Plugin/plugins/plugin_tests
    * You should see many passed tests and perhaps some skipped tests,
    depending on your setup.
5. Test using a process device
    * Compile "dummyDut" by calling "make" in Icetea root folder.
    * Execute simple smoke test:
    ```
    icetea --tcdir examples --tc test_cmdline --type process --bin test/dut/dummyDut
    ```
    * Check that the test case passed from the console report.
6. Implement a cliapp with help from examples available in
[examples/cliapp](examples/cliapp).
7. Test using a real device.
    * Connect your K64F to your host
    * Execute the same test against your cliapp and device:
    ```
    icetea --tcdir examples --tc test_cmdline --type hardware --bin mbed-os-cliapp.bin
    ```
    * You should see similar results as in the previous test with the
    dummy process dut.

