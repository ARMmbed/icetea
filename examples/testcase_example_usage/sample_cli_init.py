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

from icetea_lib.bench import Bench
from icetea_lib.Events.EventMatcher import EventMatcher
from icetea_lib.Events.Generics import EventTypes


'''
Test case example for quick starting Icetea. Icetea is slow starting now, but it can be 
configured to start quickly.

Proper usage:
    "cli_ready_trigger":
        1. allowed value: string with prefix "regex:" or no prefix.
        2. Put into the Dut requirements under the "application" key.
    Icetea wait until a line matching this regex or string appears from the DUT before sending 
    the cli init commands.

Mechanism behind:
    EventMatcher: The EventMatcher is an Observer that observes for DUT_LINE_RECEIVED events and matches the received
                    line contents to regular expressions or string provided to it, setting a flag and/or calling a
                    callback function if a match is found.
    You can use EventMatcher in test case as well.

For more details, please read tc_api.md and Events.md.
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_cli_trigger",
                       title="cli_ready_trigger example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of cli_ready_trigger",
                       component=["Icetea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 1,  # devices number
                                    "type": "hardware",  # "hardware" (by default) or "process"
                                    "application": {
                                        "bin": "build_path/build_full_name",  # build binary path
                                        "cli_ready_trigger": "/>"
                                    }
                                }
                            }
                        }
                       )

    def case(self):
        self.logger.info("cli_ready_trigger will help Icetea wait until application is ready "
                         "for communication.")
       
        # following examples shows how to create triggers from received data
        EventMatcher(EventTypes.DUT_LINE_RECEIVED, # event id
                     "ping",                       # match string or regex (see documentation)
                     self.get_dut(1),              # dut which data want to follow
                     callback=self.ping_cb)        # callback which is called when regex matches
        # this will trig above callback
        self.command(1, "echo ping")

    def ping_cb(self, dut, line):
        self.logger.info("pong (because of received %s)", line)
