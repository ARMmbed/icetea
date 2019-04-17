"""
Copyright 2017 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

LogManager module contains all logging related methods,
classes and helpers used by Icetea.
"""

import datetime
import json
import logging
import logging.config
import os
import re

import jsonschema
import pytz
import six
import jsonmerge



COLORS = True
try:
    import coloredlogs
except ImportError:
    COLORS = False

# Heavy use of global statement in this module for good reasons. Disable global-statement warning.
# pylint: disable=global-statement
LOGGING_CONFIG = {
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
    "external": {
        "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
        "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
        "level": "WARN",
        "truncate_logs": {"truncate": True, "max_len": 10000, "reveal_len": 50},
        "file": {
            "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
            "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
            "level": "DEBUG"
        }
    }
}

DEFAULT_LOGGING_CONFIG = {
    "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
    "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
    "level": "INFO",
    "truncate_logs": {"truncate": True, "max_len": 10000, "reveal_len": 50},
    "file": {
        "format": "%(asctime)s | %(source)s %(type)s %(threadName)s: %(message)s",
        "dateformat": "%Y-%m-%dT%H:%M:%S.%FZ",
        "level": "DEBUG",
        "name": "bench.log"
    }
}

LOGPATHDIR = None  # Path to run log directory
LOGTCDIR = None
LOGTCNAME = None
LOGGERS = {}
LOGFILES = []
GLOBAL_LOGFILES = []
REPEATNUM = 0
STANDALONE_LOGGING = True
VERBOSE_LEVEL = 0
SILENT_ON = False
COLOR_ON = False
TRUNCATE_LOG = True


LEVEL_FORMATS = dict(
    debug=dict(color='white'),
    info=dict(color='green'),
    verbose=dict(color='blue'),
    warning=dict(color='yellow'),
    error=dict(color='red'),
    critical=dict(color='red'))

FIELD_STYLES = dict(
    asctime=dict(color='cyan'),
    hostname=dict(color='magenta'),
    levelname=dict(color='black'),
    programname=dict(color='white'),
    name=dict(color='blue'),
    threadName=dict(color='blue'),
    source=dict(color='blue'))


class BenchLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter to add field 'extra' to logger.
    """
    def process(self, msg, kwargs):
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["source"] = self.extra["source"]
        return msg, kwargs


class BenchFormatter(logging.Formatter):
    """
    Handle time zone conversion to UTC and append milliseconds on %F.
    """
    converter = datetime.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        date_and_time = self.converter(record.created, tz=pytz.utc)
        if "%F" in datefmt:
            msec = "%03d" % record.msecs
            datefmt = datefmt.replace("%F", msec)
        str_time = date_and_time.strftime(datefmt)
        return str_time


class BenchFormatterWithType(object):  # pylint: disable=too-few-public-methods
    """
    Bench logger formatter.
    """
    def __init__(self, color=False, loggername="Bench"):
        if not color:
            config = LOGGING_CONFIG.get(loggername, {})
            self._formatter = BenchFormatter(
                config.get("format", DEFAULT_LOGGING_CONFIG.get("format")),
                config.get("dateformat", DEFAULT_LOGGING_CONFIG.get("dateformat")))
        else:

            class ColoredBenchFormatter(coloredlogs.ColoredFormatter):
                """
                This is defined as an internal class here because coloredlogs is and optional
                dependency.
                """
                converter = datetime.datetime.fromtimestamp

                def formatTime(self, record, datefmt=None):
                    date_and_time = self.converter(record.created, tz=pytz.utc)
                    if "%F" in datefmt:
                        msec = "%03d" % record.msecs
                        datefmt = datefmt.replace("%F", msec)
                    str_time = date_and_time.strftime(datefmt)
                    return str_time

            self._formatter = ColoredBenchFormatter(
                LOGGING_CONFIG.get(loggername, {}).get(
                    "format", DEFAULT_LOGGING_CONFIG.get("format")),
                LOGGING_CONFIG.get(loggername, {}).get(
                    "dateformat", DEFAULT_LOGGING_CONFIG.get("dateformat")),
                LEVEL_FORMATS, FIELD_STYLES)

    def format(self, record):
        """
        Format record with formatter.

        :param record: Record to format
        :return: Formatted record
        """
        if not hasattr(record, "type"):
            record.type = "   "
        return self._formatter.format(record)


def remove_handlers(logger):
    # TODO: Issue related to placeholder logger objects appearing in some rare cases. Check below
    # required as a workaround
    """
    Remove handlers from logger.

    :param logger: Logger whose handlers to remove
    """
    if hasattr(logger, "handlers"):
        for handler in logger.handlers[::-1]:
            try:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                logger.removeHandler(handler)
            except:  # pylint: disable=bare-except
                import traceback
                traceback.print_exc()
                break


def get_base_dir():
    """
    Return the directory where logs for this run will be stored
    """
    return LOGPATHDIR


def get_testcase_log_dir():
    """
    Return the directory where current testcase's logs will be stored
    """
    return LOGTCDIR


def get_testcase_logfilename(logname, prepend_tc_name=False):
    """ Return filename for a logfile, filename will contain the actual path +
    filename

    :param logname: Name of the log including the extension, should describe
    what it contains (eg. "device_serial_port.log")
    :param prepend_tc_name: Boolean, if True, prepends the filename with the
    testcase name
    """
    logdir = get_testcase_log_dir()
    if prepend_tc_name:
        global LOGTCNAME
        logname = LOGTCNAME + "_" + logname
    fname = os.path.join(logdir, logname)
    LOGFILES.append(fname)
    return fname


def get_base_logfilename(logname):
    """ Return filename for a logfile, filename will contain the actual path +
    filename

    :param logname: Name of the log including the extension, should describe
    what it contains (eg. "device_serial_port.log")
    """
    logdir = get_base_dir()
    fname = os.path.join(logdir, logname)
    GLOBAL_LOGFILES.append(fname)
    return fname


def get_logger(name):
    """
    Return a logger instance for given name
    """
    return logging.getLogger(name)


def get_file_logger(name, formatter=None):
    """
    Return a file logger that will log into a file located in the testcase log
    directory. Anything logged with a file logger won't be visible in the
    console or any other logger.

    :param name: Name of the logger, eg. the module name
    :param formatter: Formatter to use
    """
    if name is None or name == "":
        raise ValueError("Can't make a logger without name")

    logger = logging.getLogger(name)
    remove_handlers(logger)
    logger.setLevel(logging.INFO)

    if formatter is None:
        config = LOGGING_CONFIG.get(name, {}).get("file", DEFAULT_LOGGING_CONFIG.get("file"))
        formatter = BenchFormatter(config.get("level", "DEBUG"), config.get("dateformat"))
    func = get_testcase_logfilename(name + ".log")
    handler = _get_filehandler_with_formatter(func, formatter)
    logger.addHandler(handler)
    return logger


def _check_existing_logger(loggername, short_name):
    """
    Check if logger with name loggername exists.

    :param loggername: Name of logger.
    :param short_name: Shortened name for the logger.
    :return: Logger or None
    """
    if loggername in LOGGERS:
        # Check if short_name matches the existing one, if not update it
        if isinstance(LOGGERS[loggername], BenchLoggerAdapter):
            if ("source" not in LOGGERS[loggername].extra or
                    LOGGERS[loggername].extra["source"] != short_name):
                LOGGERS[loggername].extra["source"] = short_name
        return LOGGERS[loggername]
    return None


def _add_filehandler(logger, logpath, formatter=None, name="Bench"):
    """
    Adds a FileHandler to logger.

    :param logger: Logger.
    :param logpath: Path to file.
    :param formatter: Formatter to be used
    :param name: Name for logger
    :return: Logger
    """
    formatter = formatter if formatter else BenchFormatterWithType(loggername=name)
    handler = _get_filehandler_with_formatter(logpath, formatter)
    config = LOGGING_CONFIG.get(name, {}).get("file", DEFAULT_LOGGING_CONFIG.get("file"))
    handler.setLevel(getattr(logging, config.get("level", "DEBUG")))
    logger.addHandler(handler)
    return logger


def _get_basic_logger(loggername, log_to_file, logpath):
    """
    Get a logger with our basic configuration done.

    :param loggername: Name of logger.
    :param log_to_file: Boolean, True if this logger should write a file.
    :return: Logger
    """
    logger = logging.getLogger(loggername)
    logger.propagate = False
    remove_handlers(logger)
    logger.setLevel(logging.DEBUG)
    logger_config = LOGGING_CONFIG.get(loggername, DEFAULT_LOGGING_CONFIG)
    if TRUNCATE_LOG or logger_config.get("truncate_logs").get("truncate"):
        cfilter = ContextFilter()
        trunc_logs = logger_config.get("truncate_logs")
        # pylint: disable=invalid-name
        cfilter.MAXIMUM_LENGTH = trunc_logs.get("max_len",
                                                DEFAULT_LOGGING_CONFIG.get(
                                                    "truncate_logs").get("max_len"))
        cfilter.REVEAL_LENGTH = trunc_logs.get("reveal_len",
                                               DEFAULT_LOGGING_CONFIG.get(
                                                   "truncate_logs").get("reveal_len"))
        logger.addFilter(cfilter)

    # Filehandler for logger
    if log_to_file:
        _add_filehandler(logger, logpath, name=loggername)

    return logger


def get_resourceprovider_logger(name=None, short_name=" ", log_to_file=True):
    """
    Get a logger for ResourceProvider and it's components, such as Allocators.

    :param name: Name for logger
    :param short_name: Shorthand name for the logger
    :param log_to_file: Boolean, True if logger should log to a file as well.
    :return: Logger
    """

    global LOGGERS
    loggername = name
    logger = _check_existing_logger(loggername, short_name)
    if logger is not None:
        return logger
    logger_config = LOGGING_CONFIG.get(name, DEFAULT_LOGGING_CONFIG)
    logger = _get_basic_logger(loggername, log_to_file, get_base_logfilename(loggername + ".log"))

    cbh = logging.StreamHandler()
    cbh.formatter = BenchFormatterWithType(COLOR_ON)
    if VERBOSE_LEVEL > 0 and not SILENT_ON:
        cbh.setLevel(logging.DEBUG)
    elif SILENT_ON:
        cbh.setLevel(logging.WARN)
    else:
        cbh.setLevel(getattr(logging, logger_config.get("level")))
    logger.addHandler(cbh)

    LOGGERS[loggername] = BenchLoggerAdapter(logger, {"source": short_name})

    return LOGGERS[loggername]


def get_external_logger(name=None, short_name=" ", log_to_file=True):
    """
    Get a logger for external modules, whose logging should usually be on a less verbose level.

    :param name: Name for logger
    :param short_name: Shorthand name for logger
    :param log_to_file: Boolean, True if logger should log to a file as well.
    :return: Logger
    """

    global LOGGERS
    loggername = name
    logger = _check_existing_logger(loggername, short_name)
    if logger is not None:
        return logger
    logging_config = LOGGING_CONFIG.get(name, LOGGING_CONFIG.get("external"))
    filename = logging_config.get("file", {}).get("name", loggername)
    if not filename.endswith(".log"):
        filename = str(filename) + ".log"
    logger = _get_basic_logger(loggername, log_to_file, get_base_logfilename(filename))
    cbh = logging.StreamHandler()
    cbh.formatter = BenchFormatterWithType(COLOR_ON)

    if VERBOSE_LEVEL == 1 and not SILENT_ON:
        cbh.setLevel(logging.INFO)
    elif VERBOSE_LEVEL >= 2 and not SILENT_ON:
        cbh.setLevel(logging.DEBUG)
    elif SILENT_ON:
        cbh.setLevel(logging.ERROR)
    else:
        cbh.setLevel(getattr(logging, logging_config.get("level")))
    logger.addHandler(cbh)

    LOGGERS[loggername] = BenchLoggerAdapter(logger, {"source": short_name})

    return LOGGERS[loggername]


def get_bench_logger(name=None, short_name="  ", log_to_file=True):
    """
    Return a logger instance for given name. The logger will be a child
    of the bench logger, so anything that is logged to it, will be also logged
    to bench logger. If a logger with the given name doesn't already exist,
    create it using the given parameters.

    :param name: Name of the logger
    :param short_name: A short name (preferably 3 characters) describing the logger
    :param log_to_file: Boolean, if True the logger will also log to a file "name.log"
    """
    global LOGGERS

    # Get the root bench logger if name is none or empty or bench
    if name is None or name == "" or name == "bench":
        return LOGGERS["bench"]

    loggername = "bench." + name

    logger = _check_existing_logger(loggername, short_name)
    if logger is not None:
        return logger
    logger = _get_basic_logger(loggername, log_to_file, get_testcase_logfilename(loggername +
                                                                                 ".log"))
    logger.propagate = True
    LOGGERS[loggername] = BenchLoggerAdapter(logger, {"source": short_name})

    return LOGGERS[loggername]


def get_dummy_logger():
    """
    Get dummy logger
    :return: logger with NullHandler
    """
    logger = logging.getLogger("dummy")
    logger.addHandler(logging.NullHandler())
    return logger


def get_logfiles():
    """Return a list of logfiles with relative paths from the log
    root directory"""
    logfiles = [f for f in LOGFILES]
    logfiles.extend(GLOBAL_LOGFILES)
    return logfiles


def set_level(name, level):
    """ Set level for given logger
    :param name: Name of logger to set the level for
    :param level: The new level, see possible levels from python logging library
    """
    if name is None or name == "" or name == "bench":
        logging.getLogger("bench").setLevel(level)
    loggername = "bench." + name
    logging.getLogger(loggername).setLevel(level)


# pylint: disable=too-many-arguments
def init_base_logging(directory="./log", verbose=0, silent=False, color=False, no_file=False,
                      truncate=True, config_location=None):
    """
    Initialize the Icetea logging by creating a directory to store logs
    for this run and initialize the console logger for Icetea itself.

    :param directory: Directory where to store the resulting logs
    :param verbose: Log level as integer
    :param silent: Log level warning
    :param no_file: Log to file
    :param color: Log coloring
    :param truncate: Log truncating
    :param config_location: Location of config file.
    :raises IOError if unable to read configuration file.
    :raises OSError if log path already exists.
    :raises ImportError if colored logging was requested but coloredlogs module is not installed.
    """
    global LOGPATHDIR
    global STANDALONE_LOGGING
    global TRUNCATE_LOG
    global COLOR_ON
    global SILENT_ON
    global VERBOSE_LEVEL

    if config_location:
        try:
            _read_config(config_location)
        except IOError as error:
            raise IOError("Unable to read from configuration file {}: {}".format(config_location,
                                                                                 error))
        except jsonschema.SchemaError as error:
            raise jsonschema.SchemaError("Logging configuration schema "
                                         "file malformed: {}".format(error))

    LOGPATHDIR = os.path.join(directory, datetime.datetime.now().strftime(
        "%Y-%m-%d_%H%M%S.%f").rstrip("0"))

    # Initialize the simple console logger for IceteaManager
    icetealogger = logging.getLogger("icetea")
    icetealogger.propagate = False
    icetealogger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    formatter = BenchFormatter(LOGGING_CONFIG.get("IceteaManager").get("format"),
                               LOGGING_CONFIG.get("IceteaManager").get("dateformat"))
    if not color:
        stream_handler.setFormatter(formatter)
    elif color and not COLORS:
        raise ImportError("Missing coloredlogs module. Please install with "
                          "pip to use colors in logging.")
    else:

        class ColoredBenchFormatter(coloredlogs.ColoredFormatter):
            """
            This is defined as an internal class here because coloredlogs is and optional
            dependency.
            """
            converter = datetime.datetime.fromtimestamp

            def formatTime(self, record, datefmt=None):
                date_and_time = self.converter(record.created, tz=pytz.utc)
                if "%F" in datefmt:
                    msec = "%03d" % record.msecs
                    datefmt = datefmt.replace("%F", msec)
                str_time = date_and_time.strftime(datefmt)
                return str_time

        COLOR_ON = color
        stream_handler.setFormatter(ColoredBenchFormatter(
            LOGGING_CONFIG.get("IceteaManager").get("format"),
            LOGGING_CONFIG.get("IceteaManager").get("dateformat"),
            LEVEL_FORMATS, FIELD_STYLES))

    SILENT_ON = silent
    VERBOSE_LEVEL = verbose
    if not no_file:
        try:
            os.makedirs(LOGPATHDIR)
        except OSError:
            raise OSError("Log path %s already exists." % LOGPATHDIR)
        filename = LOGGING_CONFIG.get("IceteaManager").get("file").get("name", "icetea.log")
        icetealogger = _add_filehandler(icetealogger, get_base_logfilename(filename),
                                        formatter, "IceteaManager")
    if verbose and not silent:
        stream_handler.setLevel(logging.DEBUG)
    elif silent:
        stream_handler.setLevel(logging.WARN)
    else:
        stream_handler.setLevel(getattr(logging, LOGGING_CONFIG.get("IceteaManager").get("level")))
    icetealogger.addHandler(stream_handler)
    TRUNCATE_LOG = truncate
    if TRUNCATE_LOG:
        icetealogger.addFilter(ContextFilter())
    STANDALONE_LOGGING = False


def init_testcase_logging(name, verbose=0, silent=False, color=False,
                          truncate=True):
    """ Initialize testcase logging and default loggers. First removes any
    existing testcase loggers, creates a new directory for testcase logs under
    the root logging directory, initializes the default bench logger and
    removes any child loggers it may have.
    :param name: Name of the testcase
    :param verbose: Log level debug
    :param silent: Log level warning
    :param color: Log coloring
    :param truncate: Log truncating
    """
    global LOGTCDIR
    global LOGTCNAME
    global LOGGERS
    global REPEATNUM
    global VERBOSE_LEVEL
    global SILENT_ON
    global TRUNCATE_LOG

    if name is None or not isinstance(name, str) or not name:
        raise EnvironmentError("{} is invalid testcase name for logging configuration".format(name))

    if STANDALONE_LOGGING:
        init_base_logging()

    finish_testcase_logging()

    # Generate filename friendly base name for logs from testcase name
    LOGTCDIR = re.sub(r'[^\w\-_\. ]', '_', name)
    LOGTCNAME = LOGTCDIR
    tempname = os.path.join(LOGPATHDIR, LOGTCDIR + "_0")

    # Check if tc folder already exists. If it exists, we look for a new folder
    # by appending integers to the folder name
    while os.path.exists(tempname):
        tempname = os.path.join(LOGPATHDIR, LOGTCDIR + "_{}".format(REPEATNUM))
        REPEATNUM = REPEATNUM + 1
    LOGTCDIR = tempname
    REPEATNUM = 0

    if not os.path.exists(LOGTCDIR):
        os.makedirs(LOGTCDIR)

    # Get the bench logger and remove all existing handlers
    benchlogger = logging.getLogger("bench")
    benchlogger.propagate = False
    remove_handlers(benchlogger)
    benchlogger.setLevel(logging.DEBUG)

    TRUNCATE_LOG = truncate
    if TRUNCATE_LOG:
        benchlogger.addFilter(ContextFilter())

    # Console handler for bench
    stream_handler = logging.StreamHandler()
    if color and not COLORS:
        raise ImportError("Missing module: coloredlogs. Please install"
                          "with pip to use colors in logging.")
    stream_handler.formatter = BenchFormatterWithType(color)
    VERBOSE_LEVEL = verbose
    SILENT_ON = silent
    if verbose and not silent:
        stream_handler.setLevel(logging.DEBUG)
    elif silent:
        stream_handler.setLevel(logging.WARN)
    else:
        configs = LOGGING_CONFIG.get("Bench", {})
        stream_handler.setLevel(getattr(logging,
                                        configs.get("level", DEFAULT_LOGGING_CONFIG.get("level"))))
    benchlogger.addHandler(stream_handler)
    # file handler for bench and all child loggers
    filename = LOGGING_CONFIG.get("Bench",
                                  DEFAULT_LOGGING_CONFIG).get("file").get("name", "bench.log")
    benchlogger = _add_filehandler(benchlogger, get_testcase_logfilename(filename), name="Bench")
    LOGGERS["bench"] = BenchLoggerAdapter(benchlogger, {"source": "TC"})


def finish_testcase_logging():
    """ Finalize testcase logging by removing loggers """
    del LOGFILES[:]
    if LOGGERS:
        # From local list of loggers, retrieve one(first one)
        vlst = list(LOGGERS.values())
        logr = vlst[0].logger
        # Retrieve logging module manager from logger
        manager = logr.manager
        # Manager holds dict with hard references to all logger instances
        # produced in this python session
        for name, logger in list(manager.loggerDict.items()):
            # Only bench loggers are required to be non-persistent between
            # testcases
            if 'bench' in name:
                # Remove handlers from logger
                remove_handlers(logger)
                # Delete logger instance
                del manager.loggerDict[name]

    # Clear local logger dictionary
    LOGGERS.clear()


def _get_filehandler_with_formatter(logname, formatter=None):
    """ Return a logging FileHandler for given logname using a given
    logging formatter
    :param logname: Name of the file where logs will be stored, ".log"
    extension will be added
    :param formatter: An instance of logging.Formatter or None if the default
    should be used
    :return:
    """
    handler = logging.FileHandler(logname)
    if formatter is not None:
        handler.setFormatter(formatter)
    return handler


class ContextFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """
    Filter for filtering logging messages and truncating them after MAXIMUM_LENGTH has been reached.
    """
    MAXIMUM_LENGTH = 10000
    REVEAL_LENGTH = 50

    def filter(self, record):
        """
        Filter record
        :param record: Record to filter
        :return:
        """

        def modify(value):
            """
            Modify logged record, truncating it to max length and logging remaining length
            :param value: Record to modify
            :return:
            """
            if isinstance(value, six.string_types):
                if len(value) < ContextFilter.MAXIMUM_LENGTH:
                    return value

                try:
                    return "{}...[{} more bytes]".format(
                        value[:ContextFilter.REVEAL_LENGTH],
                        len(value) - ContextFilter.REVEAL_LENGTH)
                except UnicodeError:
                    return "{}...[{} more bytes]".format(
                        repr(value[:ContextFilter.REVEAL_LENGTH]),
                        len(value) - ContextFilter.REVEAL_LENGTH)
            elif isinstance(value, six.binary_type):
                return "{}...[{} more bytes]".format(
                    repr(value[:ContextFilter.REVEAL_LENGTH]),
                    len(value) - ContextFilter.REVEAL_LENGTH)

            else:
                return value

        record.msg = traverse_json_obj(record.msg, callback=modify)
        return True


def traverse_json_obj(obj, path=None, callback=None):
    """
    Recursively loop through object and perform the function defined
    in callback for every element. Only JSON data types are supported.
    :param obj: object to traverse
    :param path: current path
    :param callback: callback executed on every element
    :return: potentially altered object
    """
    if path is None:
        path = []

    if isinstance(obj, dict):
        value = {k: traverse_json_obj(v, path + [k], callback)
                 for k, v in obj.items()}
    elif isinstance(obj, list):
        value = [traverse_json_obj(elem, path + [[]], callback)
                 for elem in obj]
    else:
        value = obj

    if callback is None:
        return value
    return callback(value)


def _read_config(config_location):
    """
    Read configuration for logging from a json file. Merges the read dictionary to LOGGING_CONFIG.

    :param config_location: Location of file.
    :return: nothing.
    """
    global LOGGING_CONFIG
    with open(config_location, "r") as config_loc:
        cfg_file = json.load(config_loc)
        if "logging" in cfg_file:
            log_dict = cfg_file.get("logging")
            with open(os.path.abspath(os.path.join(__file__,
                                                   os.path.pardir,
                                                   'logging_schema.json'))) as schema_file:
                logging_schema = json.load(schema_file)
                jsonschema.validate(log_dict, logging_schema)
                merged = jsonmerge.merge(LOGGING_CONFIG, log_dict)
                LOGGING_CONFIG = merged
