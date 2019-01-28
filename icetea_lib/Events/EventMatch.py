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

EventMatch object. Describes a single matched event for EventMatcher.
"""


class EventMatch(object):  # pylint: disable=too-few-public-methods
    """
    EventMatcher callback object
    """
    def __init__(self, ref, event_data, match):
        """
        :param ref: reference object
        :param event_data: original event data which matches
        :param match: re.MatchObject or string depend on EventMatcher configuration
        """
        self.ref = ref
        self.event_data = event_data
        self.match = match
