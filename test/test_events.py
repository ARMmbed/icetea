# pylint: disable=missing-docstring,unused-variable

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

import unittest
from random import randint
from threading import Event as EventFlag
from time import sleep

import mock

from icetea_lib.Events.EventMatcher import EventMatcher
from icetea_lib.Events.Generics import EventTypes, Event, Observer
from icetea_lib.tools.tools import IS_PYTHON3


class MockLineProvider(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.counter = 0

    def readline(self, timeout):
        if self.counter == 2:
            self.counter = 0
            return "found"
        sleep(randint(0, timeout))
        self.counter += 1
        return "nothing"


class EventTestcase(unittest.TestCase):

    def test_resolve_match_data(self):
        test_object = mock.MagicMock()
        callback = mock.MagicMock()
        event_flag = EventFlag()
        event_matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "test", test_object,
                                     flag=event_flag, callback=callback)
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "test")
        callback.assert_called_once_with(test_object, "test")
        self.assertTrue(event_flag.isSet())
        event_flag.clear()
        callback.reset_mock()
        # Recreate matcher because it forgets itself once it has matched once.
        event_matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "regex:test*", test_object,
                                     flag=event_flag, callback=callback)
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "nothing")
        self.assertFalse(event_flag.isSet())
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "test1")
        callback.assert_called_once_with(test_object, "test1")
        self.assertTrue(event_flag.isSet())
        event_flag.clear()
        callback.reset_mock()
        event_matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "regex:test:[0-9]", test_object,
                                     flag=event_flag, callback=callback)
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "test")
        self.assertFalse(event_flag.isSet())
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "test:1")
        callback.assert_called_once_with(test_object, "test:1")
        self.assertTrue(event_flag.isSet())

    def test_resolve_data_no_caller(self):
        test_object = mock.MagicMock()
        callback = mock.MagicMock()
        event_flag = EventFlag()
        eventmatcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "test", caller=None,
                                    flag=event_flag, callback=callback)
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "test")
        callback.assert_called_once_with(test_object, "test")
        self.assertTrue(event_flag.isSet())

    def test_resolve_data_decodefail(self):
        test_object = mock.MagicMock()
        callback = mock.MagicMock()
        event_flag = EventFlag()
        if IS_PYTHON3:
            event_matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED,
                                         "\x00\x00\x00\x00\x00\x00\x01\xc8", test_object,
                                         flag=event_flag, callback=callback)
        else:
            event_matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED,
                                         repr("\x00\x00\x00\x00\x00\x00\x01\xc8"), test_object,
                                         flag=event_flag, callback=callback)
        event = Event(EventTypes.DUT_LINE_RECEIVED, test_object, "\x00\x00\x00\x00\x00\x00\x01\xc8")
        callback.assert_called_once_with(test_object, "\x00\x00\x00\x00\x00\x00\x01\xc8")
        self.assertTrue(event_flag.isSet())
        event_flag.clear()

    def test_observer(self):  # pylint: disable=no-self-use
        obs = Observer()
        callback = mock.MagicMock()
        obs.observe(EventTypes.DUT_LINE_RECEIVED, callback)
        callback.assert_not_called()
        event = Event(2, "data")
        callback.assert_not_called()
        event = Event(EventTypes.DUT_LINE_RECEIVED, "data")
        callback.assert_called_once_with("data")


if __name__ == '__main__':
    unittest.main()
