# Test Case API for Icetea

Each test case contains two mandatory sections:
* test meta-information
* case() function

Test meta-information defines all test related information,
such as requirements and default values for the execution phase.
Some of the information can be overwritten with
`Icetea` command line parameters, or by the test suite.

Each test case can also contain a setUp function and a tearDown function
(rampUp and rampDown in older test cases).
If either setUp fails due to errors such as invalid commands
(TestStepFail exception), the case function is skipped
and tearDown is called.
If setUp fails due to TestStepError exceptions
or other fatal errors, both case and
tearDown are skipped and the test bench is torn down.


A Test Case base should look like:

```python
from icetea_lib.bench import Bench

class Testcase(Bench):
    def __init__(self,
        name=<test-case-name>,
        title=<test-case-title>,
        status=<implementation-status>,
        type=<test-type>,
        sub_type=<test-sub-type>,
        purpose=<test purpose>,
        specification_href=<link>,
        component=[<list of components under test>],
        feature=[<list of features under test>],
        compatible={ <compatible information> },
        requirements={ <test requirements > }
     )

    def setup(self): pass       # optional testcase setUp -phase
    def case(self): pass        # actual test logic
    def teardown(self): pass    # optional testcase tearDown -phase


```

# Test case example

## Test case configuration/meta-information

The purpose of test-specific meta-information is to explain
what a test case should do and what is required.

| Name | Description | Example |
|---| --- | --- |
| name | Short name for testcase, have to be unique | "sample" |
| title | Short title | "smoke sample test" |
| status | Implementation status, valid values are described below | "released" |
| type | Test case type, valid values described below | "acceptance" |
| sub_type | Type specific sub-type: Allowed values described below | "certification" |
| purpose | Purpose of test case | "Demostrate FW TC API" |
| specification_href | Link to specification | "http://....." |
| component | Component under test | "Icetea" |
| feature | List of features under test | [] |
| compatible| Compatibility related configurations. Can normally be omitted. Examples below | {} |
| execution | This section can exist if case should be skipped on every run. Add "only_type" or "platforms" key to skip testcases for certain type/platforms of duts only, | {"skip": {"value":  False, "only_type": "process", "platforms": ["K64F", "SAM4E"], "reason": "This is just dummy sample"}} |
| requirements | Test case requirements. Examples below | {} |

### Status
The status field in the configuration/meta-information
describes the implementation status of the test case.
Allowed values are:

* "released", TC is verified and ready for execution
* "development", TC is in development and not yet ready for testing
* "maintenance", TC is ready, but for some reason
(e.g. DUT interface changes) it cannot be executed for now
* "broken", For some reason this TC is not working correctly
for reasons not related to the DUT. E.g. some major framework changes.
* "unknown", Unknown status


### Type
The Type field describes the type of the test case. Allowed values are:

* "installation"
* "compatibility", verify compatibility,
e.g. two different versions of DUTs
* "smoke", verify very basic situations
* "regression"
* "acceptance"
* "functional"
* "stability"
* "destructive"
* "performance"
* "reliability"
* "stress"
* "recovery"

### Sub_type
The sub_type field is used to describe the subtype of a test case.
They are type-specific. Allowed values are:

* for type: "acceptance": subtype: "certification"

### Compatible
The compatible field describes configurations related to
compatibility with hardware, and automation as a dictionary.
This can normally be omitted.

| Name  | Description | Values |
|---|---|---|
| "automation" | by default all cases are automation compatible | { "reason" : "Reason why this is not automation compatible" } |
| "hw" | More information on this later | {"value": True} |
| "framework" | Name and version of framework this testcase is for | {"name": "Icetea", "version": "1.0.0"} |

### Requirements
The requirements field is a dictionary
where test case requirements can be specified.
It can contain dictionaries under the following keys:

