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

from icetea_lib.ResourceProvider.ResourceRequirements import ResourceRequirements


class ResourceRequirementTestcase(unittest.TestCase):

    def setUp(self):
        self.simple_testreqs = {
            "type": "process",
            "allowed_platforms": [],
            "expires": 2000,
            "nick": None,
            "tags": {"test": True}
        }
        self.simple_testreqs2 = {
            "type": "process",
            "allowed_platforms": ["DEV3"],
            "nick": None,
        }
        self.recursion_testreqs = {
            "type": "process",
            "allowed_platforms": ["DEV3"],
            "application": {"bin": "test_binary"},
            "nick": None,
        }

        self.actual_descriptor1 = {"platform_name": "DEV2", "resource_type": "mbed"}
        self.actual_descriptor2 = {"platform_name": "DEV1", "resource_type": "process"}
        self.actual_descriptor3 = {"platform_name": "DEV3", "resource_type": "process"}
        self.actual_descriptor4 = {"resource_type": "process", "bin": "test_binary"}

    def test_get(self):
        dutreq = ResourceRequirements(self.simple_testreqs)
        self.assertEqual(dutreq.get("type"), "process")

        dutreq = ResourceRequirements(self.recursion_testreqs)
        self.assertEqual(dutreq.get("application.bin"), "test_binary")
        self.assertIsNone(dutreq.get("application.bin.not_exist"))

    def test_set(self):
        dutreq = ResourceRequirements(self.simple_testreqs)
        dutreq.set("test_key", "test_val")
        self.assertEqual(dutreq._requirements["test_key"], "test_val")
        # Test override
        dutreq.set("test_key", "test_val2")
        self.assertEqual(dutreq._requirements["test_key"], "test_val2")

        # test tags merging. Also a test for set_tag(tags=stuff)
        dutreq.set("tags", {"test": False, "test2": True})
        self.assertEqual(dutreq._requirements["tags"], {"test": False, "test2": True})
        dutreq.set("tags", {"test2": False})
        self.assertEqual(dutreq._requirements["tags"], {"test": False, "test2": False})

    def test_set_tags(self):
        dutreq = ResourceRequirements(self.simple_testreqs)
        dutreq._set_tag(tag="test", value=False)
        dutreq._set_tag(tag="test2", value=True)
        self.assertDictEqual(dutreq._requirements["tags"], {"test": False, "test2": True})

    def test_empty_tags(self):
        dutreq = ResourceRequirements(self.simple_testreqs)
        dutreq._set_tag("test", value=None)
        dutreq.remove_empty_tags()
        self.assertEqual(dutreq._requirements["tags"], {})
        self.assertEqual(dutreq.remove_empty_tags(tags={"test1": True, "test2": None}),
                         {"test1": True})


if __name__ == '__main__':
    unittest.main()
