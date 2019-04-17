# pylint: disable=no-member,too-many-public-methods
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

Configuration handling helpers.
"""


import os
import json
from six import string_types
from pydash import get
from jsonmerge import merge

import icetea_lib.LogManager as LogManager
from icetea_lib.TestStepError import TestStepError
from icetea_lib.TestStepError import InconclusiveError
from icetea_lib.tools.tools import find_duplicate_keys


class Configurations(object):
    """
    Configurations manage test and environment configurations.
    Provide public API's to read configuration values.
    """
    def __init__(self, args=None, logger=None, **kwargs):
        super(Configurations, self).__init__()
        self._config, self._integer_keys_found = self._parse_config(**kwargs)
        self._env_cfg = None
        self._logger = logger if logger else LogManager.get_dummy_logger()
        self._args = args

    def init(self, logger):
        """
        When test starts Bench will call _init() -function to initialize
        configurations and read execution configuration file if exists.
        :param args: arguments
        """
        self._logger = logger
        if self._integer_keys_found:
            self._logger.warning("Integer keys found in configuration for DUT requirements. "
                                 "Keys forced to strings for this run. "
                                 "Please update your DUT requirements keys to strings.")
        # Read cli given environment configuration file
        self._env_cfg = self._read_env_configs(self._args.env_cfg, self._args.iface)
        # Read cli given TC configuration file and merge it
        self._read_exec_configs(self._args)

    @property
    def test_name(self):
        """
        Get test bench name
        :return: string
        """
        # Return unknown also when name is set as None
        return "unknown" if self._config.get("name",
                                             "unknown") is None else self._config.get("name",
                                                                                      "unknown")

    @property
    def name(self):
        """
        Get test bench name
        :return: string
        """
        return self.test_name

    @property
    def config(self):
        """
        Getter for the internal config dict.

        :return: dict
        """
        return self._config

    @config.setter
    def config(self, value):
        self.set_config(value)

    @property
    def env(self):
        """
        Getter for env configuration

        :return: dict
        """
        return self._env_cfg

    def is_hardware_in_use(self):
        """
        :return: True if type is hardware
        """
        return get(self.config, "requirements.duts.*.type") == "hardware"

    def get_test_component(self):
        """
        Get test component.

        :return: string
        """
        return self.config.get("component", [''])

    def get_features_under_test(self):
        """
        Get features tested by this test case.

        :return: list
        """
        fea = self.config.get("feature", [])
        if isinstance(fea, str):
            return [fea]
        return fea

    def get_allowed_platforms(self):
        """
        Return list of allowed platfroms from requirements.

        :return: list
        """
        return get(self.config, "requirements.duts.*.allowed_platforms", list())

    # @todo find better place for these
    def status(self):
        """
        Get TC implementation status.

        :return: string or None
        """
        return self.config.get('status')

    def type(self):
        """
        Get test case type.

        :return: string or None
        """
        return self.config.get('type')

    def subtype(self):
        """
        Get test case subtype.

        :return: string or None
        """
        return self.config.get('subtype')

    def get_config(self):
        """
        Get test case configuration.

        :return: dict
        """
        return self.config

    def skip(self):
        """
        Get skip value.

        :return: Boolean or None
        """
        return get(self.config, "execution.skip.value")

    def skip_info(self):
        """
        Get the entire skip dictionary.

        :return: dictionary or None
        """
        return get(self.config, "execution.skip")

    # Get Skip Reason
    def skip_reason(self):
        """
        Get skip reason.

        :return: string
        """
        return get(self.config, "execution.skip.reason", "")

    def check_skip(self):
        """
        Check if tc should be skipped

        :return: Boolean
        """
        if not self.skip():
            return False

        info = self.skip_info()
        only_type = info.get('only_type')
        platforms = info.get('platforms', [])

        allowed = get(self.config, "requirements.duts.*.allowed_platforms", list())
        # validate platforms in allowed_platforms, otherwise no skip
        if allowed and platforms and not set(platforms).issubset(allowed):
            return False

        # skip tests by either only_type or platforms
        if only_type or platforms:
            for keys in get(self.config, "requirements.duts", dict()):
                # skip tests by only_type
                type_expr = "type" in self.config["requirements"]["duts"][keys] and \
                            self.config['requirements']['duts'][keys]["type"] == only_type
                if only_type and type_expr:
                    return True

                # skip test by platforms condition 1:
                plat_expr = "platform_name" in self.config['requirements']['duts'][keys] and \
                            self.config['requirements']['duts'][keys]["platform_name"] in platforms
                if platforms and plat_expr:
                    return True

        # no skip if neither only_type nor platforms is defined
        return False

    def get_tc_abspath(self, tc_file=None):
        """
        Get path to test case.

        :param tc_file: name of the file. If None, tcdir used instead.
        :return: absolute path.
        """
        if not tc_file:
            return os.path.abspath(self._args.tcdir)
        return os.path.abspath(tc_file)

    def set_config(self, config):
        """
        Set the configuration for this test case.

        :param config: dictionary
        :return: Nothing
        """
        self._config = config

    # Read Environment Configuration JSON file
    def _read_env_configs(self, env_cfg, iface):  # pylint: disable=no-self-use
        """
        Read environment configuration json file.

        :return: False if read fails, True otherwise.
        """
        data = None

        if env_cfg != '':
            env_cfg_filename = env_cfg
        else:
            env_cfg_filename = os.path.abspath(os.path.join(__file__,
                                                            os.path.pardir,
                                                            os.path.pardir,
                                                            os.path.pardir,
                                                            "env_cfg_json"))
        if os.path.exists(env_cfg_filename):
            with open(env_cfg_filename) as data_file:
                try:
                    data = json.load(data_file, object_pairs_hook=find_duplicate_keys)
                except ValueError as error:
                    self._logger.error(error)
                    raise InconclusiveError("Environment file {} read failed: {}".format(
                        env_cfg_filename, error))
        elif env_cfg != '':
            raise InconclusiveError('Environment file {} does not exist'.format(env_cfg))

        env = merge({}, data) if data else {}

        if iface:
            env = merge(env, {'sniffer': {'iface': iface}})
        else:
            env = merge(env, {'sniffer': {'iface': "Sniffer"}})
        return env

    # Read Execution Configuration file
    def _read_exec_configs(self, args):  # pylint: disable=too-many-branches
        """
        Read execution configuration file.

        :return: Nothing.
        :raises TestStepError if file cannot be read or merged into config, or if platform_name
        is not in allowed_platforms.
        """
        tc_cfg = None
        if args.tc_cfg:
            tc_cfg = args.tc_cfg
        # TODO: this bit is not compatible with IceteaManagement's --tc argument.
        elif isinstance(args.tc, string_types) and os.path.exists(args.tc + '.json'):
            tc_cfg = args.tc + '.json'
        if tc_cfg:
            if not os.path.exists(tc_cfg):
                self._logger.error("Execution configuration file {} does not exist.".format(tc_cfg))
                raise InconclusiveError(
                    "Execution configuration file {} does not exist.".format(tc_cfg))
            with open(tc_cfg) as data_file:
                try:
                    data = json.load(data_file, object_pairs_hook=find_duplicate_keys)
                    self._config = merge(self._config, data)
                except Exception as error:
                    self._logger.error("Testcase configuration read from file (%s) failed!", tc_cfg)
                    self._logger.error(error)
                    raise TestStepError("TC CFG read fail! {}".format(error))

        if args.type:
            self._config["requirements"]["duts"]["*"] = merge(
                self._config["requirements"]["duts"]["*"],
                {"type": args.type})

        if args.bin:
            self._config["requirements"]["duts"]["*"] = merge(
                self._config["requirements"]["duts"]["*"],
                {"application": {'bin': args.bin}})

        if args.platform_name:
            allowed = self._config["requirements"]["duts"]["*"].get("allowed_platforms")
            if allowed:
                if args.platform_name in allowed:
                    self._config["requirements"]["duts"]["*"][
                        "platform_name"] = args.platform_name
                else:
                    raise TestStepError("Required platform_name not in allowed_platforms.")
            else:
                self._config["requirements"]["duts"]["*"][
                    "platform_name"] = args.platform_name

    @staticmethod
    def _parse_config(**kwargs):
        """
        Internal helper for parsing configurations.

        :param kwargs: dict
        :return: dict
        """
        config = {
            "compatible": {
                "framework": {
                    "name": "Icetea",
                    "version": ">=1.0.0"
                },
                "automation": {
                    "value": True
                },
                "hw": {
                    "value": True
                }
            },
            "name": None,
            "type": None,
            "sub_type": None,
            "requirements": {
                "duts": {"*": {
                    "application": {
                        "bin": None
                    }
                }},
                "external": {
                    "apps": [
                    ]
                }
            }
        }
        integer_keys_found = False
        try:
            reqs = kwargs["requirements"]["duts"]
            if len(reqs) > 1:
                integer_keys_found = False
                new_keys = {}
                int_keys = []
                for key in reqs:
                    if isinstance(key, int):
                        integer_keys_found = True
                        int_keys.append(key)
                        val = reqs[key]
                        new_keys[str(key)] = val
                for key in new_keys:
                    reqs[key] = new_keys[key]
                for key in int_keys:
                    reqs.pop(key)

        except KeyError:
            pass

        for key in kwargs:
            if isinstance(kwargs[key], dict) and key in config:
                config[key] = merge(config[key], kwargs[key])
            else:
                config[key] = kwargs[key]

        return config, integer_keys_found
