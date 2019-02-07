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

__author__ = 'jusvat01'

from threading import Thread
import signal
import time


class Timeout(object):  # pylint: disable=too-few-public-methods
    """
    Timeout class using ALARM signal.
    """
    class Timeout(Exception):
        """
        Internal Timeout exception
        """
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGABRT, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):  # pylint: disable=unused-argument,no-self-use
        """
        Raise a Timeout exception
        :param args: Not used
        :return: Nothing
        :raises: Timeout
        """
        raise Timeout.Timeout()


class Timer(Thread):
    """
    Timer class, simple timer that sleeps for timeout seconds.
    """
    def __init__(self):
        super(Timer, self).__init__()
        self.timeout = None

    def wait(self, timeout):
        """
        Starts the Timer for timeout seconds, then gives 5 second grace period to join the thread.
        :param timeout: Duration for timer.
        :return: Nothing
        """
        self.timeout = timeout
        self.start()
        self.join(timeout=5)

    def run(self):
        """
        Just sleep for self.timeout seconds.
        :return:
        """
        time.sleep(self.timeout)
