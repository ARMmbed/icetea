"""
Copyright 2016 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import time
import logging
import logging.config
import json
import re
import coloredlogs

logpathdir = None
logtcdir = None
logtcname = None
loggers = {}
logfiles= []
repeatnum = 0
standalone_logging = True
verbose_on = True
silent_on = False
color_on = False

level_formats= dict(
    debug=dict(color='white'),
    info=dict(color='green'),
    verbose=dict(color='blue'),
    warning=dict(color='yellow'),
    error=dict(color='red'),
    critical=dict(color='red'))

field_styles = dict(
    asctime=dict(color='cyan'),
    hostname=dict(color='magenta'),
    levelname=dict(color='black'),
    programname=dict(color='white'),
    name=dict(color='blue'),
    threadName=dict(color='blue'),
    source=dict(color='blue'))

class BenchLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if not "extra" in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["source"] = self.extra["source"]
        return msg, kwargs

class BenchFormatterWithType():
    def __init__(self, color=False):
        if not color:
            self._formatter = logging.Formatter("%(asctime)s.%(msecs)03d | %(source)s %(type)s %(threadName)s: "
                                                "%(message)s", "%H:%M:%S")
        else:
            self._formatter = coloredlogs.ColoredFormatter(
                "%(asctime)s.%(msecs)03d | %(source)s %(type)s %(threadName)s: "
                                                "%(message)s", "%H:%M:%S", level_formats, field_styles)
    def format(self, record):
        if not hasattr(record, "type"):
            record.type = "   "
        return self._formatter.format(record)

def remove_handlers(logger):
    #ToDo: Issue related to placeholder logger objects appearing in some rare cases. Check below required as a workaround
    if hasattr(logger, "handlers"):
        for handler in logger.handlers[::-1]:
            try:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                logger.removeHandler(handler)
            except:
                import traceback
                traceback.print_exc()
                break

def get_base_dir():
    """ Return the directory where logs for this run will be stored  """
    return logpathdir

def get_testcase_log_dir():
    """ Return the directory where current testcase's logs will be stored """
    return logtcdir

def get_testcase_logfilename(logname, prependTcName=False):
    """ Return filename for a logfile, filename will contain the actual path + filename
    :param logname: Name of the log including the extension, should describe what it contains (eg. "device_serial_port.log")
    :param prependTcName: Boolean, if True, prepends the filename with the testcase name
    """
    logdir = get_testcase_log_dir()
    if prependTcName:
        global logtcname
        logname = logtcname + "_" + logname
    fname = os.path.join(logdir, logname)
    logfiles.append(fname)
    return fname

def get_base_logfilename(logname, prependTcName=False):
    """ Return filename for a logfile, filename will contain the actual path + filename
    :param logname: Name of the log including the extension, should describe what it contains (eg. "device_serial_port.log")
    :param prependTcName: Boolean, if True, prepends the filename with the testcase name
    """
    logdir = get_base_dir()
    fname = os.path.join(logdir, logname)
    logfiles.append(fname)
    return fname

def get_logger(name):
    """ Return a logger instance for given name """
    return logging.getLogger(name)

def get_file_logger(name, formatter=None):
    """
    Return a file logger that will log into a file located in the testcase log directory. Anything logged with a
    file logger won't be visible in the console or any other logger
    :param name, Name of the logger, eg. the module name
    """
    if name is None or name == "":
        raise ValueError("Can't make a logger without name")

    logger = logging.getLogger(name)
    remove_handlers(logger)
    logger.setLevel(logging.INFO)

    if formatter is None:
        formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", "%H:%M:%S")
    h = _get_filehandler_with_formatter(name, formatter)
    logger.addHandler(h)

    return logger

def get_bench_logger(name=None, short_name="  ", log_to_file=True):
    """ Return a logger instance for given name. The logger will be a child of the bench logger, so anything that is
    logged to it, will be also logged to bench logger. If a logger with the given name doesn't already exist, create it
    using the given parameters.
    :param name: Name of the logger
    :param short_name: A short name (preferably 3 characters) describing the logger
    :param log_to_file: Boolean, if True the logger will also log to a file "name.log"
    """
    global loggers
    global color_on
    global verbose_on
    global silent_on
    # Get the root bench logger if name is none or empty or bench
    if name is None or name == "" or name == "bench":
        return loggers["bench"]

    loggername = "bench." + name
    # Return existing logger if one exists
    if loggername in loggers:
        # Check if short_name matches the existing one, if not update it
        if isinstance(loggers[loggername], BenchLoggerAdapter):
            if "source" not in loggers[loggername].extra or loggers[loggername].extra["source"] != short_name:
                loggers[loggername].extra["source"] = short_name
        return loggers[loggername]

    logger = logging.getLogger(loggername)
    remove_handlers(logger)
    logger.setLevel(logging.DEBUG)

    # Filehandler for logger
    if log_to_file:
        h = _get_filehandler_with_formatter(name, BenchFormatterWithType())
        h.setLevel(logging.DEBUG)
        logger.addHandler(h)

    loggers[loggername] = BenchLoggerAdapter(logger, {"source": short_name})

    return loggers[loggername]

