# pylint: disable=missing-docstring

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

from icetea_lib.DeviceConnectors.DutInformation import DutInformationList, DutInformation


class DutInfoTestcase(unittest.TestCase):

    def setUp(self):
        self.dut1 = DutInformation("plat1", "12345", "1", "vendor")
        self.dut2 = DutInformation("plat1", "23456", "2", "vendor")
        self.dut3 = DutInformation("plat2", "34567", "3", "vendor")
        array_of_duts = [self.dut1, self.dut2, self.dut3]
        self.testlist = DutInformationList(array_of_duts)
        self.emptylist = DutInformationList()

    def test_constuction(self):
        lst = DutInformationList()
        lst.append(self.dut1)
        self.assertEqual(len(lst), 1)

        lst.append(self.dut2)
        lst.append(self.dut3)
        self.assertEqual(len(lst), 3)

    def test_dutmodel_gets(self):
        lst = self.testlist.get_uniq_list_dutmodels()
        self.assertEqual(len(lst), 2)
        self.assertListEqual(lst, ["plat1", "plat2"])
        self.assertEqual(self.testlist.get_uniq_string_dutmodels(), "plat1,plat2")
        self.assertEqual(self.emptylist.get_uniq_string_dutmodels(), "", "Empty list does not "
                                                                         "return correct message.")

    def test_get_resourceids(self):
        self.assertListEqual(self.testlist.get_resource_ids(), ['12345', '23456', '34567'])

    def test_cache(self):
        # pylint: disable=W0212
        DutInformationList._cache = dict()
        self.assertDictEqual(DutInformationList._cache, dict())

        DutInformationList.push_resource_cache("test", {"a": "1"})
        self.assertDictEqual(DutInformationList._cache, {"test": {"a": "1"}})

        DutInformationList.get_resource_cache("test")["b"] = "2"
        self.assertDictEqual(DutInformationList._cache, {"test": {"a": "1", "b": "2"}})

        DutInformationList.push_resource_cache("test", {"a": "2"})
        self.assertDictEqual(DutInformationList._cache, {"test": {"a": "2", "b": "2"}})

        DutInformationList._cache = dict()
        self.assertDictEqual(DutInformationList._cache, dict())

    def test_build_sha(self):
        # pylint: disable=W0212
        DutInformationList._cache = dict()
        info = DutInformation("plat1", "12345", "1", "vendor")
        self.assertEqual(info.build_binary_sha1, None)
        info.build_binary_sha1 = "123"
        self.assertEqual(info.build_binary_sha1, "123")
        DutInformationList._cache = dict()



if __name__ == '__main__':
    unittest.main()
