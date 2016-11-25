# Command Line Application

The purpose of the Test application (="CliApp") is to
provide cli-commands against software under test (SUT) (e.g. Mesh Stack).

The application needs to behave like any other linux shell and a
[cli library](https://github.com/ARMmbed/mbed-client-cli), that provides shell
functionality, like register commands and handling Command Line Interface, is available.
Read more about [cli from here](cli.md).

Example device side cli application can be found here:

[/examples/cliapp](/examples/cliapp)

Building example application:
```
yotta target frdm-k64f-gcc
yotta build
```
After successful device flash-able binary should be located in:
```
./build/frdm-k64f-gcc/source/example-cliapp.bin
```