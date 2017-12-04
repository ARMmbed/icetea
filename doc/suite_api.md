# Suite API for IcedTea
IcedTea supports suites in json formatted files.
These files should contain only the json document
and should end in .json.

## Suite file format
A suite file can contain one json object which contains
all the required keys for the suite. These keys are:

* "default":
    * Contains an object of configurations that should be applied
    to all testcases in this suite. See [tc_api.md](tc_api.md)
    for allowed configurations for testcases.
    * Special keys that modify the suite run instead of the testcases:
        * "iteration": how many times each testcase is run.
        Defaults to 1.
        * "retryCount": how many times each testcase can be retried.
        By default only works on testcases that resulted in
        inconclusive results.
        If a testcase was retried at least once
        and the last retry performed resulted in a passed result,
        the retried cases are not displayed in the Junit result file.
        * "retryReason": Can be "includeFailures" or "inconclusive".
        If set to includeFailures, behaviour of retryCount is modified
        so that failed testcases are also retried
        in addition to inconclusive ones.
* "testcases":
    * A list of objects each containing the following keys:
        * "name": name of testcase to be run
        * "config": Optional object that can contain configuration
        values specific for this testcase.
        If both this key and the "default" key contain the same keys,
        the values in this object will overwrite
        the ones defined in "default".

## Example suite file
An example suite file can be found in
[dummy_suite.json](./../examples/dummy_suite.json)