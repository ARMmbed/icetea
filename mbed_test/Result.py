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
import datetime

try:
  import pwd
except ImportError:
  import getpass
  pwd = None

class Result(object):
    # Constructor for Result
    def __init__(self, kwargs = {}):
        self.__verdict = 'unknown'
        self.duration = 0
        self.fw_name = "mbedtest"
        self.fw_version = '0.1'
        self.build = 'unknown'

        self.buildDate = ''
        self.branch = 'unknown'
        self.tc_git_info = None
        self.commitId = ''
        self.gitUrl = ''
        self.jobId = ''
        self.buildUrl = ''
        self.campaign = ''

        self.fail_reason = ''
        self.skip_reason = ''
        self.dutType = '',
        self.dutCount = 0,
        self.dutVendor = 'atmel',
        self.dutModel = '',
        self.dutSn = ''
        self.logpath = None
        self.retcode = -1
        self.tester = self.__get_username()
        self.component = [] # CUT - Component Under Test
        self.feature = []   # FUT - Feature Under Test
        self.logfiles = []

        self.stdout = ''
        self.stderr = ''

        self.tc_metadata = {'name': 'unknown', 'purpose': ''}
        for key in kwargs:
            if key == 'testcase':
                self.tc_metadata['name']=kwargs[key]
            if key == 'tc_metadata':
                self.tc_metadata=kwargs[key]
            if key == 'verdict':
                self.setVerdict(kwargs[key])
            if key == 'build':
                self.build=kwargs[key]
            if key == 'buildDate':
                self.buildDate=kwargs[key]
            if key == 'buildUrl':
                self.buildUrl=kwargs[key]
            if key == 'branch':
                self.branch=kwargs[key]
            if key == 'commitId':
                self.commitId=kwargs[key]
            if key == 'gitUrl':
                self.gitUrl=kwargs[key]
            if key == 'buildUrl':
                self.buildUrl=kwargs[key]
            if key == 'jobId':
                self.jobId=kwargs[key]
            if key == 'campaign':
                self.campaign=kwargs[key]
            if key == 'duration':
                self.duration=kwargs[key]
            if key == 'branch':
                self.branch=kwargs[key]
            if key == 'skip_reason':
                self.skip_reason=kwargs[key]
            if key == 'reason':
                self.fail_reason=kwargs[key]
            if key == 'stdout':
                self.stdout=kwargs[key]
            if key == 'stderr':
                self.stderr=kwargs[key]
            if key == 'fw_name':
                self.fw_name=kwargs[key]
            if key == 'fw_version':
                self.fw_version=kwargs[key]
            if key == 'retcode':
                self.retcode=kwargs[key]
                if( self.retcode == 0 ):
                    self.setVerdict("pass", self.retcode)
                else:
                    self.setVerdict("fail", self.retcode)


    def getVerdict(self):
        return self.__verdict

    # Set final verdict
    def setVerdict(self, verdict, retcode = -1, duration = -1):
        verdict = verdict.lower()
        if not verdict in ['pass', 'fail', 'unknown', 'skip', 'inconclusive']:
            raise ValueError("Unknown verdict %s", verdict)
        if retcode == -1 and verdict == 'pass': retcode = 0
        self.__verdict = verdict
        self.retcode = retcode
        if duration >= 0:
            self.duration = duration

    def setTcMetadata(self, tc_metadata):
        self.tc_metadata = tc_metadata

    def getTestcaseName(self):
        return self.tc_metadata['name']

    def getDuration(self, seconds=False):
        if seconds:
            return str(self.duration)
        delta = datetime.timedelta(seconds=self.duration)
        return str(delta)

    # get testcase metadata
    def getTestcaseObj(self):
        return self.tc_metadata

    def hasLogs(self):
        files = []
        if os.path.exists( self.logpath ):
            for root, dirs, files in os.walk(os.path.abspath(self.logpath)):
              for file in files:
                files.append( os.path.join(root, file) )
            if len(files) > 0:
                return True, files
        return False, []

    # get current os username
    def __get_username(self):
        if pwd:
            return pwd.getpwuid(os.geteuid()).pw_name
        else:
            return getpass.getuser()
