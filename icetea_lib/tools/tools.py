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

import os
import sys
import platform
import re
import string
import importlib
import inspect
from pkg_resources import require, DistributionNotFound
from six import iteritems
from sys import platform as _platform
try:
    from queue import Empty
except ImportError:
    from Queue import Empty

from sys import version_info

UNIXPLATFORM = _platform == "linux" or _platform == "linux2" or _platform == "darwin"
IS_PYTHON3 = version_info[0] == 3


def get_fw_name():
    """
    :return: Framework name as str
    """
    return "Icetea"


def get_fw_version():
    """
    Try to get version of the framework. First try pkg_resources.require, if that fails
    read from setup.py
    :return: Version as str
    """
    version = 'unknown'
    try:
        pkg = require(get_fw_name())[0]
    except DistributionNotFound:
        # Icetea is not installed. try to read version string from setup.py
        try:
            setup_path = os.path.abspath(os.path.dirname(__file__)+'/../..')
            with open(os.path.join(setup_path, 'setup.py')) as setup_file:
                lines = setup_file.readlines()
                for line in lines:
                    m = re.search(r"VERSION = \"([\S]{5,})\"", line)
                    if m:
                        version = m.group(1)
                        break
        except Exception:  # pylint: disable=broad-except
            pass
    else:
        version = "-rc".join(pkg.version.split("rc"))
    return version


# calculate sha1 for a file
def sha1_of_file(filepath):
    """
    Get sha1 of file
    :param filepath: File to hash
    :return: sha1 hash of file or None
    """
    import hashlib
    try:
        with open(filepath, 'rb') as file_to_hash:
            return hashlib.sha1(file_to_hash.read()).hexdigest()
    except:
        return None

# Check if number is integer or not
def check_int(s):
    """
    Check if number is integer or not.

    :param s: Number as str
    :return: Boolean
    """
    if not isinstance(s, str):
        return False
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()


# Convert string to the number
def num(s):
    """
    Convert string to the number.

    :param s: String to convert
    :return: int or None
    """
    try:
        if check_int(s):
            return int(s)
        else:
            return -1
    except ValueError:
        return -1


# Check if PID (process id) is running
def is_pid_running(pid):
    """
    Check if PID (process id) is running.

    :param pid: Pid to check
    :return : Boolean
    """
    if platform.system() == "Windows":
        return _is_pid_running_on_windows(pid)
    return _is_pid_running_on_unix(pid)


def _is_pid_running_on_unix(pid):
    """
    Check if PID is running for Unix systems.
    """
    try:
        os.kill(pid, 0)
    except OSError as err:
        # if error is ESRCH, it means the process doesn't exist
        return not err.errno == os.errno.ESRCH
    return True


def _is_pid_running_on_windows(pid):
    """
    Check if PID is running for Windows systems
    """
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


def strip_escape(string='', encoding="utf-8"):
    """
    Strip escape characters from string.

    :param string: string to work on
    :return: stripped string
    """
    matches = []
    try:
        if hasattr(string, "decode"):
            string = string.decode(encoding)
    except Exception: # pylint: disable=broad-except
        # Tried to decode something that is not decodeable in the specified encoding. Let's just
        # move on.
        pass
    try:
        for match in ansi_eng.finditer(string):
            matches.append(match)
    except TypeError as error:
        raise TypeError("Unable to strip escape characters from data {}: {}".format(
            string, error))
    matches.reverse()
    for match in matches:
        start = match.start()
        end = match.end()
        string = string[0:start] + string[end:]
    return string


def load_class(full_class_string, verbose=False, silent=False):
    """
    dynamically load a class from a string
    """
    if not isinstance(full_class_string, str):
        if not silent:
            print("Error, loadClass: input not a string: %s" % str(full_class_string))
        return None
    if len(full_class_string) == 0:
        if not silent:
            print("Error, loadClass: empty string")
        return None
    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]
    try:
        module_ = importlib.import_module(module_path)
        # Finally, we retrieve the Class
        return getattr(module_, class_str)
    except AttributeError:
        return None
    except Exception as e:
        raise e


def import_module(modulename):
    """
    Static method for importing module modulename. Can handle relative imports as well.

    :param modulename: Name of module to import. Can be relative
    :return: imported module instance.
    """
    module = None
    try:
        module = importlib.import_module(modulename)
    except ImportError:
        # If importing fails we see if the modulename has dots in it, split the name.
        if "." in modulename:
            modules = modulename.split(".")
            package = ".".join(modules[1:len(modules)])
            # Might raise an ImportError again. If so, we really failed to import the module.
            module = importlib.import_module(package)
        else:
            # No dots, really unable to import the module. Raise.
            raise
    return module


