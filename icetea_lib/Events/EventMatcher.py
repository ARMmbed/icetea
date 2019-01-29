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

import re

from icetea_lib.Events.Generics import Observer
from icetea_lib.Events.EventMatch import EventMatch
from icetea_lib.tools.tools import IS_PYTHON3


class EventMatcher(Observer):
    """
    EventMatcher class. This is an Observer that listens to certain events and tries to match
    them to a preset match data.
    """
    def __init__(self, event_type, match_data, caller=None,  # pylint: disable=too-many-arguments
                 flag=None, callback=None, forget=True):
        Observer.__init__(self)
        self.caller = caller
        self.event_type = event_type
        self.flag_to_set = flag
        self.callback = callback
        self.match_data = match_data
        self.__forget = forget
        self.observe(event_type, self._event_received)

    def _event_received(self, ref, data):
        """
        Handle received event.

        :param ref: ref is the object that generated the event.
        :param data: event data.
        :return: Nothing.
        """
        match = self._resolve_match_data(ref, data)
        if match:
            if self.flag_to_set:
                self.flag_to_set.set()
            if self.callback:
                self.callback(EventMatch(ref, data, match))
            if self.__forget:
                self.forget()

    def _resolve_match_data(self, ref, event_data):
        """
        If match_data is prefixed with regex: compile it to a regular expression pattern.
        Match event data with match_data as either regex or string.

        :param ref: Reference to object that generated this event.
        :param event_data: Data from event, as string.
        :return: return re.MatchObject if match found, False if ref is not caller
        set for this Matcher or if no match was found.
        """
        if self.caller is None:
            pass
        elif ref is not self.caller:
            return False
        try:
            dat = event_data if IS_PYTHON3 else event_data.decode("utf-8")
            if self.match_data.startswith("regex:"):
                splt = self.match_data.split(":", 1)
                pttrn = re.compile(splt[1])
                match = re.search(pttrn, dat)
                return match if match is not None else False
            return event_data if self.match_data in dat else False
        except UnicodeDecodeError:
            dat = repr(event_data)
            return self._resolve_match_data(ref, dat)
