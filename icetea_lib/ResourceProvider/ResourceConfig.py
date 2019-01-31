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

ResourceConfig module. This module contains code related to parsing and handling resource
configurations for test cases.
"""

import copy
import math
import re
from six import string_types
from icetea_lib import LogManager
from icetea_lib.ResourceProvider.ResourceRequirements import ResourceRequirements


class ResourceConfig(object):  # pylint: disable=too-many-instance-attributes
    """
    Object used to describe and manipulate the resource configuration used by a testcase.
    """
    def __init__(self, json_configuration=None, logger=None):
        self.json_config = json_configuration
        self._dut_requirements = []
        self.logger = logger
        self._sim_config = None
        if self.logger is None:
            self.logger = LogManager.get_dummy_logger()
        self._counts = {"total": 0, "hardware": 0, "process": 0, "serial": 0, "mbed": 0}

    @property
    def _hardware_count(self):
        """
        Amount of hardware resources.

        :return: integer
        """
        return self._counts.get("hardware") + self._counts.get("serial") + self._counts.get("mbed")

    @_hardware_count.setter
    def _hardware_count(self, value):
        self._counts["hardware"] = value

    @property
    def _process_count(self):
        """
        Amount of process resources.

        :return: integer
        """
        return self._counts.get("process")

    @_process_count.setter
    def _process_count(self, value):
        self._counts["process"] = value

    @property
    def _dut_count(self):
        """
        Total amount of resources.

        :return: integer
        """
        return self._counts.get("total")

    @_dut_count.setter
    def _dut_count(self, value):
        self._counts["total"] = value

    def resolve_configuration(self, configuration):
        """
        Resolve requirements from given JSON encoded data.
        The JSON should follow the testcase meta-data requirements field format. This function
        will resolve requirements for each individual DUT and create a DUT requirements list
        that contains the configuration for each DUT, eg:
        {
            "duts": [
                { "*": {"count": 2, "type": "process" } }
            ]
        }
        would result in the following configuration:
        [
            { "1": {"type": "process", "allowed_platforms": [], "nick": None }
            { "2": {"type": "process", "allowed_platforms": [], "nick": None }
        ]

        :param requirements: optional argument if requirements come from external source,
        should be similar to the following format:
        {
            "duts": [
                { "*": {"count": 2, "type": "process" } }
            ]
        }

        """
        configuration = configuration if configuration else self.json_config
        self._resolve_requirements(configuration["requirements"])
        self._resolve_dut_count()

    def _resolve_requirements(self, requirements):
        """
        Internal method for resolving requirements into resource configurations.

        :param requirements: Resource requirements from test case configuration as dictionary.
        :return: Empty list if dut_count cannot be resolved, or nothing
        """
        try:
            dut_count = requirements["duts"]["*"]["count"]
        except KeyError:
            return []

        default_values = {
            "type": "hardware",
            "allowed_platforms": [],
            "nick": None,
        }

        default_values.update(requirements["duts"]["*"])
        del default_values["count"]
        dut_keys = list(default_values.keys())
        dut_keys.extend(["application", "location", "subtype"])

        dut_requirements = self.__generate_indexed_requirements(dut_count,
                                                                default_values,
                                                                requirements)

        # Match groups of duts defined with 1..40 notation.
        for key in requirements["duts"].keys():
            if not isinstance(key, string_types):
                continue
            match = re.search(r'([\d]{1,})\.\.([\d]{1,})', key)
            if match:
                first_dut_idx = int(match.group(1))
                last_dut_idx = int(match.group(2))
                for i in range(first_dut_idx, last_dut_idx+1):
                    for k in dut_keys:
                        if k in requirements["duts"][key]:
                            dut_requirements[i-1].set(k, copy.copy(requirements["duts"][key][k]))

        for idx, req in enumerate(dut_requirements):

            if isinstance(req.get("nick"), string_types):
                nick = req.get("nick")
                req.set("nick", ResourceConfig.__replace_base_variables(nick,
                                                                        len(dut_requirements),
                                                                        idx))
            self._solve_location(req, len(dut_requirements), idx)
        self._dut_requirements = dut_requirements
        return None

    def _solve_location(self, req, dut_req_len, idx):
        """
        Helper function for resolving the location for a resource.

        :param req: Requirements dictionary
        :param dut_req_len: Amount of required resources
        :param idx: index, integer
        :return: Nothing, modifies req object
        """
        if not req.get("location"):
            return
        if len(req.get("location")) == 2:
            for x_and_y, coord in enumerate(req.get("location")):

                if isinstance(coord, string_types):
                    coord = ResourceConfig.__replace_coord_variables(coord,
                                                                     x_and_y,
                                                                     dut_req_len,
                                                                     idx)
                    try:
                        loc = req.get("location")
                        loc[x_and_y] = eval(coord)  # pylint: disable=eval-used
                        req.set("location", loc)
                    except SyntaxError as error:
                        self.logger.error(error)
                        loc = req.get("location")
                        loc[x_and_y] = 0.0
                        req.set("location", loc)
        else:
            self.logger.error("invalid location field!")
            req.set("location", [0.0, 0.0])

    @staticmethod
    def __replace_base_variables(text, req_len, idx):
        """
        Replace i and n in text with index+1 and req_len.

        :param text: base text to modify
        :param req_len: amount of required resources
        :param idx: index of resource we are working on
        :return: modified string
        """
        return text \
            .replace("{i}", str(idx + 1)) \
            .replace("{n}", str(req_len))

    @staticmethod
    def __replace_coord_variables(text, x_and_y, req_len, idx):
        """
        Replace x and y with their coordinates and replace pi with value of pi.

        :param text: text: base text to modify
        :param x_and_y: location x and y
        :param req_len: amount of required resources
        :param idx: index of resource we are working on
        :return: str
        """
        return ResourceConfig.__replace_base_variables(text, req_len, idx) \
            .replace("{xy}", str(x_and_y)) \
            .replace("{pi}", str(math.pi))

    @staticmethod
    def __generate_indexed_requirements(dut_count, basekeys, requirements):
        """
        Generate indexed requirements from general requirements.

        :param dut_count: Amount of duts
        :param basekeys: base keys as dict
        :param requirements: requirements
        :return: Indexed requirements as dict.
        """
        dut_requirements = []
        for i in range(1, dut_count + 1):
            dut_requirement = ResourceRequirements(basekeys.copy())
            if i in requirements["duts"]:
                for k in requirements["duts"][i]:
                    dut_requirement.set(k, requirements["duts"][i][k])
            elif str(i) in requirements["duts"]:
                i = str(i)
                for k in requirements["duts"][i]:
                    dut_requirement.set(k, requirements["duts"][i][k])
            dut_requirements.append(dut_requirement)
        return dut_requirements

    def count_hardware(self):
        """
        :return: Hardware resource count
        """
        return self._hardware_count

    def get_dut_range(self, i=0):
        """
        get range of length dut_count with offset i.
        :param i: Offset
        :return: range
        """
        return range(1 + i, self.count_duts() + i + 1)

    def _resolve_hardware_count(self):
        """
        Calculate amount of hardware resources.

        :return: Nothing, adds results to self._hardware_count
        """
        length = len([d for d in self._dut_requirements if d.get("type") in ["hardware",
                                                                             "serial", "mbed"]])
        self._hardware_count = length

    def count_process(self):
        """
        :return: Process resource count
        """
        return self._process_count

    def _resolve_process_count(self):
        """
        Calculate amount of process resources.

        :return: Nothing, adds results to self._process_count
        """
        length = len([d for d in self._dut_requirements if d.get("type") == "process"])
        self._process_count = length

    def count_duts(self):
        """
        :return: Total amount of resources
        """
        return self._dut_count

    def _resolve_dut_count(self):
        """
        Calculates total amount of resources required and their types.

        :return: Nothing, modifies _dut_count, _hardware_count and
        _process_count
        :raises: ValueError if total count does not match counts of types separately.
        """
        self._dut_count = len(self._dut_requirements)
        self._resolve_process_count()
        self._resolve_hardware_count()
        if self._dut_count != self._hardware_count + self._process_count:
            raise ValueError("Missing or invalid type fields in dut configuration!")

    def get_dut_configuration(self, ident=None):
        """
        Getter for dut configuration for dut ident.

        :param ident: Identification for dut. If set to None, all requirements are returned.
        :return: Requirements dictionary for dut ident if ident is not None,
        else dictionary with all requirements.
        """
        return self._dut_requirements if ident is None else self._dut_requirements[ident]

    def set_dut_configuration(self, ident, config):
        """
        Set requirements for dut ident.

        :param ident: Identity of dut.
        :param config: If ResourceRequirements object, add object as requirements for resource
        ident. If dictionary, create new ResourceRequirements object from dictionary.
        :return: Nothing
        """
        if hasattr(config, "get_requirements"):
            self._dut_requirements[ident] = config
        elif isinstance(config, dict):
            self._dut_requirements[ident] = ResourceRequirements(config)
