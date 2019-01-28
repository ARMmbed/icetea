#!/usr/bin/env python
# pylint: disable=missing-docstring

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
"""

import logging
import unittest
import mock
import requests

from icetea_lib.build import Build
from icetea_lib.build import NotFoundError


class BuildTestCase(unittest.TestCase):
    """ Basic true asserts to see that testing is executed
    """

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        pass

    def test_build_file(self):

        build = Build.init("file:./test/test_build.py")
        self.assertEqual(build.get_type(), "file")
        self.assertEqual(build.get_url(), "./test/test_build.py")
        self.assertEqual(build.is_exists(), True)
        self.assertTrue(build.get_data().startswith(b'#!/usr/bin/env python'))

        build = Build.init("file:\\test\\build.py")
        self.assertEqual(build.get_type(), "file")
        self.assertEqual(build.get_url(), "\\test\\build.py")

        build = Build.init("file:c:\\file.py")
        self.assertEqual(build.get_type(), "file")
        self.assertEqual(build.get_url(), "c:\\file.py")

        build = Build.init("file:/tmp/file.py")
        self.assertEqual(build.get_type(), "file")
        self.assertEqual(build.get_url(), "/tmp/file.py")
        self.assertEqual(build.is_exists(), False)
        with self.assertRaises(NotFoundError):
            build.get_data()

    @mock.patch("icetea_lib.build.build.requests.get")
    def test_build_http(self, mocked_get):
        mocked_get.return_value = mock.MagicMock()
        type(mocked_get).content = mock.PropertyMock(return_value="\r")
        build = Build.init("http://www.hep.com")
        self.assertEqual(build.get_type(), "http")
        self.assertEqual(build.get_url(), "http://www.hep.com")
        self.assertTrue(build.get_data(), "\r")

    @mock.patch("icetea_lib.build.build.requests.get",
                side_effect=iter([requests.exceptions.SSLError]))
    def test_build_http_error(self, mocked_get):  # pylint: disable=unused-argument
        build = Build.init("https://hep.com")
        self.assertEqual(build.get_type(), "http")
        with self.assertRaises(NotFoundError):
            build.get_data()

    def test_build_uuid(self):
        uuid = "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
        build = Build.init(uuid)
        self.assertEqual(build.get_type(), "database")
        self.assertEqual(build.get_url(), uuid)
        with self.assertRaises(NotImplementedError):
            build.get_data()

    def test_build_id(self):
        uuid = "537eed02ed345b2e039652d2"
        build = Build.init(uuid)
        self.assertEqual(build.get_type(), "database")
        self.assertEqual(build.get_url(), uuid)
        with self.assertRaises(NotImplementedError):
            build.get_data()

    def test_build_unknown_type(self):
        with self.assertRaises(NotImplementedError):
            build = Build.init(",")
        with self.assertRaises(NotImplementedError):
            build = Build(ref="", type="unknown")
            build._load()  # pylint: disable=protected-access
