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

import re
# Python version compatibility fix
try:
    basestring
except NameError:
    basestring = str

class Invert:
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
    position = 0
    for message in expectedResponse:
        try:
            ok, position, match = FindNext(lines, message, position)
           # print("ok: %i, position: %i, match: %s" % (ok, position, match))
            if ok == False:
                return False
            position = position + 1
        except TypeError as msg:
            #invalid type
            #traceback.print_exc()
            #print("Invalid SearchType: %s" % msg)
            return False
        except LookupError as msg:
            #Not found
            #print("Not Found: %s" % msg)
            return False
    return True
