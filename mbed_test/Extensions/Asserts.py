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

from mbed_test.TestStepError import TestStepFail
import json

class Asserts():
    def __init__(self, bench):
        self.bench = bench
        self.executeCommand = self.command = self.bench.command
        self.logger = self.bench.logger

        # Extend bench functionality with these new commands
        setattr(bench, "assertTraceDoesNotContain", self.assertTraceDoesNotContain)
        setattr(bench, "assertTraceContains", self.assertTraceContains)
        setattr(bench, "assertDutTraceDoesNotContain", self.assertDutTraceDoesNotContain)
        setattr(bench, "assertDutTraceContains", self.assertDutTraceContains)
        setattr(bench, "assertTrue", self.assertTrue)
        setattr(bench, "assertFalse", self.assertFalse)
        setattr(bench, "assertNone", self.assertNone)
        setattr(bench, "assertNotNone", self.assertNotNone)
        setattr(bench, "assertEqual", self.assertEqual)
        setattr(bench, "assertNotEqual", self.assertNotEqual)
        setattr(bench, "assertJsonContains", self.assertJsonContains)


    def assertTraceDoesNotContain(self, response, message):
        if response.verifyTrace(message, False):
            raise TestStepFail('Assert: Message(s) "%s" in response' % message)

    def assertTraceContains(self, response, message):
        if not response.verifyTrace(message, False):
            raise TestStepFail('Assert: Message(s) "%s" not in response' % message)

    def assertDutTraceDoesNotContain(self, k, message):
        if self.bench.verifyTrace(k, message, False):
            raise TestStepFail('Assert: Message(s) "%s" in response' % message)

    def assertDutTraceContains(self, k, message):
        if not self.bench.verifyTrace(k, message, False):
            raise TestStepFail('Assert: Message(s) "%s" not in response' % message)

    def assertTrue(self, expr, message=None):
        if not expr:
            raise TestStepFail(message if message is not None else 'Assert: %r != True' % expr)

    def assertFalse(self, expr, message=None):
        if expr:
            raise TestStepFail(message if message is not None else 'Assert: %r != False' % expr)

    def assertNone(self, expr, message=None):
        if expr != None:
            raise TestStepFail(message if message is not None else "Assert: %s != None" % str(expr))

    def assertNotNone(self, expr, message=None):
        if expr == None:
            raise TestStepFail(message if message is not None else "Assert: %s == None" % str(expr))

    def assertEqual(self, a, b, message=None):
        if not a == b:
            raise TestStepFail(message if message is not None else "Assert: %s != %s" % (str(a), str(b)))

    def assertNotEqual(self, a, b, message=None):
        if not a != b:
            raise TestStepFail(message if message is not None else "Assert: %s == %s" % (str(a), str(b)))

    def assertJsonContains(self, jsonStr=None, key=None, message=None):
        if jsonStr is not None:
            try:
                data=json.loads(jsonStr)
                if key not in data:
                    raise TestStepFail(message if message is not None else "Assert: Key : %s is not in : %s" % (str(key), str(jsonStr)))
            except TypeError as e:
                raise TestStepFail(message if message is not None else "Unable to parse json "+str(e))
        else:
            raise TestStepFail(message if message is not None else "Json string is empty")
