"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Authors:
Jussi Vatjus-Anttila <jussi.vatjus-anttila@arm.com>
"""

import re
import os
import requests
from icetea_lib.tools.tools import sha1_of_file


class NotFoundError(Exception):
    """
    Not Found Error
    """
    pass


class Build(object):
    """
    Class Build
    """
    def __init__(self, **kwargs):
        """
        :param kwargs: dictionary of ref, type
        :return: nothing
        """
        self._ref = kwargs['ref']
        self._type = kwargs['type']
        self.name = None
        self.date = None
        self.sha1 = None
        self.branch = None
        self.toolchain = None
        self.build_url = None
        self.giturl = None
        self.commit_id = None

    @staticmethod
    def init(ref):
        """function init
        ref: reference for build, e.g. file:c:\\.. or http://...
        """
        r_http = re.compile(r"^(https?:.*)")
        r_uuid = re.compile(
            r"^([a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})$",
            re.I)
        r_id = re.compile(r"^([0-9a-fA-F]{24})$")
        r_file = re.compile(r"^file:(.*)$")
        r_any = re.compile(r"([\S\s]{4,})$")
        types = [
            {"cls": BuildHttp, "res": [r_http]},
            {"cls": BuildDatabase, "res": [r_uuid, r_id]},
            {"cls": BuildFile, "res": [r_file, r_any]}
        ]

        for _type in types:
            for reg in _type["res"]:
                match = reg.match(ref)
                if match:
                    return _type["cls"](ref=match.group(1))

        raise NotImplementedError("Cannot detect reference type: %s" % ref)

    def get_data(self):
        """
        function get_data
        :return: Buffer
        """
        return self._load()

    def get_type(self):
        """
        :return: reference type - file,id,url
        """
        return self._type

    def get_url(self):
        """
        Get reference url.

        :return: reference type - file,id,url
        """
        return self._ref

    def get_file(self):
        """
        Load data into a file and return file path.

        :return: path to file as string
        """
        raise NotImplementedError()


    def _load(self):
        """
        Load test case
        """
        raise NotImplementedError()

    @property
    def url(self):
        return self._ref

    @url.setter
    def url(self, url):
        self._ref = url


class BuildFile(Build):
    """
    Build as a File
    """

    def __init__(self, ref):
        """
        Constructor
        """
        super(BuildFile, self).__init__(ref=ref, type='file')
        sha = sha1_of_file(ref)
        self.sha1 = sha if sha else ""

    def is_exists(self):
        """
        Check if file exists.

        :return: Boolean
        """
        return os.path.isfile(self._ref)

    def get_file(self):
        return self._ref if self.is_exists() else None

    def _load(self):
        """
        Function load.

        :return: file contents
        :raises: NotFoundError if file not found
        """
        if self.is_exists():
            return open(self._ref, "rb").read()
        raise NotFoundError("File %s not found" % self._ref)

class BuildHttp(Build):
    """
    Build as a Http link
    """

    def __init__(self, ref):
        super(BuildHttp, self).__init__(ref=ref, type='http')
        self.auth = ('user', 'pass')
        self.http_verify = False
        self.timeout = None

    def _load(self):
        """
        Function load.
        :return: Response content
        :raises: NotFoundError
        """
        try:
            get = requests.get(self._ref,
                               verify=self.http_verify,
                               auth=self.auth,
                               timeout=self.timeout)
        except requests.exceptions.RequestException as err:
            raise NotFoundError(err)
        return get.content

    def is_exists(self):
        """
        Check if file exists
        :return: Boolean
        """
        try:
            return self._load() is not None
        except NotFoundError:
            return False

    def get_file(self):
        """
        Load data into a file and return file path.

        :return: path to file as string
        """
        content = self._load()
        if not content:
            return None
        filename = "temporary_file.bin"
        with open(filename, "wb") as file_name:
           file_name.write(content)
        return filename


class BuildDatabase(Build):
    """
    Build as a Database ID
    """

    def __init__(self, ref):
        super(BuildDatabase, self).__init__(ref=ref, type='database')

    def _load(self):
        """function load
        returns
        """
        raise NotImplementedError("loading from DB not supported")
