#######
Logging
#######
Icetea contains it's own logging facilities implemented using the python logging module.
By default Icetea produces the following loggers:

* IceteaManager
    * Primarily logs items related to test case search, suite generation etc etc.
    * By default logs at INFO level to console and DEBUG level to icetea.log file.
* Bench
    * Each test case has their own Bench logger. This is what is accessed by self.logger in test cases.
    * By default logs at INFO level to console and DEBUG level to bench.log file.
* ResourceProvider
    * The ResourceProvider has it's own logger, primarily logs items related to configuration parsing and resources.
    * By default logs at INFO level to console and DEBUG level to ResourceProvider.log file.

In addition to these loggers Icetea generates a logger for some of the internally used
modules, such as mbed-flasher and the allocators used. These are categorized as either external
loggers (mbed-flasher) or ResourceProvider loggers (allocators).

The logging facilities and helpers are defined in icetea_lib.LogManager module.

****************
External loggers
****************
You can create an external logger for use with your plugins or other libraries (or just to enable
some custom logging) with get_external_logger() function defined in icetea_lib.LogManager module.
These external loggers log to the console at WARN level by default and DEBUG level to their
specific log files. For further configuration see the Configuration section below.

*************
Configuration
*************
You have two options for configuring logging. The first is our command line interface arguments.
You can use the -v argument to bump internal loggers (IceteaManager, Bench and ResourceProvider)
to log into the console at DEBUG level. This also bumps the external loggers console logging from
WARN to INFO. To push the external loggers to the DEBUG level, use -vv instead.

The second option is to use a JSON configuration file. This file needs to contain a JSON object
that has the key "logging" in it's base level. Icetea will read a JSON object from the
"logging" key into a dictionary and use it's contents to configure most of it's loggers. An
example of the contents of this file (and available configuration values) is shown below.::

    {
        "logging": {
            "IceteaManager": {
                "format": "%(asctime)s | %(message)s",
                "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
                "level": "INFO",
                "truncate_logs": {"truncate": True, "max_len": 10000, "reveal_len": 50},
                "file": {
                    "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
                    "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
                    "level": "DEBUG",
                    "name": "icetea.log"
                }
            },
            "Bench": {
                "format": "%(asctime)s | %(message)s",
                "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
                "level": "INFO",
                "truncate_logs": {"truncate": True, "max_len": 10000, "reveal_len": 50},
                "file": {
                    "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
                    "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
                    "level": "DEBUG",
                    "name": "bench.log"
                }
            },
            "external": {
                "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
                "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
                "level": "WARN",
                "truncate_logs": {"truncate": True, "max_len": 10000, "reveal_len": 50},
                "file": {
                    "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
                    "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
                    "level": "DEBUG",
                    "name": "external.log"
                }
            },
            <any logger name>: {
                    "format": <any valid format string>,
                    "dateformat": <any valid date format string>
                    "level": <string with any valid logging level name>
                    "truncate_logs": {
                        "truncate": <boolean>,
                        "max_len": <int>,
                        "reveal_len":<int>
                    }
                    "file": {
                        "format": <any valid format string>,
                        "dateformat": <any valid date format string>
                        "level": <string with any valid logging level name>,
                        "name": <name for log file of this logger. Just the file name, no path.>
                    }
            }
        }
    }


