# pylint: disable=missing-docstring,expression-not-assigned

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
"""

import logging
import os
import unittest

from icetea_lib.LogManager import ContextFilter, traverse_json_obj
from icetea_lib.tools.tools import IS_PYTHON3


class ContextFilterTest(unittest.TestCase):

    # Helper function
    @staticmethod
    def create_log_record(msg):
        return logging.LogRecord(name="", level=logging.ERROR, pathname="",
                                 lineno=0, msg=msg, args=None, exc_info=None,
                                 func=None)

    def setUp(self):
        self.contextfilter = ContextFilter()

    def test_filter_base64(self):
        msg = "aaa="
        record = self.create_log_record(msg)
        self.contextfilter.filter(record)
        self.assertEqual(msg, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH)]
        msg = "".join(msg)
        record = self.create_log_record(msg)
        self.contextfilter.filter(record)
        expected = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[9950 more bytes]"
        self.assertEqual(expected, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH * 2)]
        msg = "".join(msg)
        record = self.create_log_record(msg)
        self.contextfilter.filter(record)
        expected = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[19950 more bytes]"
        self.assertEqual(expected, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH - 1)]
        msg = "".join(msg)
        record = self.create_log_record(msg)
        self.contextfilter.filter(record)
        self.assertEqual(msg, record.msg)

        msg = []
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH + 1)]
        msg = "".join(msg)
        record = self.create_log_record(msg)
        self.contextfilter.filter(record)
        expected = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[9951 more bytes]"
        self.assertEqual(expected, record.msg)

    def test_filter_human_readable(self):
        msg = [" "]
        [msg.append("a") for _ in range(ContextFilter.MAXIMUM_LENGTH)]
        msg = "".join(msg)
        record = self.create_log_record(msg)
        expected = " aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...[9951 more bytes]"
        self.contextfilter.filter(record)
        self.assertEqual(expected, record.msg)

    def test_filter_binary_data(self):
        msg = []
        [msg.append(os.urandom(1024)) for _ in range(ContextFilter.MAXIMUM_LENGTH +1)]
        msg = b"".join(msg)
        expected = "{}...[10240974 more bytes]".format(msg[:50])
        record = self.create_log_record(msg)
        self.contextfilter.filter(record)

        self.assertEqual(expected, record.msg)

        msg = []
        [msg.append(u'\ufffd') for _ in range(ContextFilter.MAXIMUM_LENGTH + 1)]
        msg = "".join(msg)
        if not IS_PYTHON3:
            expected = u"{}...[9951 more bytes]".format(repr(msg[:50]))
        else:
            expected = u"{}...[9951 more bytes]".format(msg[:50])

        record = self.create_log_record(msg)
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
