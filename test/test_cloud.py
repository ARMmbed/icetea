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

import unittest
import mock
from mbed_clitest.cloud import Cloud, CloudResult



class CloudTestcase(unittest.TestCase):

    def setUp(self):
        # TODO: Setup stuff, test variables etc.
        self.cloudclient = Cloud(module="test.moduletest")


    def test_module_import(self):
        # Test ImportError with non-existent module
        with self.assertRaises(ImportError):
            cm = Cloud(module="Nonexistentmodule")

        # Verify that Cloud interface init function can import cloud module properly
        cm = Cloud(module="test.moduletest")
        self.assertIsNotNone(cm.client, "Cloud client was None!")

        #Verify correct behaviour with incorrect module
        with self.assertRaises(ImportError):
            cm = Cloud(module="test.moduletest.wrongmodule")


    def test_get_suite(self):
        self.cloudclient.get_suite("test_suite", ["foo", "bar"])
        self.cloudclient.client.get_suite.assert_called_once_with("test_suite",["foo", "bar"])


    def test_get_campaigns(self):
        self.cloudclient.get_campaigns()
        self.assertTrue(self.cloudclient.client.get_campaigns.called)


    def test_get_campaign_id(self):
        self.cloudclient.get_campaign_id("test_campaign")
        self.cloudclient.client.get_campaign_id.assert_called_once_with("test_campaign")
        with self.assertRaises(KeyError):
            self.cloudclient.get_campaign_id("test_campaign")


    def test_get_campaign_names(self):
        self.cloudclient.get_campaign_names()
        self.assertTrue(self.cloudclient.client.get_campaign_names.called)


    def test_updateTestcase(self):
        self.cloudclient.updateTestcase({"test": "meta", "meta": "data"})
        self.cloudclient.client.update_testcase.assert_called_once_with({"test": "meta", "meta": "data"})


    def test_sendResult(self):
        self.cloudclient.sendResult({"verdict": "PASS"})
        self.cloudclient.client.upload_results.assert_called_once_with({"verdict": "PASS"})

        self.assertIsNone(self.cloudclient.sendResult("data"))



    def test_converter(self):
        metadata = {"status": "ready",
                    "name": "tc_name",
                    "title": "this_is_title",
                    "requirements": {
                    },
                    "feature": "unit test",
                    "component": "clitest"
                    }


        self.assertEquals(self.cloudclient._convert_to_db_tc_metadata(metadata),
                          {'status': {'value': 'ready'}, 'requirements': {'node': {'count': 1}},
                           'other_info': {'features': 'unit test', 'components': 'clitest', 'title': 'this_is_title'},
                           'tcid': 'tc_name'})






if __name__ == '__main__':
    unittest.main()
