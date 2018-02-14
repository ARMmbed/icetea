# Example cliapp for mbed OS 5

This application demonstrates how to create a very basic cliapp to use with Icetea.

## Using the application

### Pre-requisites:
* A functional [mbed CLI](https://github.com/ARMmbed/mbed-cli) compilation environment.
* An mbed OS 5 compatible development board.
* A serial terminal application. For example screen, putty or minicom.

### Building
1. Deploy the application: `mbed deploy`.
2. Build using mbed CLI. For example `mbed compile -t GCC_ARM -m K64F`.
3. Flash the created binary to your development board.
4. Attach a serial terminal to your board to use the CLI. (The default baudrate is 115200.)

## Notes on application configuration file `mbed_app.json`

The following macros are set to configure mbed-client-cli to use stdlib malloc and free:
* `"MEM_ALLOC=malloc"`
* `"MEM_FREE=free"`

To enable tracing, the mbed-trace library is included and enabled:
* `"target.features_add": ["COMMON_PAL"]`
* `"mbed-trace.enable": 1`
