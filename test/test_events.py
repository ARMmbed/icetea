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
from time import sleep
import mock
from threading import Event as EventFlag

from icetea_lib.Events.EventMatcher import EventMatcher
from icetea_lib.Events.Generics import EventTypes, Event, Observer


class MockLineProvider(object):
    def __init__(self):
        self.counter = 0

    def readline(self, timeout):
        if self.counter == 2:
            self.counter = 0
            return "found"
        else:
            sleep(randint(0, timeout))
            self.counter += 1
            return "nothing"


class EventTestcase(unittest.TestCase):

    def test_resolve_match_data(self):
        o = mock.MagicMock()
        cb = mock.MagicMock()
        ef = EventFlag()
        em = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "test", o, flag=ef, callback=cb)
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "test")
        cb.assert_called_once_with(o, "test")
        self.assertTrue(ef.isSet())
        ef.clear()
        cb.reset_mock()
        # Recreate matcher because it forgets itself once it has matched once.
        em = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "regex:test*", o, flag=ef, callback=cb)
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "nothing")
        self.assertFalse(ef.isSet())
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "test1")
        cb.assert_called_once_with(o, "test1")
        self.assertTrue(ef.isSet())
        ef.clear()
        cb.reset_mock()
        em = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "regex:test:[0-9]", o, flag=ef, callback=cb)
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "test")
        self.assertFalse(ef.isSet())
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "test:1")
        cb.assert_called_once_with(o, "test:1")
        self.assertTrue(ef.isSet())

    def test_resolve_match_data_no_caller(self):
        o = mock.MagicMock()
        cb = mock.MagicMock()
        ef = EventFlag()
        em = EventMatcher(EventTypes.DUT_LINE_RECEIVED, "test", caller=None, flag=ef, callback=cb)
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "test")
        cb.assert_called_once_with(o, "test")
        self.assertTrue(ef.isSet())

    def test_resolve_match_data_decodefail(self):
        o = mock.MagicMock()
        cb = mock.MagicMock()
        ef = EventFlag()
        em = EventMatcher(EventTypes.DUT_LINE_RECEIVED, repr("\x00\x00\x00\x00\x00\x00\x01\xc8"),
                          o, flag=ef, callback=cb)
        ev = Event(EventTypes.DUT_LINE_RECEIVED, o, "\x00\x00\x00\x00\x00\x00\x01\xc8")
        cb.assert_called_once_with(o, "\x00\x00\x00\x00\x00\x00\x01\xc8")
        self.assertTrue(ef.isSet())
        ef.clear()


    def test_observer(self):
        obs = Observer()
        cb = mock.MagicMock()
        obs.observe(EventTypes.DUT_LINE_RECEIVED, cb)
        cb.assert_not_called()
        e = Event(2, "data")
        cb.assert_not_called()
        e = Event(EventTypes.DUT_LINE_RECEIVED, "data")
        cb.assert_called_once_with("data")




if __name__ == '__main__':
    unittest.main()
