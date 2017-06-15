# CLI concept

The Command Line Interface (CLI) concept was originally developed to flexibly and efficiently control the Device Under Test (DUT) in manual use cases, and to use test scripts easily.

Our solution, the [Host Controlling Interface](#Host-API), behaves exactly the same way as any normal computer shell, such as Linux bash. It provides a flexible way, with low memory consumption, to control IoT devices. It is also easily approachable for the developers, because they are most probably familiar with some shell (for example, DOS or busybox).

Concept parts:

* [Test Framework](#test-framework)
* [Test Case](#test-case)
* [Test Application](#test-app)

## Test Framework

The Test Framework, [mbedtest](mbedtest.md), executes the tests and collects the results. It is written in python, but could be extended with any other programming language as well. Python was our choice because it is already used in many existing projects.

## Test Case

A test case is a single python file. It is a class that inherits the `Testcase` base class.
To learn more about test cases, read [Test API](tc_api.md).

## Host API

Host (DUT) API is the physical interface between the host and the Device Under Test (DUT). The [Command Line Interface](cli.md) is used for controlling the host.

## Test App

Any application based on the command line interface can be a test application.
A test application has some basic requirements based on the Test Framework:

* Each TX/RX line must be terminated by `<CR><LF>` characters (or at least `<LF>`).
* Necessary commands:
  * `echo off` (to stop echoing)
  * `echo on` (to start echoing)
  * `set --vt100 off` (stop using vt100 control characters)
  * `set --vt100 on` (use vt100 control characters)
  * `set --retcode false` (stop printing retcodes)
  * `set --retcode true` (print retcode after each commands)

The Test Framework assumes that a `communication block` is a single line.

For example, when the test automation needs to take control over CLI, it initializes the interface to act
more optimal for scriptable point of view, like disable echoing, terminal control characters and enable return code prints.

```
echo off
set --vt100 off
set --retcode true
```

After this, the device is not echoing any received characters or printing any `vt100` control characters
that are hidden anyway and not needed for the test scripts. It also activates the `retcode` prints, for example:

`retcode: 0`

The Test Framework recognizes the print and assumes that the command was executed correctly before sending
further commands.

When the test is completed, the Test Framework initializes the device side interface back for human:

```
echo on
set --vt100 on
set --retcode false
```

In brief, _mbedtest_ is made for executing tests directly in the Linux shell (Device Under Test).
