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

Icetea event matcher usage example.
For details, please check doc/Events.md

Object: EventMatcher
    constructor arguments:
        1. event_type: Event type to follow.

        2. match_data: Str match data to look for. Adding 'regex:' prefix will
        indicate that this is a regular expression.

        3. flag: Optional Event to be set when match.

        4. callback: Callback function, receives an EventMatch object as an argument.

        5. forget: Optionally possible to stay listening more matches (default: True).

Object: EventMatch
    attributes:
        1. ref: Reference to object that triggered the event. Usually a Dut object.

        2. event_data: Data received on the event.

        3. match: re.MatchObject.
"""

# pylint: disable=missing-docstring,no-member,unused-variable,attribute-defined-outside-init
from threading import Event

from icetea_lib.bench import Bench
from icetea_lib.TestStepError import TestStepError
from icetea_lib.Events.EventMatcher import EventMatcher
from icetea_lib.Events.Generics import EventTypes


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_event_matcher",
                       title="Icetea built-in event matcher example",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of Icetea event matcher",
                       component=["icetea"],
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 1,
                                   "type": "hardware",
                                   "application": {
                                       "bin": "build_path/build_full_name",
                                   }
                               },
                               "1": {
                                   "nick": "dut1"  # give dut a nick
                               }
                           }
                       }
                      )

    def setup(self):
        # Start an EventMatcher to follow line received events, looking for the echoed hello.
        self.matcher = EventMatcher(EventTypes.DUT_LINE_RECEIVED,
                                    "hello",
                                    callback=self.callback_function)

    def case(self):
        # send command "echo hello" to 1st dut by index
        # "hello" matcher calls callback_function when echo coming back
        self.command(1, "echo hello")

        # Alternative example: Wait data from DUT with 10s timeout
        # create event matcher which is trigged when "ping" is received from DUT
        event = Event()
        EventMatcher(EventTypes.DUT_LINE_RECEIVED,  # event id
                     "ping",                        # match string or regex (see documentation)
                     self.get_dut(1),               # dut which data want to follow
                     event)
        # simulate "ping" by sending echo command
        self.command(1, "echo ping")
        # waits until event is set - "ping" is received
        if not event.wait(10):
            # if wait timeouts raise Error
            raise TestStepError("ping did not arrive")
        self.logger.info("Pong!")

    def callback_function(self, match_obj):
        match = match_obj.match  # re.MatchObject
        event_source = match_obj.ref  # Dut object that generated this event
        # Dut object is defined in icetea_lib/DeviceConnectors/Dut.py
        self.logger.info("Oh hello!")
        self.logger.info("Event data: %s", match_obj.event_data)
