# Test Case API for mbed test

Each test case contains two mandatory sections:
* test meta-information
* case() function

Test meta-information defines all test related information, such as requirements and default values for the execution phase.
Some of the information can be overwritten with `mbedtest` command line parameters, or by the test suite.

Each test case can also contain a setUp function and a tearDown function (rampUp and rampDown in older test cases). 
If either setUp fails due to errors such as invalid commands (TestStepFail exception), the case function is skipped and tearDown is called.
If setUp fails due to TestStepError exceptions or other fatal errors, both case and tearDown are skipped and the test bench is torn down. 


A Test Case base should look like this:

```python
from mbed_test.bench import Bench

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
        feature==[<list of features under test>],
        compatible={ <compatible information> },
        requirements={ <test requirements > }
     ):

    def setUp(self): pass       # optional testcase setUp -phase
    def case(self): pass        # actual test logic
    def tearDown(self): pass    # optional testcase tearDown -phase


```


# Test case example

## Test case configuration/meta-information

The purpose of test-specific meta-information is to explain what a test case should do and what is required. It also helps
to decide whether a test can be executed automatically.

| Name | Description | Required | Example |
|--- | --- | --- | --- |
| name | Short name for testcase, have to be unique | Yes, required for mbedtest to find the testcase | "sample" |
| title | Short title | No | "smoke sample test" |
| status | Implementation status, valid values are described below | No | "released" |
| type | Test case type, valid values described below | No | "acceptance" |
| sub_type | Type specific sub-type: Allowed values described below | No | "certification" |
| purpose | Purpose of test case | No | "Demostrate FW TC API" |
| specification_href | Link to specification | No | "http://....." |
| component | Component under test | No | "mbed-test" |
| feature | List of features under test | No | [] |
| compatible| Compatibility related configurations. Can normally be omitted. Examples below | No | {} |
| execution | This section can exist if case should be skipped on every run.  | No | {"skip": {"value":  False, "reason": "This is just dummy sample"}} |
| requirements | Test case requirements. Examples below | Yes, but can be left empty | {} |

Most of the fields in the metadata are not actually required, but some of them might be important information for a developer or tester working with you testcase.

### Status
The status field in the configuration/meta-information describes the implementation status of the test case. Allowed values are:

* "released", TC is verified and ready for execution
* "development", TC is in development and not yet ready for testing
* "maintenance", TC is ready, but for some reason (e.g. DUT interface changes) it cannot be executed for now
* "broken", For some reason this TC is not working correctly for reasons not related to the DUT. E.g. some major framework changes.
* "unknown", Unknown status

### Type
The Type field describes the type of the test case. Allowed values are:

* "installation"
* "compatibility", verify compatibility, e.g. two different versions of DUTs
* "smoke", verify very basic situations
* "regression"
* "acceptance"
* "functional"
* "stability"
* "destructive"
* "performance"
* "reliability"
* "functional"

### Sub_type
The sub_type field is used to describe the subtype of a test case. They are type-specific. Allowed values are:

* for type: "acceptance": subtype: "certification"

### Compatible
The compatible field describes configurations related to compatibility with hardware and automation as a dictionary. This can normally be omitted.

| Name  | Description | Values |
|---|---|---|
| "automation" | by default all cases are automation compatible | { "reason" : "Reason why this is not automation compatible" } |
| "hw" | More information on this later | {"value": True} |
| "framework" | Name and version of framework this testcase is for | {"name": "mbed-test", "version": "1.0.0"} |

### Requirements
The requirements field is a dictionary where test case requirements can be specified.
It contains several dictionaries under the following keys:

1. "duts"
    * "*", dictionary, contains default requirements for all nodes
        * "count", number of duts required
        * "type", type of duts, allowed values: hardware(default), process, simulate
        * "allowed_platforms", list of platforms allowed for this test case. If this list exists, will skip allocating devices not in the list.
        * "pre-cmds", list of commands that should be executed before setUp() is called.
        * "application", dictionary of application details
            * "name", application name
            * "version", application version requirement.
            * "bin", required node -binary (url/absolute/relative). For process this process will be launched from Bench. For hardware this file is to be flashed to the boards.
            * "init_cli_cmds", table of command line commands that are used to initialize nodes. If table is gicen as command, second parameter defines whether command is run asynchronous or not (True/False).
       * "rf_channel", default rf-channel to be used. Can be overwritten with command line parameters
       * "location", Location of nodes as x and y, in format 0.0, for example "location": [0.0, 10.0]
    * "1", specific configurations for node 1
        * "nick", nickname for DUT 1
        * all default requirements can be overridden here.
        * Extra variables available in here: {n}  = duts total count, {i}  = dut index
    * "2...10", specify configurations for multiple duts like this.
        * Extra variables available here: {n}  = duts total count, {i}  = dut index, {pi} = math.pi, {xy} = x-axis: -> 0, y-axis -> 1
        * You can also set math inside location: "location": ["cos(%n/7*$n*2*$pi)*50", "sin($n/7*$n*2*$pi)*50"], "location": ["{n}", "{n}*{i}*{pi}"]}
2. "external", external applications which should be started before TC setUp and will be killed at the end of the test
    * "apps", list of dictionaries.
        * Some applications have their own wrapper classes, which implement methods and properties for use in test cases. These can be run along with the test case by giving the name field.
            * These apps might have additional configuration parameters dependent on the environment. These have to be defined in env_cfg.json
            * {"name", "DeviceServer"}
        * Other applications require a configuration field as well, containing the application command and executable path.
            * {"name": "lighting", "config": {"cmd": "runLighting.bat", "path": "../../lighting/bin"}}

## Test case functions
A test case must contain at least an __init__ function and case() function. In addition to these it can contain a setUp() and a tearDown() function.

**init**
The init function should call Bench init function with the test case configuration as parameters. See code example below and configuration description above for more details.

**setUp**
All prerequisites for test case execution should be handled here. This can include things like setting up dut configurations, initializing network interfaces etc.

**case**
Test case functionality should be implemented here.

**tearDown**
Cleanup can be performed here. This can include things like deleting temporary files, powering down dut interfaces etc.

## Full code example with comments
Full code example and template for a testcase is available in [template_tc.py](../examples/template_tc.py)