1. "duts"
    * "*", dictionary, contains default requirements for all nodes
        * "count", number of duts required
        * "type", type of duts,
        allowed values: hardware(default, same as mbed), process, serial, mbed
        * "serial_port": defines the serial port this dut is connected to, as a string, when using serial type dut.
        * "allowed_platforms", list of platforms allowed
        for this test case. If no other platform is specified
        with platform_name, first item in this list will be used.
        * "platform_name", String name of platform
        you wish to use for duts. Can also be set for individual duts
        (see below). Must be found in allowed_platforms is
        allowed_platforms is defined and non-empty.
        * "pre-cmds", list of commands that should be
        executed before test case setup() is called.
        * "post-cmds", list of commands that should be
        executed after test case teardown() has been completed.
        * "application", dictionary of application details
            * "name", application name
            * "version", application version requirement.
            * "bin", required node -binary (url/absolute/relative).
            For process, the process will be launched from Bench.
            For hardware this file is to be flashed to the boards.
            If not defined either here or in command line
            and hardware duts are used, flashing will be skipped.
            * "cli_ready_trigger", string with prefix "regex:"
            or no prefix. If this is defined, Icetea will
            wait until a line matching this regex or string appears
            from the DUT before sending the cli init commands.
            See [Events.md](Events.md) for more details.
            * "cli_ready_trigger_timeout",
            timeout that is set for the cli init wait loop.
            * "init_cli_cmds", table of command line commands
            that are used to initialize nodes.
            If table is given as command, second parameter defines
            whether command is run asynchronous or not (True/False).
            * "post_cli_cmds", table of command line commands
            that are used prior to disconnecting from nodes.
            If table is given as command, second parameter defines
            whether command is run asynchronous or not (True/False).
            * "bin_args", a list of arguments that can be attached to
            process type duts. When process is launched,
            these arguments are added to the command.
        * "location", Location of nodes as x and y, in format 0.0,
        for example "location": [0.0, 10.0]
    * "1", specific configurations for node 1
        * "nick", nickname for DUT 1
        * Most default requirements can be overridden here.
        * NOTE if --bin cli argument is used,
        value specified here will not be overwritten!
        * Extra variables available in here: {n}  = duts total count,
        {i}  = dut index
    * "2...10", specify configurations for multiple duts like this.
        * Extra variables available here:
        {n}  = duts total count, {i}  = dut index,
        {pi} = math.pi, {xy} = x-axis: -> 0, y-axis -> 1
        * You can also set math inside location:
        "location": ["cos(%n/7*$n*2*$pi)*50", "sin($n/7*$n*2*$pi)*50"],
        "location": ["{n}", "{n}*{i}*{pi}"]}
2. "external", external applications which should be started
before TC setUp and will be killed at the end of the test
    * "apps", list of dictionaries.
        * Some applications have their own wrapper classes,
        which implement methods and properties for use in test cases.
        These can be run along with the test case
        by giving the name field.
            * These apps might have additional configuration parameters
            dependent on the environment.
            These have to be defined in env_cfg.json
            * {"name", "DeviceServer"}
        * Other applications require a configuration field as well,
        containing the application command and executable path.
            * {"name": "lighting", "config":
            {"cmd": "runLighting.bat", "path": "../../lighting/bin"}}

None of these are mandatory if you don't require duts or external applications from your test cases.

## Test case functions
A test case must contain at least an __init__ function
and case() function. In addition to these it can contain
a setup() and a teardown() function.

**init**
The init function should call Bench init function
with the test case configuration as parameters.
See code example below and configuration description
above for more details.

**setup**
All prerequisites for test case execution should be handled here.
This can include things like setting up dut configurations,
initializing network interfaces etc.

**case**
Test case functionality should be implemented here.

**teardown**
Cleanup can be performed here. This can include things
like deleting temporary files, powering down dut interfaces etc.

## Test case additional functions

**self.get_time()**
Return interval between current time and test case start.

**self.get_platforms()**
List of hardware platforms of the duts. 

