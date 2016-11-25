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

import copy
import math
import re
from mbed_test import LogManager

class ResourceConfig(object):
    """
    Object used to describe and manipulate the resource configuration used by a testcase.
    """
    def __init__(self, json_configuration=None, logger=None):
        self.json_config = json_configuration
        self._dut_requirements = []
        self.logger = logger
        if self.logger is None:
            self.logger = LogManager.get_dummy_logger()
        self._dut_count = 0
        self._process_count = 0
        self._hardware_count = 0

    def resolve_configuration(self, configuration):
        """
        Resolve requirements from given JSON encoded data. The JSON should follow the testcase meta-data requirements
        field format. This function will resolve requirements for each individual DUT and create a DUT requirements list
        that contains the configuration for each DUT, eg:
        {
            "duts": [
                { "*": {"count": 2, "type": "hardware" } }
            ]
        }
        would result in the following configuration:
        [
            { "1": {"type": "hardware", "allowed_platforms": [], "nick": None }
            { "2": {"type": "hardware", "allowed_platforms": [], "nick": None }
        ]

        :param requirements: optional argument if requirements come from external source, should be similar to the
        following format:
        {
            "duts": [
                { "*": {"count": 2, "type": "hardware } }
            ]
        }

        """
        configuration = configuration if configuration else self.json_config
        self._resolve_requirements(configuration["requirements"])

        self._resolve_dut_count()

    def _resolve_requirements(self, requirements):
        try:
            dut_count = requirements["duts"]["*"]["count"]
        except:
            return []

        defaultValues = {
            "type": "hardware",
            "allowed_platforms": [],
            "nick": None
        }
        dut_requirements = []

        defaultValues.update( requirements["duts"]["*"] )
        del defaultValues["count"]
        dut_keys = defaultValues.keys()
        dut_keys.extend(["application", "rf_channel", "location", "subtype"])

        for i in range(1,dut_count+1):
            dut_requirement = defaultValues.copy()
            if i in requirements["duts"]:
                for k in dut_keys:
                    if k in requirements["duts"][i]:
                        dut_requirement[k] = requirements["duts"][i][k]
            elif str(i) in requirements["duts"]:
                i = str(i)
                for k in dut_keys:
                    if k in requirements["duts"][i]:
                        dut_requirement[k] = requirements["duts"][i][k]
            dut_requirements.append(dut_requirement)

        for key in requirements["duts"].keys():
            if not isinstance(key, basestring):
                continue
            match = re.search('([\d]{1,})\.\.([\d]{1,})', key)
            if match:
                firstDutIdx = int(match.group(1))
                lastDutIdx = int(match.group(2))
                for i in range(firstDutIdx, lastDutIdx+1):
                    for k in dut_keys:
                        if k in requirements["duts"][key]:
                            dut_requirements[i-1][k] = copy.copy( requirements["duts"][key][k] )

        for idx, req in enumerate(dut_requirements):

            def replaceBaseVariables(text):
                return text\
                    .replace("{i}", str(idx+1))\
                    .replace("{n}", str(len(dut_requirements)))

            if isinstance(req["nick"], basestring):
                nick = req["nick"]
                req["nick"] = replaceBaseVariables(nick)
            if "location" in req:
                if len(req["location"]) == 2:
                    for xy, coord in enumerate(req["location"]):
                        def replaceCoordVariables(text):
                            return replaceBaseVariables(text)\
                                .replace("{xy}", str(xy))\
                                .replace("{pi}", str(math.pi))

                        if isinstance(coord, basestring):
                            coord = replaceCoordVariables(coord)
                            try:
                                req["location"][xy] = eval(coord)
                            except SyntaxError as e:
                                self.logger.error(e)
                                req["location"][xy] = 0.0
                else:
                    self.logger.error("invalid location field!")
                    req["location"] = [0.0, 0.0]

        self._dut_requirements = dut_requirements

    def count_hardware(self):
        return self._hardware_count

    def _resolve_hardware_count(self):
        try:
            l = len([d for d in self._dut_requirements if d["type"] == "hardware"])
        except KeyError:
            raise ValueError("Invalid DUT configuration, missing type field!")
        self._hardware_count = l


    def count_process(self):
        return self._process_count

    def _resolve_process_count(self):
        try:
            l = len([d for d in self._dut_requirements if d["type"] == "process"])
        except KeyError:
            raise ValueError("Invalid DUT configuration, missing type field!")
        self._process_count = l

    def count_duts(self):
        return self._dut_count

    def _resolve_dut_count(self):
        self._dut_count = len(self._dut_requirements)
        self._resolve_process_count()
        self._resolve_hardware_count()

    def get_dut_configuration(self, id=None):
        return self._dut_requirements if id is None else self._dut_requirements[id]

    def set_dut_configuration(self, id, config):
        self._dut_requirements[id] = config
