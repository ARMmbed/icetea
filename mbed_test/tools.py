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

import os
import sys
import platform
import ctypes
import re
import importlib
from sys import platform as _platform
import traceback
from sys import version_info
if not version_info[0] != 2:  #(2, 6, 4, 'final', 0)
    from Queue import Empty
else:
    from queue import Empty

# Check if number is integer or not
def check_int(s):
    if isinstance(s, str) == False:
        return False
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

# Convert string to the number
def num(s):
    try:
        if check_int(s):
            return int(s)
        else:
            return -1
    except ValueError:
        return -1

unixPlatform = _platform == "linux" or _platform == "linux2" or _platform == "darwin"

# Check if PID (process id) is running
def is_pid_running(pid):
    return (_is_pid_running_on_windows(pid) if platform.system() == "Windows"
        else _is_pid_running_on_unix(pid))

def _is_pid_running_on_unix(pid):
    try:
        os.kill(pid, 0)

    except OSError as err:
        # if error is ESRCH, it means the process doesn't exist
        return not err.errno == os.errno.ESRCH
    return True


def _is_pid_running_on_windows(pid):
    import ctypes.wintypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(1, 0, pid)
    if handle == 0:
        return False
    exit_code = ctypes.wintypes.DWORD()
    ret = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
    is_alive = (ret == 0 or exit_code.value == _STILL_ALIVE)
    kernel32.CloseHandle(handle)
    return is_alive

ansi_pattern = '\033\[((?:\d|;)*)([a-zA-Z])'
ansi_eng = re.compile(ansi_pattern)

def strip_escape(string=''):
    lastend = 0
    matches = []
    newstring = str(string)
    for match in ansi_eng.finditer(string):
        start = match.start()
        end = match.end()
        matches.append(match)
    matches.reverse()
    for match in matches:
        start = match.start()
        end = match.end()
        string = string[0:start] + string[end:]
    return string


def loadClass(full_class_string, verbose=False, silent=False):
    """
    dynamically load a class from a string
    """
    if not isinstance(full_class_string, str):
        if not silent:
            print("Error, loadClass: input not a string: %s" %str(full_class_string))
        return None
    if len(full_class_string) == 0:
        if not silent:
            print("Error, loadClass: empty string")
        return None
    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]
    try:
        module = importlib.import_module(module_path)
        # Finally, we retrieve the Class
        return getattr(module, class_str)
    except AttributeError:
        return None
    except Exception as e:
        if not silent:
            print("Error, loadClass: Module not found: %s" %module_path)
        if(verbose):traceback.print_exc()
        #TODO: return a string with a concise reason instead of traceback.
        return None

def flush_queue(q):
    while True:
        try:
            q.get(block=False)
        except Empty:
            break

def get_abs_path(relativePath):
    absPath = '/'.join(os.path.abspath(sys.modules[__name__].__file__).split('/')[:-1])
    absPath =  os.path.abspath(absPath +'/'+ relativePath)
    return absPath

def verifyModule(src, dst):
    # check if module exists
    if not os.path.exists(dst):
        # if not, create symlink for it
        try:
            os.symlink(src, dst)
        except Exception:
            raise EnvironmentError(dst+" library missing!")

def get_pkg_version(pkg_name, parse=False):
    '''verify and get installed python package version
    :param pkg_name:    python package name
    :param parse: parse version number with pkg_resourc.parse_version -function
    :return: None if pkg is not installed, otherwise version as a string or parsed version when parse=True
    '''
    import pkg_resources  # part of setuptools
    try:
        version = pkg_resources.require(pkg_name)[0].version
        return pkg_resources.parse_version(version) if parse else version
    except pkg_resources.DistributionNotFound:
        return None

def get_number(s):
    """
    :param s: string, where to look up numbers(integer)
    :return: number or None if number(integer) is not found
    """
    m = re.match(".*([\d]{1,})", s)
    if m:
        return int(m.group(1))
    else:
        return None

def strintkey_to_intkey(item):
    """
    :param item: dictionary, where some keys are string integers
    :return: nothing. Modifies dictionary in-place.
    """
    if isinstance(item, dict):
        for key, value in item.items():
            new_key = None
            if isinstance(key, basestring) and key.isdigit():
                new_key = int(key)
            strintkey_to_intkey(value)
            if new_key:
                # This will overwrite an existing key. However, since this
                # function is used with the assumption that such a key doesn't
                # exist(because that's the use case for this function), it's
                # not an issue.
                item[new_key] = value
                del item[key]
            else:
                item[key] = value

ogcounter = 0
def generate_object_graphs_by_class(classlist):
    """
    Generate reference and backreference graphs for objects of type class for each class given in classlist. Useful for
    debugging reference leaks in framework etc.

    Usage example to generate graphs for class "someclass":
    >>> import someclass
    >>> someclassobject = someclass()
    >>> generate_object_graphs_by_class(someclass)

    Needs "objgraph" module installed.
    """
    try:
        import objgraph, gc
    except ImportError:
        return
    interesting_classes = []
    graphcount = 0
    if not isinstance(classlist, list):
        classlist = [classlist]
    for ic in classlist:
        for obj in gc.get_objects():
            if isinstance(obj, ic):
                graphcount += 1
                objgraph.show_refs([obj], filename='%d_%s_%d_refs.png' % (ogcounter, obj.__class__.__name__, graphcount))
                objgraph.show_backrefs([obj], filename='%d_%s_%d_backrefs.png' % (ogcounter, obj.__class__.__name__, graphcount))
