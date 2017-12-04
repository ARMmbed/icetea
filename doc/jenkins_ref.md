# Jenkins Build and Log Reference

This doc explains reference of finding jobs build result from CI.

Please note, for each PR there is only one CI job each time, which has two parallel nodes:

    - linux: running tests on Linux

    - windows: running tests on Windows


## Github PR Status Lables

The lable listed here would help to understand and quickly found what's wrong in CI if failed.

1. **unittest in windows**
    - shows build result of unittest running on Windows

2. **unittest in linux**
    - build result of unittest running on Linux

3. **plugin tests in linux**
    - build result of tests for testing plugin module running on Linux

4. **plugin tests in windows**
    - build result of tests for testing plugin module on Windows

5. **pylint check**
    - build result of pylint check for IcedTea

6. **continuous-integration/jenkins/branch**
    - general build result
    - if one of listed 5 above result failed, this one would be failed
    - if all of listed 5 above result are success, but this one is failed, it means some of post build
    actions, like archiving files, publish HTML results, publish junit result, etc is/are failed.


## Check Logs

In `Build Artifacts`, it collects all the logs needed:

    * log_linux/    : all the html results for unittest and plugin tests run on Linux
    * log_windows/  : all the html results for unittest and plugin tests run on Windows



## HTML Reports

There are HTML reports for tests on each node, which you can find the button below job console output.

 * Windows Build HTML Results
 * Linux Build HTML Report
