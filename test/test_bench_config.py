# pylint: disable=missing-docstring,no-self-use,protected-access,invalid-name,too-few-public-methods
# pylint: disable=wrong-import-order
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

import os
import subprocess
import sys
import unittest

from icetea_lib.TestBench.Configurations import Configurations
from icetea_lib.TestStepError import InconclusiveError, TestStepError
from icetea_lib.IceteaManager import ExitCodes

from test.dummy_dut import compile_dummy_dut


class MockArgs(object):
    def __init__(self):
        self.tc_cfg = None
        self.channel = None
        self.type = None
        self.bin = None
        self.platform_name = None


class ConfigMixerTests(unittest.TestCase):

    def test_read_env_config(self):
        cmixer = Configurations()

        with self.assertRaises(InconclusiveError):
            env_cfg = cmixer._read_env_configs("test_config", "test_iface")

        env_cfg = cmixer._read_env_configs(
            os.path.abspath(os.path.join(__file__, "..", "data", "test_env_cfg.json")),
            "test_iface")
        self.assertDictEqual(env_cfg, {"test_config": "test",
                                       "sniffer": {"iface": "test_iface"}})

        with self.assertRaises(InconclusiveError):
            env_cfg = cmixer._read_env_configs(
                os.path.abspath(os.path.join(__file__, "..", "data",
                                             "test_env_cfg_with_duplicates.json")), "test_iface")

    def test_read_exec_config(self):
        cmixer = Configurations()
        args = MockArgs()
        args.tc_cfg = "non_existent_file.json"
        with self.assertRaises(InconclusiveError):
            cmixer._read_exec_configs(args)
        args.tc_cfg = os.path.abspath(os.path.join(__file__, "..", "data", "test_env_cfg.json"))
        args.channel = "1"
        args.type = "type"
        args.bin = "bin"
        args.platform_name = "platform"
        cmixer._read_exec_configs(args)
        self.assertDictContainsSubset(
            {"test_config": "test",
             "requirements": {
                 "duts": {
                     "*": {
                         "type": "type",
                         "application": {
                             "bin": "bin"
                         },
                         "platform_name": "platform"
                     }
                 },
                 "external": {
                     "apps": []
                 }
             }
            },
            cmixer.config
        )

        args.tc_cfg = os.path.abspath(os.path.join(__file__, "..", "data",
                                                   "test_env_cfg_with_duplicates.json"))
        with self.assertRaises(TestStepError):
            cmixer._read_exec_configs(args)

        args.tc_cfg = os.path.abspath(os.path.join(__file__, "..", "data", "test_env_cfg.json"))

        args.platform_name = "not-in-allowed"
        cmixer.config["requirements"]["duts"]["*"]["allowed_platforms"] = ["allowed"]
        with self.assertRaises(TestStepError):
            cmixer._read_exec_configs(args)
        args.platform_name = "allowed"
        cmixer._read_exec_configs(args)
        self.assertDictContainsSubset(
            {"test_config": "test",
             "requirements": {
                 "duts": {
                     "*": {
                         "type": "type",
                         "application": {
                             "bin": "bin"
                         },
                         "allowed_platforms": ["allowed"],
                         "platform_name": "allowed"
                     }
                 },
                 "external": {
                     "apps": []
                 }
             }
            },
            cmixer.config
        )

    @unittest.skipIf(sys.platform == 'win32', "windows does't support process tests")
    def test_config_parse_corner_case_33(self):
        compile_dummy_dut()
        script_file = os.path.abspath(os.path.join(__file__, os.path.pardir, os.path.pardir,
                                                   "icetea.py"))
        tcdir = os.path.abspath(os.path.join(__file__, os.path.pardir))

        retcode = subprocess.call(
            "python " + script_file + " --clean -s "
                                      "--tc test_config_parse_corner_case --failure_return_value "
                                      "--tcdir " + tcdir,
            shell=True)
        self.assertEqual(retcode, ExitCodes.EXIT_SUCCESS)

    def test_parse_config(self):
        basic_config = {
            "name": "my_test",
            "type": "regression",
            "sub_type": None,
            "requirements": {
                "duts": {"*": {
                    "application": {
                        "bin": None
                    }
                }}
            }
        }
        expected = {
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
            "name": "my_test",
            "type": "regression",
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
        retval, int_keys = Configurations._parse_config(**basic_config)
        self.assertDictEqual(retval, expected)
        self.assertFalse(int_keys)

        basic_config = {
            "name": "my_test",
            "type": "regression",
            "sub_type": None,
            "requirements": {
                "duts": {
                    "*": {
                        "application": {
                            "bin": None
                        }
                    },
                    1: {"nick": "intkey"}}
            }
        }
        expected = {
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
            "name": "my_test",
            "type": "regression",
            "sub_type": None,
            "requirements": {
                "duts": {
                    "*": {
                        "application": {
                            "bin": None
                        }
                    },
                    "1": {"nick": "intkey"}},
                "external": {
                    "apps": [
                    ]
                }
            }
        }

        retval, int_keys = Configurations._parse_config(**basic_config)
        self.assertDictEqual(retval, expected)
        self.assertTrue(int_keys)
