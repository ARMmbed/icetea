# pylint: disable=redefined-builtin

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
# Python version compatibility fix
try:
    basestring
except NameError:
    basestring = str  # pylint: disable=invalid-name


class Invert(object):  # pylint: disable=too-few-public-methods
    """
    Class Invert
    """
    def __init__(self, string_obj):
        self.str = string_obj

    def __str__(self):
        return self.str


def find_next(lines, find_str, start_index):
    """
    Find the next instance of find_str from lines starting from start_index.

    :param lines: Lines to look through
    :param find_str: String or Invert to look for
    :param start_index: Index to start from
    :return: (boolean, index, line)
    """
    mode = None
    if isinstance(find_str, basestring):
        mode = 'normal'
        message = find_str
    elif isinstance(find_str, Invert):
        mode = 'invert'
        message = str(find_str)
    else:
        raise TypeError("Unsupported message type")
    for i in range(start_index, len(lines)):
        if re.search(message, lines[i]):
            return mode == 'normal', i, lines[i]
        elif message in lines[i]:
            return mode == 'normal', i, lines[i]
    if mode == 'invert':
        return True, len(lines), None
    raise LookupError("Not found")


def verify_message(lines, expected_response):
    """
    Looks for expectedResponse in lines.

    :param lines: a list of strings to look through
    :param expected_response: list or str to look for in lines.
    :return: True or False.
    :raises: TypeError if expectedResponse was not list or str.
    LookUpError through FindNext function.
    """
    position = 0
    if isinstance(expected_response, basestring):
        expected_response = [expected_response]
    if isinstance(expected_response, set):
        expected_response = list(expected_response)
    if not isinstance(expected_response, list):
        raise TypeError("verify_message: expectedResponse must be list, set or string")
    for message in expected_response:
        try:
            found, position, _ = find_next(lines, message, position)
            if not found:
                return False
            position = position + 1
        except TypeError:
            return False
        except LookupError:
            return False
    return True
