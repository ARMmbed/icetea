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

Result module, contains the Result class which is used for storing the results and metadata of a
single test case for reporting purposes.
"""

import os
import datetime

from icetea_lib.tools.tools import get_fw_name, get_fw_version, set_or_delete
from icetea_lib.DeviceConnectors.DutInformation import DutInformationList

try:
    import pwd
except ImportError:
    import getpass
    pwd = None


class Result(object):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """
    Result object, used for storing all relevant information from the test case
    for reporting and storage purposes.
    """
    # Constructor for Result
    def __init__(self, kwargs=None):
        kwargs = {} if kwargs is None else kwargs
        self.__verdict = 'unknown'
        self.duration = kwargs.get("duration", 0)
        self.framework_info = {
            "name": kwargs.get("fw_name", get_fw_name()),
            "version": kwargs.get("fw_version", get_fw_version())
        }
        self.tc_git_info = {
            "url": kwargs.get("gitUrl", ''),
            "branch": kwargs.get("branch", ''),
            "commitId": kwargs.get("commitId", '')
        }
        self.job_id = kwargs.get("jobId", '')
        self.campaign = kwargs.get("campaign", '')
        self.retries_left = 0
        self.duration = kwargs.get("duration", 0)

        self.fail_reason = kwargs.get("reason", '')
        self.skip_reason = kwargs.get("skip_reason", '')
        self.dutinformation = DutInformationList()
        self.dut_type = ''
        self.dut_count = 0
        self.dut_vendor = []
        self.toolchain = 'unknown'
        self.logpath = None
        self.retcode = kwargs.get("retcode", -1)
        self.tester = Result.__get_username()
        self.component = []  # CUT - Component Under Test
        self.feature = []   # FUT - Feature Under Test
        self.logfiles = []
        self.tc_metadata = kwargs.get("tc_metadata", {'name': '', 'purpose': ''})
        self.tc_metadata['name'] = kwargs.get("testcase", '')
        self.stdout = kwargs.get("stdout", '')
        self.stderr = kwargs.get("stderr", '')
        if "verdict" in kwargs:
            self.set_verdict(kwargs.get("verdict"))
        if 'retcode' in kwargs:
            self.retcode = kwargs.get("retcode")
            if self.retcode == 0:
                self.set_verdict("pass", self.retcode)
            else:
                self.set_verdict("fail", self.retcode)
        self.uploaded = False

    def set_tc_git_info(self, git_info):
        """
        Set test case git information.

        :param git_info: git information as dictionary. Keys: url, branch and commitId
        :return: Nothing
        """
        self.tc_git_info.update(git_info)

    # TC properties

    # TC git branch
    @property
    def tcbranch(self):
        """
        get test case git branch.

        :return: branch
        """
        return self.tc_git_info.get('branch')

    @tcbranch.setter
    def tcbranch(self, value):
        set_or_delete(self.tc_git_info, 'branch', value)

    # TC GIT commit id
    @property
    def tc_commit_id(self):
        """
        get test case commit id.

        :return: commit id
        """
        return self.tc_git_info.get('commitId')

    @tc_commit_id.setter
    def tc_commit_id(self, value):
        set_or_delete(self.tc_git_info, 'commitId', value)

    # TC GIT URL
    @property
    def tc_git_url(self):
        """
        get test case git url.

        :return: git url
        """
        return self.tc_git_info.get('url', self.tc_git_info.get('scm_link'))

    @tc_git_url.setter
    def tc_git_url(self, value):
        self.tc_git_info['gitUrl'] = value

    # BUILD

    # Build name
    @property
    def build(self):
        """
        get build name.

        :return: build name. None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.name
        return None

    @build.setter
    def build(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.name = value

    # Build name
    @property
    def build_date(self):
        """
        get build date.

        :return: build date. None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.date
        return None

    @build_date.setter
    def build_date(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.date = value

    # Build file sha1
    @property
    def build_sha1(self):
        """
        get sha1 hash of build.

        :return: build sha1 or None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.sha1
        return None

    @build_sha1.setter
    def build_sha1(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.sha1 = value

    @property
    def build_url(self):
        """
        get build url.

        :return: build url or None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.build_url
        return None

    @build_url.setter
    def build_url(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.build_url = value

    @property
    def build_git_url(self):
        """
        get build git url.

        :return: build git url or None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.giturl
        return None

    @build_git_url.setter
    def build_git_url(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.giturl = value

    @property
    def build_data(self):
        """
        get build data.

        :return: build data or None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.get_data()
        return None

    @property
    def build_branch(self):
        """
        get build branch.

        :return: build branch or None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.branch
        return None

    @build_branch.setter
    def build_branch(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.branch = value

    @property
    def buildcommit(self):
        """
        get build commit id.

        :return: build commit id or None if not found
        """
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            return self.dutinformation.get(0).build.commit_id
        return None

    @buildcommit.setter
    def buildcommit(self, value):
        # pylint: disable=len-as-condition
        if len(self.dutinformation) > 0 and (self.dutinformation.get(0).build is not None):
            self.dutinformation.get(0).build.commit_id = value

    # FRAMEWORK

    @property
    def fw_name(self):
        """
        get test framework name.

        :return: framework name or None if not found
        """
        return self.framework_info.get("name")

    @fw_name.setter
    def fw_name(self, value):
        self.framework_info["name"] = value

    @property
    def fw_version(self):
        """
        get framework version.

        :return: framework version or None if not found
        """
        return self.framework_info.get("version")

    @fw_version.setter
    def fw_version(self, value):
        self.framework_info["version"] = value

    @property
    def skip(self):
        """
        Determine if test was skipped.

        :return: True if test was skipped, else False
        """
        return self.skipped()

    @property
    def success(self):
        """
        Determine if test was passed.

        :return: True if test was passed, else False
        """
        return self.passed()

    @property
    def failure(self):
        """
        Determine if test failed.

        :return: True if test failed, else False
        """
        return self.failed()

    @property
    def inconclusive(self):
        """
        Determine if test was inconclusive.

        :return: True if test was inconclusive, else False
        """
        return self.was_inconclusive()

    def get_verdict(self):
        """
        Get test verdict.

        :return: verdict
        """
        return self.__verdict

    # Set final verdict
    def set_verdict(self, verdict, retcode=-1, duration=-1):
        """
        Set the final verdict for this Result.

        :param verdict: Verdict, must be from ['pass', 'fail', 'unknown', 'skip', 'inconclusive']'
        :param retcode: integer return code
        :param duration: test duration
        :return: Nothing
        :raises: ValueError if verdict was unknown.
        """
        verdict = verdict.lower()
        if not verdict in ['pass', 'fail', 'unknown', 'skip', 'inconclusive']:
            raise ValueError("Unknown verdict {}".format(verdict))
        if retcode == -1 and verdict == 'pass':
            retcode = 0
        self.__verdict = verdict
        self.retcode = retcode
        if duration >= 0:
            self.duration = duration

    def build_result_metadata(self, data=None, args=None):
        """
        collect metadata into this object

        :param data: dict
        :param args: build from args instead of data
        """
        data = data if data else self._build_result_metainfo(args)
        if data.get("build_branch"):
            self.build_branch = data.get("build_branch")
        if data.get("buildcommit"):
            self.buildcommit = data.get("buildcommit")
        if data.get("build_git_url"):
            self.build_git_url = data.get("build_git_url")
        if data.get("build_url"):
            self.build_url = data.get("build_url")
        if data.get("campaign"):
            self.campaign = data.get("campaign")
        if data.get("job_id"):
            self.job_id = data.get("job_id")
        if data.get("toolchain"):
            self.toolchain = data.get("toolchain")
        if data.get("build_date"):
            self.build_date = data.get("build_date")

    @staticmethod
    def _build_result_metainfo(args):
        """
        Internal helper for collecting metadata from args to results
        """
        data = dict()
        if hasattr(args, "branch") and args.branch:
            data["build_branch"] = args.branch
        if hasattr(args, "commitId") and args.commitId:
            data["buildcommit"] = args.commitId
        if hasattr(args, "gitUrl") and args.gitUrl:
            data["build_git_url"] = args.gitUrl
        if hasattr(args, "buildUrl") and args.buildUrl:
            data["build_url"] = args.buildUrl
        if hasattr(args, "campaign") and args.campaign:
            data["campaign"] = args.campaign
        if hasattr(args, "jobId") and args.jobId:
            data["job_id"] = args.jobId
        if hasattr(args, "toolchain") and args.toolchain:
            data["toolchain"] = args.toolchain
        if hasattr(args, "buildDate") and args.buildDate:
            data["build_date"] = args.buildDate
        return data

    def set_tc_metadata(self, tc_metadata):
        """
        Set test case metadata.

        :param tc_metadata: dictionary
        :return: Nothing
        """
        self.tc_metadata = tc_metadata

    def get_tc_name(self):
        """
        Get name from tc metadata.

        :return: Name from tc metadata
        """
        return self.tc_metadata['name']

    def get_toolchain(self):
        """
        get toolchain.

        :return: toolchain
        """
        return self.toolchain

    def passed(self):
        """
        Determine if test passed.

        :return: True if test was passed, else False
        """
        return self.get_verdict() == 'pass'

    def skipped(self):
        """
        Determine if test was skipped.

        :return: True if test was skipped, else False
        """
        return self.get_verdict() == 'skip'

    def was_inconclusive(self):
        """
        Determine if test was inconclusive.

        :return: True if test was inconclusive, else False
        """
        return self.get_verdict() == 'inconclusive'

    def failed(self):
        """
        Determine if test failed.

        :return: True if test failed, else False
        """
        return self.get_verdict() == 'fail'

    def get_fail_reason(self):
        """
        Get fail reason.

        :return: failure reason
        """
        return self.fail_reason

    def set_dutinformation(self, info):
        """
        Create a new DutInformationList with initial data info.

        :param info: list of DutInformation objects
        :return: Nothing
        """
        self.dutinformation = DutInformationList(info)

    def add_dutinformation(self, info):
        """
        Append the information of a new dut to the dutinformation list.

        :param info: DutInformation object
        :return: Nothing
        """
        self.dutinformation.append(info)

    @property
    def dut_resource_id(self):
        """
        Get dut resource id:s.

        :return: list of resource id:s or unknown if none were found.
        """
        return self.dutinformation.get_resource_ids()

    def get_dut_models(self):
        """
        Gets a string of dut models in this TC.

        :return: String of dut models separated with commas.
        unknown platform if no dut information is available
        """
        return self.dutinformation.get_uniq_string_dutmodels()

    @property
    def dut_models(self):
        """
        Gets a list of dut models in this TC.

        :return: List of dut models in this TC. Empty list if information is not available.
        """
        return self.dutinformation.get_uniq_list_dutmodels()

    def get_duration(self, seconds=False):
        """
        Get test case duration.

        :param seconds: if set to True, return tc duration in seconds, otherwise as str(
        datetime.timedelta)
        :return: str(datetime.timedelta) or duration as string in seconds
        """
        if seconds:
            return str(self.duration)
        delta = datetime.timedelta(seconds=self.duration)
        return str(delta)

    # get testcase metadata
    def get_tc_object(self):
        """
        get tc metadata.

        :return: tc metadata dictionary
        """
        return self.tc_metadata

    def has_logs(self):
        """
        Check if log files are available and return file names if they exist.

        :return: list
        """
        found_files = []
        if self.logpath is None:
            return found_files
        if os.path.exists(self.logpath):
            for root, _, files in os.walk(os.path.abspath(self.logpath)):

                for fil in files:
                    found_files.append(os.path.join(root, fil))
        return found_files

    # get current os username
    @staticmethod
    def __get_username():
        """
        Get current os username.

        :return: os username.
        """
        if pwd:
            return pwd.getpwuid(os.geteuid()).pw_name
        return getpass.getuser()
