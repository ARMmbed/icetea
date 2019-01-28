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

import os
import time
import logging
import logging.config
import re
import six

COLORS = True
try:
    import coloredlogs
except ImportError:
    coloredlogs = None
    COLORS = False

# Heavy use of global statement in this module for good reasons. Disable global-statement warning.
# pylint: disable=global-statement

LOGPATHDIR = None  # Path to run log directory
LOGTCDIR = None
LOGTCNAME = None
LOGGERS = {}
LOGFILES = []
GLOBAL_LOGFILES = []
REPEATNUM = 0
STANDALONE_LOGGING = True
VERBOSE_ON = True
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
        if not "extra" in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["source"] = self.extra["source"]
        return msg, kwargs


class BenchFormatterWithType(object):  # pylint: disable=too-few-public-methods
    """
    Bench logger formatter.
    """
    def __init__(self, color=False):
        if not color:
            self._formatter = logging.Formatter(
                "%(asctime)s.%(msecs)03d | %(source)s %(type)s %(threadName)s: "
                "%(message)s", "%H:%M:%S")
        else:
            self._formatter = coloredlogs.ColoredFormatter(
                "%(asctime)s.%(msecs)03d | %(source)s %(type)s %(threadName)s: "
                "%(message)s", "%H:%M:%S", LEVEL_FORMATS, FIELD_STYLES)

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
    remove handlers from logger.

    :param logger: Logger whose handlers to remove
    :return:
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
    """
    Return filename for a logfile, filename will contain the actual path + filename.

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
    """ Return filename for a logfile, filename will contain the actual path + filename

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

    :param name, Name of the logger, eg. the module name
    """
    if name is None or name == "":
        raise ValueError("Can't make a logger without name")

    logger = logging.getLogger(name)
    logger.propagate = False
    remove_handlers(logger)
    logger.setLevel(logging.INFO)

    if formatter is None:
        formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", "%H:%M:%S")
    func = get_testcase_logfilename(name + ".log")
    handler = _get_filehandler_with_formatter(func, formatter)
    logger.addHandler(handler)

    return logger


def get_resourceprovider_logger(name=None, short_name=" ", log_to_file=True):
    """
    Get logger for ResourceProvider and related classes.

    :param name: Name of the logger
    :param short_name: Shorthand name
    :param log_to_file: If True enable logging to file.
    :return: logging.Logger
    """

    global LOGGERS
    loggername = name
    # Return existing logger if one exists
    if loggername in LOGGERS:
        # Check if short_name matches the existing one, if not update it
        if isinstance(LOGGERS[loggername], BenchLoggerAdapter):
            if ("source" not in LOGGERS[loggername].extra or
                    LOGGERS[loggername].extra["source"] != short_name):
                LOGGERS[loggername].extra["source"] = short_name
        return LOGGERS[loggername]

    logger = logging.getLogger(loggername)
    logger.propagate = False
    remove_handlers(logger)
    logger.setLevel(logging.DEBUG)
    if TRUNCATE_LOG:
        logger.addFilter(ContextFilter())

    # Filehandler for logger
    if log_to_file:
        func = get_base_logfilename(name + ".log")
        handler = _get_filehandler_with_formatter(func, BenchFormatterWithType())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    cbh = logging.StreamHandler()
    cbh.formatter = BenchFormatterWithType(COLOR_ON)
    if VERBOSE_ON:
        cbh.setLevel(logging.DEBUG)
    elif SILENT_ON:
        cbh.setLevel(logging.WARN)
    else:
        cbh.setLevel(logging.INFO)
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
    # Return existing logger if one exists
    if loggername in LOGGERS:
        # Check if short_name matches the existing one, if not update it
        if isinstance(LOGGERS[loggername], BenchLoggerAdapter):
            if ("source" not in LOGGERS[loggername].extra or
                    LOGGERS[loggername].extra["source"] != short_name):
                LOGGERS[loggername].extra["source"] = short_name
        return LOGGERS[loggername]

    logger = logging.getLogger(loggername)
    logger.propagate = True
    remove_handlers(logger)
    logger.setLevel(logging.DEBUG)
    if TRUNCATE_LOG:
        logger.addFilter(ContextFilter())

    # Filehandler for logger
    if log_to_file:
        func = get_testcase_logfilename(name + ".log")
        handler = _get_filehandler_with_formatter(func, BenchFormatterWithType())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    LOGGERS[loggername] = BenchLoggerAdapter(logger, {"source": short_name})

    return LOGGERS[loggername]


def get_dummy_logger():
    """
    Get dummy logger.

    :return: logger with NullHandler
    """
    logger = logging.getLogger("dummy")
    logger.propagate = False
    logger.addHandler(logging.NullHandler())
    return logger


def get_logfiles():
    """
    Return a list of logfiles with relative paths from the log
    root directory
    """
    logfiles = [f for f in LOGFILES]
    logfiles.extend(GLOBAL_LOGFILES)
    return logfiles


def set_level(name, level):
    """
    Set level for given logger.

    :param name: Name of logger to set the level for
    :param level: The new level, see possible levels from python logging library
    """
    if name is None or name == "" or name == "bench":
        logging.getLogger("bench").setLevel(level)
    loggername = "bench." + name
    logging.getLogger(loggername).setLevel(level)


# pylint: disable=too-many-arguments
def init_base_logging(directory="./log", verbose=False, silent=False, color=False, no_file=False,
                      truncate=True):
    """
    Initialize the Icetea logging by creating a directory to store logs
    for this run and initialize the console logger for Icetea itself.

    :param directory: Directory where to store the resulting logs
    :param verbose: Log level debug
    :param silent: Log level warning
    :param no_file: Log to file
    :param color: Log coloring
    :param truncate: Log truncating
    :return: Nothing
    """
    global LOGPATHDIR
    global STANDALONE_LOGGING
    global TRUNCATE_LOG
    global COLOR_ON
    global SILENT_ON
    global VERBOSE_ON

    LOGPATHDIR = os.path.join(directory, time.strftime("%Y-%m-%d_%H%M%S"))
    if not os.path.exists(LOGPATHDIR) and not no_file:
        os.makedirs(LOGPATHDIR)

    # Initialize the simple console logger for IceteaManager
    icetealogger = logging.getLogger("icetea")
    icetealogger.propagate = False
    icetealogger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", "%H:%M:%S")
    if not color:
        stream_handler.setFormatter(formatter)
    elif color and not COLORS:
        raise ImportError("Missing coloredlogs module. Please install with"
                          "pip to use colors in logging.")
    else:
        stream_handler.setFormatter(coloredlogs.ColoredFormatter(
            "%(asctime)s.%(msecs)03d %(message)s", "%H:%M:%S"))

    if color and COLORS:
        COLOR_ON = color
    SILENT_ON = silent
    VERBOSE_ON = verbose
    if not no_file:
        file_handler = logging.FileHandler(get_base_logfilename("icetea.log"))
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        icetealogger.addHandler(file_handler)
    if verbose:
        stream_handler.setLevel(logging.DEBUG)
    elif silent:
        stream_handler.setLevel(logging.WARN)
    else:
        stream_handler.setLevel(logging.INFO)
    icetealogger.addHandler(stream_handler)
    TRUNCATE_LOG = truncate
    if TRUNCATE_LOG:
        icetealogger.addFilter(ContextFilter())

    STANDALONE_LOGGING = False


def init_testcase_logging(name, verbose=True, silent=False, color=False,
                          truncate=True):
    """
    Initialize testcase logging and default loggers. First removes any
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
    global VERBOSE_ON
    global SILENT_ON
    global TRUNCATE_LOG

    if name is None or not isinstance(name, str) or not name:
        raise EnvironmentError("Invalid testcase name for logging configuration")

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
    VERBOSE_ON = verbose
    SILENT_ON = silent
    if verbose:
        stream_handler.setLevel(logging.DEBUG)
    elif silent:
        stream_handler.setLevel(logging.WARN)
    else:
        stream_handler.setLevel(logging.INFO)
    benchlogger.addHandler(stream_handler)
    # file handler for bench and all child loggers
    func = get_testcase_logfilename("bench.log")
    handler = _get_filehandler_with_formatter(func, BenchFormatterWithType())
    handler.setLevel(logging.DEBUG)
    benchlogger.addHandler(handler)
    LOGGERS["bench"] = BenchLoggerAdapter(benchlogger, {"source": "TC"})


def finish_testcase_logging():
    """
    Finalize testcase logging by removing loggers
    """
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
    """
    Return a logging FileHandler for given logname using a given
    logging formatter.

    :param logname: Name of the file where logs will be stored, ".log"
    extension will be added
    :param formatter: An instance of logging.Formatter or None if the default
    should be used
    :return: FileHandler
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
