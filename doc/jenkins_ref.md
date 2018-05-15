# Jenkins Build and Log Reference

This doc explains reference of finding jobs build result from CI.

Please note, for each PR there is only one CI job each time, which has multiple parallel nodes and tasks:

number | CI-slave-node-name | github-status-label | task | function | env config
--- | --- | --- | --- | --- | ---
1 | linux | unittest in linux | run python 2 unittest in linux | `baseBuild("linux")` | N/A
2 | windows | unittest in windows | run python 2 unittest in windows  | `baseBuild("windows")` | N/A
3 | linux | plugin tests in linux | run python 2 plugin tests in linux | `baseBuild("linux")` | N/A
4 | windows | plugin tests in windows | run python 2 plugin tests in windows | `baseBuild("windows")` | N/A
5 | oul_ext_lin_nuc | e2e-local-hw-tests in linux | run e2e local hardware tests in linux | `runLinuxHwTests()` | python 2 virtualenv
6 | oul_ext_win_flasher_nuc | e2e-local-hw-tests in windows | run e2e local hardware tests in windows | `runWinHwTests()` | python 2 virtualenv
7 | arm-none-eabi-gcc | build app | build example mbed_cliapp with mbed-os5 | `buildExampleApp()` | N/A
8 | linux | pylint check | run python 2 pylint check | `pylint_linux_check()` | N/A
9 | N/A | continuous-integration/jenkins/pr-head | CI job result in general | N/A

**Note: continuous-integration/jenkins/branch**

- general build result
- if one of listed above tasks result failed, this one would be failed
- if all of listed above taks result are success, but this one is failed, it means some of post build
actions, like archiving files, publish HTML results, publish junit result, etc is/are failed.


## Key Functions

1. `baseBuild(String platform)`
    - platform value: `windows` or `linux`: means run task on OS linux or windows
    - This function: run unittest, run plugin tests, create coverage report, publish HTML report
2. `buildExampleApp()`: build example cliapp
3. `pylint_linux_check()`: check global installed python version and run pylint check
4. `runWinHwTests()`: run e2e local hardware tests on windows python 2 virtualenv
5. `runLinuxHwTests()`: run e2e local hardware tests on linux python 2 virtualenv
    - **Note:** becuase of the CI slave is shared
with other jobs, ykush power switch might be turned off, so at here, turn on ykush first, and sleep 1 second to wait power
switch on
6. `setBuildStatus()`: function for set github status label and build result


## Check Logs

In `Build Artifacts`, it collects all the logs needed:

    * example_app   : save example binary and build log
    * log_linux/    : all the html results for unittest and plugin tests run on Linux
    * log_windows/  : all the html results for unittest and plugin tests run on Windows
    * pylint.log    : check result of python 2 code style on linux


## HTML Reports

There are HTML reports for tests on each node, which you can find the button below job console output.

 * Windows Build HTML Results
 * Linux Build HTML Report
