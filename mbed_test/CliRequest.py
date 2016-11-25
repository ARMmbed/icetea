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

import time

# Command Request
class CliRequest(object):
    def __init__(self, cmd="", timestamp=time.time(), **kwargs):
        self.cmd = cmd
        self.wait = True
        self.timeout = 10
        self.async = False
        self.timestamp = timestamp
        self.expectedRetcode = 0
        self.response = None
        self.dutIndex = -1

        for key in kwargs:
            if key == 'wait':
                self.wait = kwargs[key]
            elif key == 'expectedRetcode':
                self.expectedRetcode = kwargs[key]
            elif key == 'timeout':
                self.timeout = kwargs[key]
            elif key == 'async':
                self.async = kwargs[key]
            elif key == 'dutIndex':
                self.dutIndex = kwargs[key]

    def __str__(self):
        return self.cmd

    def get_timedelta(self, now):
        return now-self.timestamp