def get_dummy_logger():
    logger = logging.getLogger("dummy")
    logger.addHandler(logging.NullHandler())
    return logger

def get_logfiles():
    """ Return a list of logfiles with relative paths from the log root directory """
    return [f.replace(get_base_dir(), ".") for f in logfiles]

def set_level(name, level):
    """ Set level for given logger
    :param name: Name of logger to set the level for
    :param level: The new level, see possible levels from python logging library
    """
    if name is None or name == "" or name == "bench":
        logging.getLogger("bench").setLevel(level)
    loggername = "bench." + name
    logging.getLogger(loggername).setLevel(level)

def init_base_logging(dir="./log", verbose=False, silent=False, color=False, list=False):
    """ Initialize the mbedtest logging by creating a directory to store logs for this run and initialize the console
    logger for mbedtest itself
    :param dir: Directory where to store the resulting logs
    :return:
    """
    global logpathdir
    global standalone_logging

    logpathdir = os.path.join(dir, time.strftime("%Y-%m-%d_%H%M%S"))
    if not os.path.exists(logpathdir) and not list:
        os.makedirs(logpathdir)

    # Initialize the simple console logger for mbedtestManagement
    mbedtestlogger = logging.getLogger("mbedtest")
    mbedtestlogger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", "%H:%M:%S")
    if not color:
        sh.setFormatter(formatter)
    else:
        sh.setFormatter(coloredlogs.ColoredFormatter("%(asctime)s.%(msecs)03d %(message)s", "%H:%M:%S"))

    if not list:
        fh = logging.FileHandler(get_base_logfilename("mbedtest.log"))
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG)
        mbedtestlogger.addHandler(fh)
    if verbose:
        sh.setLevel(logging.DEBUG)
    elif silent:
        sh.setLevel(logging.WARN)
    else:
        sh.setLevel(logging.INFO)
    mbedtestlogger.addHandler(sh)

    standalone_logging = False

def init_testcase_logging(name, verbose=True, silent=False, color=False):
    """ Initialize testcase logging and default loggers. First removes any existing testcase loggers, creates a new
    directory for testcase logs under the root logging directory, initializes the default bench logger and removes any
    child loggers it may have.
    :param name: Name of the testcase
    """
    global logtcdir
    global logtcname
    global logpathdir
    global logfiles
    global loggers
    global standalone_logging
    global repeatnum
    global verbose_on
    global silent_on
    global color_on
    if name is None or not isinstance(name, str) or len(name) == 0:
        raise EnvironmentError("Invalid testcase name for logging configuration")

    if standalone_logging:
        init_base_logging()

    finish_testcase_logging()

    # Generate filename friendly base name for logs from testcase name
    logtcdir = re.sub('[^\w\-_\. ]', '_', name)
    logtcname = logtcdir
    tempname = os.path.join(logpathdir, logtcdir + "_0")

    #Check if tc folder already exists. If it exists, we look for a new folder by appending integers to the folder name
    while os.path.exists(tempname):
        tempname = os.path.join(logpathdir, logtcdir + "_{}".format(repeatnum))
        repeatnum = repeatnum + 1
    logtcdir = tempname
    repeatnum = 0

    if not os.path.exists(logtcdir):
        os.makedirs(logtcdir)

    # Get the bench logger and remove all existing handlers
    benchlogger = logging.getLogger("bench")
    remove_handlers(benchlogger)
    benchlogger.setLevel(logging.DEBUG)

    # Console handler for bench
    cbh = logging.StreamHandler()
    color_on = color
    cbh.formatter = BenchFormatterWithType(color)
    verbose_on = verbose
    silent_on = silent
    if verbose:
        cbh.setLevel(logging.DEBUG)
    elif silent:
        cbh.setLevel(logging.WARN)
    else:
        cbh.setLevel(logging.INFO)
    benchlogger.addHandler(cbh)
    # file handler for bench and all child loggers
    h = _get_filehandler_with_formatter("bench", BenchFormatterWithType())
    h.setLevel(logging.DEBUG)
    benchlogger.addHandler(h)
    loggers["bench"] = BenchLoggerAdapter(benchlogger, {"source": "TC"})

def finish_testcase_logging():
    """ Finalize testcase logging by removing loggers """
    del logfiles[:]
    if loggers:
        # From local list of loggers, retrieve one(first one)
        logr = loggers.values()[0].logger
        # Retrieve logging module manager from logger
        manager = logr.manager
        # Manager holds dict with hard references to all logger instances produced in this python session
        for name, logger in manager.loggerDict.items():
            # Only bench loggers are required to be non-persistent between testcases
            if 'bench' in name:
                # Remove handlers from logger
                remove_handlers(logger)
                # Delete logger instance
                del manager.loggerDict[name]
    #Clear local logger dictionary
    loggers.clear()


def _get_filehandler_with_formatter(logname, formatter=None):
    """ Return a logging FileHandler for given logname using a given logging formatter
    :param logname: Name of the file where logs will be stored, ".log" extension will be added
    :param formatter: An instance of logging.Formatter or None if the default should be used
    :return:
    """
    global logfiles
    fn = get_testcase_logfilename(logname + ".log")
    h = logging.FileHandler(fn)
    if formatter is not None:
        h.setFormatter(formatter)
    return h
