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


class LockFile:
    """
    Simple lock class for locking a file.
    """
    def __init__(self, filename):
        self._lock_filename = filename + ".lock"
        self._lockfd = None

    def acquire(self):
        try:
            self._lock_fd = os.open(self._lock_filename, os.O_CREAT | os.O_EXCL)
        except OSError:
            return False
        return True

    def release(self):
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            try:
                os.remove(self._lock_filename)
            except OSError:
                # Hmm, someone deleted our lock while we had it locked? Nothing we can do, so just continue
                pass


def removeFile(filename, path=None):
    cwd = os.getcwd()
    try:
        if path:
            os.chdir(path)
    except OSError:
        raise
    try:
        os.remove(filename)
        os.chdir(cwd)
        return True
    except OSError as e:
        os.chdir(cwd)
        raise


def renameFile(old, new, path=None):
    cwd = os.getcwd()
    try:
        if path:
            os.chdir(path)
    except OSError:
        raise
    try:
        os.rename(old, new)
        os.chdir(cwd)
        return True
    except OSError:
        os.chdir(cwd)
        raise
