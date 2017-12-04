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

This module contains generic event mechanism classes.
"""

"""
Enum for event types
"""
class EventTypes:
    DUT_LINE_RECEIVED = 1

'''
Usage:
1. Inherit in the class you want to listen for events
2. Make sure Observer's initializer gets called!
3. Use .observe(event_name, callback_function) to register
   events that u want to observe. event_name is just a string-
   identifier for a certain event
'''
class Observer:
    """Observer
    """
    _observers = []

    def __init__(self):
        self._observed_events = {}
        self.reinit()

    def reinit(self):
        self.forget()
        self._observers.append(self)

    def observe(self, event, callback_fn):
        self._observed_events[event] = callback_fn

    def forget(self):
        self._observed_events = {}
        if self in self._observers:
            self._observers.remove(self)


'''
Usage:
1. Call from anywhere in your code
The apropriate observers will get notified once the event fires
'''
class Event:
    """Event emitter
    """
    def __init__(self, event, *callback_args):
        for observer in Observer._observers:
            if event in observer._observed_events:
                observer._observed_events[event](*callback_args)