**self.get_dut(index)**
Get a handle to a DUT with index, see section
[DUT public API](#dut-public-api) for functions that can
be accessed using DUT handle.

## Test case errors
A testcase can take advantage of the built-in error
types of the Bench class. These are TestStepFail,
TestStepError and InconclusiveError.
These errors can be imported for use
from icetea_lib.TestStepError module.

**TestStepFail**
A testcase that raises this Exception will automatically
be marked as failed. Testcase developers can raise this error
if the testcase should fail for whatever reason they deem necessary.

**TestStepError**
TestStepError exception is used in case where something very
fatal unexpected happens in test environment.

**InconclusiveError**
This error can be raised by the testcase if the testcase seems
to fail for reasons not related to the SUT, for example unstable
3rd party service causing a failure.

**SkippedTestcaseException**
This error can be raised in the test case setup or case functions to skip the test case for whatever reason.

## DUT public API

**open_connection()**
Open the communication channel to DUT (eg. serial port).
By default testcase automatically calls this during rampup.
Raises `DutConnectionError` if communication channel was already open.

**close_connection()**
Close the communication channel to DUT (eg. serial port).
By default testcase automatically calls this during rampdown.
This can be used during testcase to close the channel for example
to communicate with the DUT in another manner (eg. the serial port).

**comport**
If DUT has serial communication channel,
this returns the serial port name or path
(eg. COM0 or /dev/ttyACM0).
Please note only local device has this comport usage.

**store_traces**
This property (boolean) controls storing received lines for a dut. If this is set to True (default), all lines the dut receives are stored in memory in an internal list called traces.
If set to False, no lines will be stored. This also affects lines related to CliResponse objects, so command response objects will not have lines stored in them either.

## Command and response public API
The testcase superclass Bench contains
a command api that can be used to send commands to the DUT.
This command returns a CliResponse object,
which contains an api to parse the response lines.

### command

The command function takes the following arguments
that have some default values:
k, cmd, wait=True, expected_retcode=0, timeout=50,
asynchronous=False, report_cmd_fail=True

**k**: Index where command is sent, '*' -send command for all duts.
Also nick can be used.

**cmd**: Command to be sent to DUT.

**wait**: For special cases when retcode is not wanted to wait.

**expected_retcode**: Expecting this retcode, default: 0,
can be None when it is ignored.

**timeout**: Command timeout in seconds.

**asynchronous**: Send command, but wait for response in parallel.
When sending next command previous response will be wait.
When using async mode, response is dummy

**report_cmd_fail**: If True (default),
exception is thrown on command execution error

### CliResponse

The command function returns an object of this class.
CliResponse contains the following public apis:

* success()
    * Indicates if the retcode of the command was 0.
* fail()
    * Indicates if the retcode of the command was non-zero.
* verify_trace(expected_traces, break_in_fail=True)
    * Searches for expected traces in the traces collected
    from the command that created this object.
    * expectedTraces can be a list of strings or a string.
    * Returns True or False
    * Can raise TypeError or LookupError
* verify_message(expected_response, break_in_fail=True)
    * Searches for expected messages in the lines collected
    from
    the command that created this object.
    * expectedResponse can be list or set of strings or a string.
    * Returns True or False
    * Can raise TypeError or LookupError
* verify_response_duration(expected=None, zero=0,
threshold_percent=0,
break_in_fail=True)
    * Verifies that response duration is in bounds
    * Returns tuple (duration, expected, error)
    * Raises TestStepFail if breakInFail=True and duration
    was not in bounds.
* verify_response_time(expected_below)
    * Verifies that response time was below expected threshold.
    * Returns nothing
    * Raises ValueError if response time was longer than expected.

## Asserts
Several assertions are available as plugins to the Bench class, or as
functions you can import and use in your test cases. These asserts
are implemented in [asserts.py](../icetea_lib/tools/asserts.py).
These asserts usually raise TestStepFail if the assertion fails
or an AttributeError if the asserted expression was not of correct type.

The following asserts are available:
* assertTraceDoesNotContain(response, message)
    * response must have callable attribute verifyTrace
    (see [CliResponse](#command-and-response-public-api).
    * Asserts that the trace message is not found
    in response using verifyTrace(message, False).
* assertTraceContains(response, message)
    * Like assertTraceDoesNotContain, but asserts
    instead that message is found in response.
* assertDutTraceDoesNotContain(k, message, bench)
    * bench must be an instance of the test bench object (self in tc:s)
    * Verifies that dut k has not received trace message.
* assertDutTraceContains(k, message, bench)
    * bench must be an instance of the test bench object (self in tc:s)
    * Verifies that dut k has received trace message.
* assertTrue(expr, message=None)
    * Asserts that expr is True. Message is added into
    exception message if provided.
* assertFalse(expr, message=None)
    * Asserts that expr is False. Message is added into
    exception message if provided.
* assertNone(expr, message=None)
    * Asserts that expr is None. Message is added into
    exception message if provided.
* assertNotNone(expr, message=None)
    * Asserts that expr is not None. Message is added into
    exception message if provided.
* assertEqual(a, b, message=None)
    * Asserts that a == b. Message is added into exception
    message if provided.
* assertNotEqual(a, b, message=None)
    * Asserts that a != b. Message is added into exception
    message if provided.
* assertJsonContains(jsonStr=None, key=None, message=None)
    * jsonStr must be json as string. Uses json.loads to
    convert json into dict.
    * Asserts that key exists in jsonStr.

## Test case configuration
Test case configuration is loaded in four steps.
Step 1 is the base configuration loaded from the test case
__init__ method arguments. The second and third steps are from
the possible suite configuration file, that has configuration
fields for both suite wide default configuration values
applied to all test cases and test case specific configurations.
The final step a possible json configuration file defined on the cli
as --tc_cfg. At each step the configurations are merged
into the existing set. Example of a tc_cfg file is shown below:

```
{
    "requirements": {
        "duts: {
            {"*": {
                "count": 5
                }
            }
        }
    }
}
```

## Environment configuration
The test case can work with some external dependencies,
applications and modules that are defined in the test case configuration.
The configuration for these external modules can be set in the same place, but
it can also be defined in a separate environment configuration file
that is defined on the cli --env_cfg argument. This file is a json
file and it's merged into the test bench __env variable that
defaults to the following dictionary:

```
{
    "sniffer": {
        "iface": "Sniffer"
    }
}
```

This merge is done at the start of the test case.


## Multiple cases sharing setup and teardown
Icetea contains a decorator called test_case which can be used
to implement multiple testcases that have
the same setup and teardown steps.
By using this decorator several testcases can be
implemented in the same file.
It works by replacing the case-function of a Testcase object
with the function that the decorator is added to.
Example use of this can be found in
[multiple_tests_cases.py](../examples/multiple_test_cases_by_file_example/multiple_tests_cases.py).
Take note that the base class cannot be named "Testcase".
It will cause errors in the execution.

## Full code example with comments
Full code example and template for a testcase is available in
[sample.py](../examples/sample.py)

# Test bench
The test bench is implemented by a group of modules in icetea_lib/TestBench.
All of the implementation has been split into separate modules related to their function.
The runner itself is a state machine that has been implemented in the RunnerSM module.
All available functions of the test bench are defined in the BenchApi module.

## Implementation
Implementation has been split into 10 modules. Each one implements a set of functionalities for the
test bench.
Many of these refer to several attributes of the other modules. For ease of use these are called
through the common BenchApi class that provides the test bench with the interface to use these
functions.

* ArgsHandler
    * Handling of cli arguments.
* BenchFunctions
    * Different kinds of functions that don't really fit anywhere else.
* Commands
    * Implements DUT command handling.
* Configurations
    * Different kinds of API:s for DUT and environment configurations.
* Logger
    * Logger
* Plugins
    * Handling for Plugins.
* Resources
    * Handling for Duts and other resources.
* Results
    * Handling for Results.
* Topology
    * Functions for handling network topology.
* NetworkSniffer
    * Functions for handling the network sniffer.
