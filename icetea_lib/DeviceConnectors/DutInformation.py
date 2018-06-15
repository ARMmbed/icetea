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

DutInformation module. Contains DutInformation and DutInformationList classes.
These classes are meant to contain information of allocated duts. DutInformationList contains
several helper methods to get some relevant information from it's contents.
"""


#Disable too many arguments warning, too few public methods warning
#pylint: disable=R0913,R0903



class DutInformation(object):
    """
    DutInformation object.
    Contains fields platform (string), index (int), vendor (string), and build (Build)
    """
    def __init__(self, platform, resourceid, index="", vendor="", build=None):
        self.platform = platform
        self.index = index
        self.resource_id = resourceid
        self.vendor = vendor
        self.build = build


class DutInformationList(object):
    """
    DutInformationList object. List of DutInformation objects in member dutinformations as a list.
    helper methods for getting unique dut models in either string or list format and a list of
    resource ID:s.
    """
    def __init__(self, content=None):
        self.dutinformations = content if content else []

    def get(self, index):
        #Disable len(seq) as condition value warning
        #pylint: disable=C1801
        if index > len(self):
            return None
        return self.dutinformations[index]

    def get_uniq_string_dutmodels(self):
        """
        Gets a string of dut models in this TC.

        :return: String of dut models separated with commas.
        String "unknown platform" if no dut information is available
        """
        models = self.get_uniq_list_dutmodels()
        if not models:
            return ""
        return ",".join(models)

    def get_uniq_list_dutmodels(self):
        """
        Gets a list of dut models in this TC
        :return: List of dut models in this TC. Empty list if information is not available.
        """
        models = []
        if self.dutinformations:
            for info in self.dutinformations:
                models.append(info.platform)
            seen = []
            for item in models:
                if item not in seen:
                    seen.append(item)
            return seen
        return models


    def get_resource_ids(self):
        """
        Get resource ids as a list.

        :return: List of resource id:s or "unknown"
        """
        resids = []
        if self.dutinformations:
            for info in self.dutinformations:
                resids.append(info.resource_id)
            return resids
        return "unknown"

    def append(self, dutinfo):
        """
        Append a DutInformation object to the list.

        :param dutinfo: object to append
        :return: Nothing
        """
        self.dutinformations.append(dutinfo)

    def __len__(self):
        """
        overrides len operation for DutInformationList.

        :return: Length of internal dutinformation list as int
        """
        return len(self.dutinformations)
