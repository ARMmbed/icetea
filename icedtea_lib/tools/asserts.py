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

from icedtea_lib.TestStepError import TestStepFail
import inspect
import os
import json

def format_message(msg):
    """
    Formatting function for assert messages. Fetches the filename, function and line number of the code causing the fail
    and formats it into a three-line error message. Stack inspection is used to get the information.
    Originally done by BLE-team for their testcases.
    :param msg: Message to be printed along with the information.
    :return: Formatted message as string.
    """
    callerframerecord = inspect.stack()[2]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    _, filename = os.path.split(info.filename)
    caller_site = "In file {!s}, in function {!s}, at line {:d}".format(filename, info.function, info.lineno)
    return "{!s}\n{!s}\n{!s}".format(msg, caller_site, info.code_context)


def assertTraceDoesNotContain(response, message):
    if not hasattr(response, "verify_trace"):
        raise AttributeError("Response object does not contain verify_trace method!")
    if response.verify_trace(message, False):
        raise TestStepFail('Assert: Message(s) "%s" in response' % message)


def assertTraceContains(response, message):
    if not hasattr(response, "verify_trace"):
        raise AttributeError("Response object does not contain verify_trace method!")
    if not response.verify_trace(message, False):
        raise TestStepFail('Assert: Message(s) "%s" not in response' % message)


def assertDutTraceDoesNotContain(k, message, bench):
    if not hasattr(bench, "verify_trace"):
        raise AttributeError("Bench object does not contain verify_trace method!")
    if bench.verify_trace(k, message, False):
        raise TestStepFail('Assert: Message(s) "%s" in response' % message)


def assertDutTraceContains(k, message, bench):
    if not hasattr(bench, "verify_trace"):
        raise AttributeError("Bench object does not contain verify_trace method!")
    if not bench.verify_trace(k, message, False):
        raise TestStepFail('Assert: Message(s) "%s" not in response' % message)


def assertTrue(expr, message=None):
    if not expr:
        raise TestStepFail(format_message(message) if message is not None else 'Assert: %r != True' % expr)


def assertFalse(expr, message=None):
    if expr:
        raise TestStepFail(format_message(message) if message is not None else 'Assert: %r != False' % expr)


def assertNone(expr, message=None):
    if expr is not None:
        raise TestStepFail(format_message(message) if message is not None else "Assert: %s != None" % str(expr))


def assertNotNone(expr, message=None):
    if expr is None:
        raise TestStepFail(format_message(message) if message is not None else "Assert: %s == None" % str(expr))


def assertEqual(a, b, message=None):
    if not a == b:
        raise TestStepFail(format_message(message) if message is not None else "Assert: %s != %s" % (str(a), str(b)))

def assertNotEqual(a, b, message=None):
    if not a != b:
        raise TestStepFail(format_message(message) if message is not None else "Assert: %s == %s" % (str(a), str(b)))

def assertJsonContains(jsonStr=None, key=None, message=None):
    if jsonStr is not None:
        try:
            data=json.loads(jsonStr)
            if key not in data:
                raise TestStepFail(format_message(message) if message is not None else "Assert: Key : %s is not in : %s" % (str(key), str(jsonStr)))
        except (TypeError, ValueError) as e:
            raise TestStepFail(format_message(message) if message is not None else "Unable to parse json "+str(e))
    else:
        raise TestStepFail(format_message(message) if message is not None else "Json string is empty")
