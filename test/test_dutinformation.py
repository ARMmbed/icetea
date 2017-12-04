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

from icedtea_lib.DeviceConnectors.DutInformation import DutInformationList, DutInformation


class DutInfoTestcase(unittest.TestCase):

    def setUp(self):
        self.d1 = DutInformation("plat1", "12345", "1", "vendor")
        self.d2 = DutInformation("plat1", "23456", "2", "vendor")
        self.d3 = DutInformation("plat2", "34567", "3", "vendor")
        ar = [self.d1, self.d2, self.d3]
        self.testlist = DutInformationList(ar)
        self.emptylist = DutInformationList()

    def test_constuction(self):
        lst = DutInformationList()
        lst.append(self.d1)
        self.assertEqual(len(lst), 1)

        lst.append(self.d2)
        lst.append(self.d3)
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


if __name__ == '__main__':
    unittest.main()