def flush_queue(queue):
    """
    Flush the queue.

    :param queue: queue to flush
    :return: Nothing
    """
    while True:
        try:
            queue.get(block=False)
        except Empty:
            break


def get_abs_path(relative_path):
    """
    Get absolute path for relative path.

    :param relative_path: Relative path
    :return: absolute path
    """
    abs_path = os.path.sep.join(os.path.abspath(sys.modules[__name__].__file__).split(os.path.sep)[
                               :-1])
    abs_path = os.path.abspath(abs_path + os.path.sep + relative_path)
    return abs_path


def get_pkg_version(pkg_name, parse=False):
    """
    Verify and get installed python package version.

    :param pkg_name:    python package name
    :param parse: parse version number with pkg_resourc.parse_version -function
    :return: None if pkg is not installed,
    otherwise version as a string or parsed version when parse=True
    """
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


def combine_urls(path1, path2):
    """
    Returns the combination of two urls and checks that there are no double slashes at the seam.
    TODO: Extend to check for other anomalies as well.

    :param path1: First part of the url
    :param path2: Second part of the url
    :return: Combination of the paths with double slashes removed
    """
    if path1.endswith("/") and path2.startswith("/"):
        path2 = path2.replace("/", "", 1)
    elif path1.endswith("/") == False and path2.startswith("/") == False:
        path2 = "/" + path2
    return path1 + path2


def recursive_dictionary_get(keys, dict):
    """
    Gets contents of requirement key recursively so users can search
    for specific keys inside nested requirement dicts.

    :param key: key or dot separated string of keys to look for.
    :param dict: Dictionary to search from
    :return: results of search or None
    """
    if "." in keys and len(keys) > 1:
        key = keys.split(".", 1)
        new_dict = dict.get(key[0])
        # Make sure that the next level actually has a dict we can continue the search from.
        if not new_dict or not hasattr(new_dict, "get"):
            return None
        return recursive_dictionary_get(key[1], new_dict)
    else:
        return dict.get(keys) if (dict and hasattr(dict, "get")) else None


def test_case(testcasebase, **kwargs):
    """
    Decorator which allow definition of test cases as simple functions.

    :param testcasebase: this is the base class that will be used to create
    the test case. It is exected that this base class implement __init__,
    setUp and tearDown
    :param kwargs: Dictionary of arguments that will be passed as initialization
    parameters of the test case
    """
    def wrap(case_function):
        kwargs['name'] = name = kwargs.get('name', case_function.__name__)
        class_name = "class_" + name
        func_globals = case_function.__globals__ if IS_PYTHON3 else case_function.func_globals
        func_globals[class_name] = type(
            class_name,
            (testcasebase,object), {
                '__init__': lambda self:
                    testcasebase.__init__(self, **kwargs),
                'IS_TEST': True,
                'case': case_function
            }
        )
        return case_function
    return wrap


def remove_empty_from_dict(d):
    """
    Remove empty items from dictionary d

    :param d:
    :return:
    """
    if type(d) is dict:
        return dict(
            (k,
             remove_empty_from_dict(v)) for k, v in iteritems(d) if v and remove_empty_from_dict(v))
    elif type(d) is list:
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    else:
        return d


def hex_escape_str(original_str):
    """
    Function to make sure we can generate proper string reports.
    If character is not printable, call repr for that character.
    Finally join the result.
    :param original_str: Original fail reason as string.
    :return: string
    """
    new = []
    for char in original_str:
        if str(char) in string.printable:
            new.append(str(char))
            continue

        if IS_PYTHON3:
            new.append(str(char).encode("unicode_escape").decode("ascii"))
        else:
            new.append(repr(char).replace("'", ""))
    return "".join(new)


def set_or_delete(dictionary, key, value):
    """
    Set value as value of dict key key. If value is None, delete key key from dict.

    :param dictionary: Dictionary to work on.
    :param key: Key to set or delete. If deleting and key does not exist in dict, nothing is done.
    :param value: Value to set. If value is None, delete key.
    :return: Nothing, modifies dict in place.
    """
    if value:
        dictionary[key] = value
    else:
        if dictionary.get(key):
            del dictionary[key]


def split_by_n(seq, n):
    """
    A generator to divide a sequence into chunks of n units.
    """
    while seq:
        yield seq[:n]
        seq = seq[n:]


def getargspec(fnct):
    """
    Compatibility wrapper for inspect.getargspec, which is deprecated in python 3.

    :param fnct: Function to inspect
    :return: Named tuple
    """
    if IS_PYTHON3:
        return inspect.getfullargspec(fnct)  # pylint: disable=no-member
    return inspect.getargspec(fnct)


class Singleton(type):
    """
    Singleton metaclass implementation:
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
