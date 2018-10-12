# pylint: disable=missing-docstring,protected-access

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

import unittest
import mock

from icetea_lib.Result import Result
from icetea_lib.cloud import Cloud, create_result_object


class CloudTestcase(unittest.TestCase):

    def setUp(self):
        with mock.patch("icetea_lib.cloud.get_pkg_version") as mocked_reader:
            mocked_reader.return_value = [mock.MagicMock()]
            self.cloudclient = Cloud(module="moduletest")

    @mock.patch("icetea_lib.cloud.get_pkg_version")
    def test_module_import(self, mocked_version_reader):
        mocked_version_reader.return_value = "1.0.0"
        # Test ImportError with non-existent module
        with self.assertRaises(ImportError):
            cloud_module = Cloud(module="Nonexistentmodule")

        # Verify that Cloud interface init function can import cloud module properly
        cloud_module = Cloud(module="test.moduletest")
        self.assertIsNotNone(cloud_module._client, "Cloud client was None!")

        # Verify correct behaviour with incorrect module
        with self.assertRaises(ImportError):
            cloud_module = Cloud(module="test.moduletest.wrongmodule")

    def test_get_suite(self):
        self.cloudclient.get_suite("test_suite", ["foo", "bar"])
        self.cloudclient._client.get_suite.assert_called_once_with("test_suite", ["foo", "bar"])

    def test_get_campaigns(self):
        self.cloudclient.get_campaigns()
        self.assertTrue(self.cloudclient._client.get_campaigns.called)

    def test_get_campaign_id(self):
        self.cloudclient.get_campaign_id("test_campaign")
        self.cloudclient._client.get_campaign_id.assert_called_once_with("test_campaign")
        with self.assertRaises(KeyError):
            self.cloudclient.get_campaign_id("test_campaign")

    def test_get_campaign_names(self):
        self.cloudclient.get_campaign_names()
        self.assertTrue(self.cloudclient._client.get_campaign_names.called)

    def test_update_testcase(self):
        self.cloudclient.update_testcase({"test": "meta", "meta": "data"})
        self.cloudclient._client.update_testcase.assert_called_once_with({"test": "meta",
                                                                          "meta": "data"})

    def test_send_result(self):
        self.cloudclient.send_result({"verdict": "PASS"})
        self.cloudclient._client.upload_results.assert_called_once_with({"verdict": "PASS"})

        self.assertIsNone(self.cloudclient.send_result("data"))

    def test_converter(self):
        metadata = {"status": "ready",
                    "name": "tc_name",
                    "title": "this_is_title",
                    "requirements": {
                    },
                    "feature": "unit test",
                    "component": "Icetea"
                   }

        self.assertEquals(self.cloudclient._convert_to_db_tc_metadata(metadata),
                          {'status': {'value': 'ready'}, 'requirements': {'node': {'count': 1}},
                           'other_info': {'features': 'unit test', 'components': 'Icetea',
                                          'title': 'this_is_title'},
                           'tcid': 'tc_name'})

    def test_cloudresult_simple(self):
        test_res = {
            "testcase": "tc_name",
            "verdict": "pass",
            "retcode": 0,
            "fw_name": "Icetea",
            "fw_version": "0.10.2"
        }
        result = Result(test_res)
        res = create_result_object(result)
        compare = {
            'exec': {
                'verdict': 'pass',
                'env': {
                    'framework': {
                        'ver': '0.10.2',
                        'name': 'Icetea'
                    }
                },
                'dut': {
                    'sn': 'unknown'
                }
            },
            'tcid': 'tc_name'
        }

        self.assertDictContainsSubset(compare, res)

    def test_cloudresult_full(self):
        test_res = {
            "testcase": "tc_name",
            "verdict": "fail",
            "reason": "ohnou",
            "retcode": 0,
            "duration": 1,
            "fw_name": "Icetea",
            "fw_version": "0.10.2"
        }
        result = Result(test_res)

        class DummyBuild(object):
            @property
            def branch(self):
                return 'master'

            @property
            def commit_id(self):
                return '1234'

            @property
            def build_url(self):
                return 'url'

            @property
            def giturl(self):
                return 'url'

            @property
            def date(self):
                return "22.22.2222"

            @property
            def sha1(self):
                return "asdv"

        class DummyDut(object):
            @property
            def resource_id(self):
                return '123'

            @property
            def platform(self):
                return 'K64F'

            @property
            def build(self):
                return DummyBuild()

        result.set_dutinformation([DummyDut()])
        res = create_result_object(result)
        compare = {
            'exec': {
                'verdict': 'pass',
                'note': 'ohnou',
                'duration': 1,
                'env': {
                    'framework': {
                        'ver': '0.10.2',
                        'name': 'Icetea'
                    }
                },
                'sut': {
                    'commitId': '1234',
                    'buildUrl': 'url',
                    'gitUrl': 'url',
                    'branch': 'master',
                    "buildDate": "22.22.2222",
                    "buildSha1": "asdv"
                },
                'dut': {
                    'sn': '123',
                    'model': 'K64F'
                }
            },
            'tcid': 'tc_name'
        }
        self.assertDictContainsSubset(compare, res)
