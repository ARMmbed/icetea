# pylint: disable=missing-docstring,expression-not-assigned,no-self-use,unused-variable,
# pylint: disable=unused-argument,protected-access

import logging

import os
import unittest
import mock

from jsonschema import ValidationError

import icetea_lib.LogManager as LogManager
from icetea_lib.LogManager import ContextFilter, traverse_json_obj, get_external_logger
from icetea_lib.tools.tools import IS_PYTHON3


class FunctionTests(unittest.TestCase):
    def setUp(self):
        pass

    @mock.patch("icetea_lib.LogManager.os.path.join")
    def test_verbosity_set_to_warn(self, mock_os):
        LogManager.VERBOSE_LEVEL = 0
        LogManager.SILENT_ON = False
        logger = get_external_logger("test_logger", "TST", False)
        logger = logging.getLogger("test_logger")
        self.assertTrue(logger.handlers[0].level == logging.WARNING)

    @mock.patch("icetea_lib.LogManager.os.path.join")
    def test_verbosity_set_to_info(self, mock_os):
        LogManager.VERBOSE_LEVEL = 1
        LogManager.SILENT_ON = False
        logger = get_external_logger("test_logger2", "TST", False)
        logger = logging.getLogger("test_logger2")
        self.assertTrue(logger.handlers[0].level == logging.INFO)

    @mock.patch("icetea_lib.LogManager.os.path.join")
    def test_verbosity_set_to_debug(self, mock_os):
        LogManager.VERBOSE_LEVEL = 2
        LogManager.SILENT_ON = False
        logger = get_external_logger("test_logger3", "TST", False)
        logger = logging.getLogger("test_logger3")
        self.assertTrue(logger.handlers[0].level == logging.DEBUG)

    @mock.patch("icetea_lib.LogManager.os.path.join")
    def test_verbosity_set_to_silent(self, mock_os):
        LogManager.VERBOSE_LEVEL = 2
        LogManager.SILENT_ON = True
        logger = get_external_logger("test_logger4", "TST", False)
        logger = logging.getLogger("test_logger4")
        self.assertTrue(logger.handlers[0].level == logging.ERROR)


class ConfigFileTests(unittest.TestCase):
    def setUp(self):
        self.original_config = LogManager.LOGGING_CONFIG

    def test_configs_read(self):
        filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                "does_not_exist.json"))
        with self.assertRaises(IOError):
            LogManager.init_base_logging(config_location=filepath)
        filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                "logging_config.json"))
        LogManager._read_config(filepath)

    def test_configs_merge(self):
        filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                "logging_config.json"))
        LogManager._read_config(filepath)
        self.assertDictEqual(LogManager.LOGGING_CONFIG.get("test_logger"), {"level": "ERROR"})

    def test_configs_schema_validation(self):
        filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                "erroneous_logging_config.json"))
        with self.assertRaises(ValidationError):
            LogManager._read_config(filepath)
        filepath = os.path.abspath(os.path.join(__file__, os.path.pardir, "tests",
                                                "logging_config.json"))
        LogManager._read_config(filepath)

    def tearDown(self):
        LogManager.LOGGING_CONFIG = self.original_config


class ContextFilterTest(unittest.TestCase):
    def setUp(self):
        self.contextfilter = ContextFilter()

    def test_filter_base64(self):
        msg = "aaa="
        record = create_log_record(msg)
        self.contextfilter.filter(record)
        self.assertEqual(msg, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH)]
        msg = "".join(msg)
        record = create_log_record(msg)
        self.contextfilter.filter(record)
        expected = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[9950 more bytes]"
        self.assertEqual(expected, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH * 2)]
        msg = "".join(msg)
        record = create_log_record(msg)
        self.contextfilter.filter(record)
        expected = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[19950 more bytes]"
        self.assertEqual(expected, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH - 1)]
        msg = "".join(msg)
        record = create_log_record(msg)
        self.contextfilter.filter(record)
        self.assertEqual(msg, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH + 1)]
        msg = "".join(msg)
        record = create_log_record(msg)
        self.contextfilter.filter(record)
        expected = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[9951 more bytes]"
        self.assertEqual(expected, record.msg)

    def test_filter_human_readable(self):
        msg = [" "]
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH)]
        msg = "".join(msg)
        record = create_log_record(msg)
        expected = " aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[9951 more bytes]"
        self.contextfilter.filter(record)
        self.assertEqual(expected, record.msg)

    def test_filter_binary_data(self):
        msg = []
        [msg.append(os.urandom(1024)) for _ in range(ContextFilter.MAXIMUM_LENGTH +1)]
        msg = b"".join(msg)
        expected = "{}...[10240974 more bytes]".format(msg[:50])
        record = create_log_record(msg)
        self.contextfilter.filter(record)

        self.assertEqual(expected, record.msg)

        msg = []
        [msg.append(u'\ufffd') for _ in range(ContextFilter.MAXIMUM_LENGTH + 1)]
        msg = "".join(msg)
        if not IS_PYTHON3:
            expected = u"{}...[9951 more bytes]".format(repr(msg[:50]))
        else:
            expected = u"{}...[9951 more bytes]".format(msg[:50])

        record = create_log_record(msg)
        self.contextfilter.filter(record)
        self.assertEqual(expected, record.msg)


class TraverseJsonObjTest(unittest.TestCase):
    def test_stays_untouched(self):
        test_dict = [{"a": "aa", "b": ["c", "d", {"e": "aa", "f": "aa"}]}]

        self.assertEqual(test_dict, traverse_json_obj(test_dict))

    def test_all_modified(self):
        test_dict = [{"a": "aa", "b": ["c", "d", {"e": "aa", "f": "aa"}]}]

        def modify(value):
            return "bb" if value == "aa" else value

        expected = [{"a": "bb", "b": ["c", "d", {"e": "bb", "f": "bb"}]}]
        self.assertEqual(expected, traverse_json_obj(test_dict, callback=modify))


class CustomFormatterTest(unittest.TestCase):

    def test_benchformatter_formats_timestamp(self):  # pylint: disable=invalid-name
        formatter = LogManager.BenchFormatter("%(asctime)s | %(source)s %(type)s %(threadName)s: "
                                              "%(message)s", "%Y-%m-%dT%H:%M:%S.%FZ")

        record = create_log_record("test_message")
        time_str = formatter.formatTime(record, "%Y-%m-%dT%H:%M:%S.%FZ")

        # Check that T exists, should be in between date and time.
        self.assertTrue(time_str.rfind("T") > 0)

        # Check that date format matches ISO-8601
        date = time_str[:time_str.rfind("T")]
        self.assertRegexpMatches(date, r"^([0-9]{4})(-?)(1[0-2]|0[1-9])\2(3[01]|0[1-9]|[12][0-9])$")

        # Chech that time format matches ISO-8601
        time_ending = time_str[time_str.rfind("T") + 1: time_str.rfind(".")]
        self.assertRegexpMatches(time_ending, r"^(2[0-3]|[01][0-9]):?([0-5][0-9]):?([0-5][0-9])$")

        # Check that time_str ends with Z to show it's UTC
        self.assertTrue(time_str.endswith("Z"))

        # Check that milliseconds exist
        millis = time_str[time_str.rfind(".") + 1: time_str.rfind("Z")]
        self.assertRegexpMatches(millis, r"([0-9][0-9][0-9])")


# Helper function
def create_log_record(msg):
    return logging.LogRecord(name="", level=logging.ERROR, pathname="",
                             lineno=0, msg=msg, args=None, exc_info=None,
                             func=None)
