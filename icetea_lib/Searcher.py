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
    basestring = str

class Invert(object):
    def __init__(self, str):
        self.str = str
    def __str__(self):
        return self.str


def FindNext(lines, find_str, startIndex):
    mode = None
    if isinstance(find_str, basestring):
        mode = 'normal'
        message = find_str
    elif isinstance(find_str, Invert):
        mode = 'invert'
        message = str(find_str)
    else:
        raise TypeError("Unsupported message type")
    for i in range(startIndex, len(lines)):
        if re.search(message, lines[i]):
            return mode == 'normal', i, lines[i]
        elif message in lines[i]:
            return mode == 'normal', i, lines[i]
    if mode == 'invert':
        return True, i, None
    raise LookupError("Not found")


def verifyMessage(lines, expectedResponse):
    """
    Looks for expectedResponse in lines

    :param lines: a list of strings to look through
    :param expectedResponse: list or str to look for in lines.
    :return: True or False.
    :raises: TypeError if expectedResponse was not list or str.
            LookUpError through FindNext function.
    """
    position = 0
    if isinstance(expectedResponse, basestring):
        expectedResponse = [expectedResponse]
    if isinstance(expectedResponse, set):
        expectedResponse = list(expectedResponse)
    if not isinstance(expectedResponse, list):
        raise TypeError("VerifyMessage: expectedResponse must be list, set or string")
    for message in expectedResponse:
        try:
            ok, position, match = FindNext(lines, message, position)
            if not ok:
                return False
            position = position + 1
        except TypeError:
            return False
        except LookupError:
            return False
    return True
