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

# pylint: disable=invalid-name

import inspect
import os
import json

from icetea_lib.TestStepError import TestStepFail


def format_message(msg):
    """
    Formatting function for assert messages. Fetches the filename,
    function and line number of the code causing the fail
    and formats it into a three-line error message. Stack inspection is used to get the information.
    Originally done by BLE-team for their testcases.

    :param msg: Message to be printed along with the information.
    :return: Formatted message as string.
    """
    callerframerecord = inspect.stack()[2]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    _, filename = os.path.split(info.filename)
    caller_site = "In file {!s}, in function {!s}, at line {:d}".format(filename,
                                                                        info.function,
                                                                        info.lineno)
    return "{!s}\n{!s}\n{!s}".format(msg, caller_site, info.code_context)


def assertTraceDoesNotContain(response, message):
    """
    Raise TestStepFail if response.verify_trace finds message from response traces.

    :param response: Response. Must contain method verify_trace
    :param message: Message to look for
    :return: Nothing
    :raises: AttributeError if response does not contain verify_trace method.
    TestStepFail if verify_trace returns True.
    """
    if not hasattr(response, "verify_trace"):
        raise AttributeError("Response object does not contain verify_trace method!")
    if response.verify_trace(message, False):
        raise TestStepFail('Assert: Message(s) "%s" in response' % message)


def assertTraceContains(response, message):
    """
    Raise TestStepFail if response.verify_trace does not find message from response traces.

    :param response: Response. Must contain method verify_trace
    :param message: Message to look for
    :return: Nothing
    :raises: AttributeError if response does not contain verify_trace method.
    TestStepFail if verify_trace returns False.
    """
    if not hasattr(response, "verify_trace"):
        raise AttributeError("Response object does not contain verify_trace method!")
    if not response.verify_trace(message, False):
        raise TestStepFail('Assert: Message(s) "%s" not in response' % message)


def assertDutTraceDoesNotContain(dut, message, bench):
    """
    Raise TestStepFail if bench.verify_trace does not find message from dut traces.

    :param dut: Dut object.
    :param message: Message to look for.
    :param: Bench, must contain verify_trace method.
    :raises: AttributeError if bench does not contain verify_trace method.
    TestStepFail if verify_trace returns True.
    """
    if not hasattr(bench, "verify_trace"):
        raise AttributeError("Bench object does not contain verify_trace method!")
    if bench.verify_trace(dut, message, False):
        raise TestStepFail('Assert: Message(s) "%s" in response' % message)


def assertDutTraceContains(dut, message, bench):
    """
    Raise TestStepFail if bench.verify_trace finds message from dut traces.

    :param dut: Dut object.
    :param message: Message to look for.
    :param: Bench, must contain verify_trace method.
    :raises: AttributeError if bench does not contain verify_trace method.
    TestStepFail if verify_trace returns True.
    """
    if not hasattr(bench, "verify_trace"):
        raise AttributeError("Bench object does not contain verify_trace method!")
    if not bench.verify_trace(dut, message, False):
        raise TestStepFail('Assert: Message(s) "%s" not in response' % message)


def assertTrue(expr, message=None):
    """
    Assert that expr evaluates to True.

    :param expr: expression to evaluate.
    :param message: Message set to raised Exception
    :raises: TestStepFail if not expr.
    """
    if not expr:
        raise TestStepFail(
            format_message(message) if message is not None else 'Assert: %r != True' % expr)


def assertFalse(expr, message=None):
    """
    Assert that expr evaluates to False.

    :param expr: expression to evaluate.
    :param message: Message set to raised Exception
    :raises: TestStepFail if expr.
    """
    if expr:
        raise TestStepFail(
            format_message(message) if message is not None else 'Assert: %r != False' % expr)


def assertNone(expr, message=None):
    """
    Assert that expr is None.

    :param expr: expression.
    :param message: Message set to raised Exception
    :raises: TestStepFail if expr is not None.
    """
    if expr is not None:
        raise TestStepFail(
            format_message(message) if message is not None else "Assert: %s != None" % str(expr))


def assertNotNone(expr, message=None):
    """
    Assert that expr is not None.

    :param expr: expression.
    :param message: Message set to raised Exception
    :raises: TestStepFail if expr is None.
    """
    if expr is None:
        raise TestStepFail(
            format_message(message) if message is not None else "Assert: %s == None" % str(expr))


def assertEqual(first, second, message=None):
    """
    Assert that first equals second.

    :param first: First part to evaluate
    :param second: Second part to evaluate
    :param message: Failure message
    :raises: TestStepFail if not first == second
    """
    if not first == second:
        raise TestStepFail(
            format_message(message) if message is not None else "Assert: %s != %s" % (str(first),
                                                                                      str(second)))


def assertNotEqual(first, second, message=None):
    """
    Assert that first does not equal second.

    :param first: First part to evaluate
    :param second: Second part to evaluate
    :param message: Failure message
    :raises: TestStepFail if not first != second
    """
    if not first != second:
        raise TestStepFail(
            format_message(message) if message is not None else "Assert: %s == %s" % (str(first),
                                                                                      str(second)))


def assertJsonContains(jsonStr=None, key=None, message=None):
    """
    Assert that jsonStr contains key.

    :param jsonStr: Json as string
    :param key: Key to look for
    :param message: Failure message
    :raises: TestStepFail if key is not in jsonStr or
    if loading jsonStr to a dictionary fails or if jsonStr is None.
    """
    if jsonStr is not None:
        try:
            data = json.loads(jsonStr)
            if key not in data:
                raise TestStepFail(
                    format_message(message) if message is not None else "Assert: "
                                                                        "Key : %s is not "
                                                                        "in : %s" % (str(key),
                                                                                     str(jsonStr)))
        except (TypeError, ValueError) as e:
            raise TestStepFail(
                format_message(message) if message is not None else "Unable to parse json "+str(e))
    else:
        raise TestStepFail(
            format_message(message) if message is not None else "Json string is empty")
