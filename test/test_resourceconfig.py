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
from icetea_lib.ResourceProvider.ResourceConfig import ResourceConfig
from icetea_lib.ResourceProvider.ResourceRequirements import ResourceRequirements

class TestVerify(unittest.TestCase):
    def setUp(self):
        self.rc = ResourceConfig()
        self.testreqs = {
            "requirements": {
                "duts": {
                    "*": {"count": 2, "type": "process"}
                }
            }
        }
        self.testreqsresult = [
            {
                "type": "process",
                "allowed_platforms": [],
                "nick": None,
            },
            {
                "type": "process",
                "allowed_platforms": [],
                "nick": None,
            }
        ]

    def tearDown(self):
        del self.rc

    def test_dut_counts(self):
        self.rc._dut_requirements = [ResourceRequirements({"type": "process"}),
                                     ResourceRequirements({"type": "hardware"})]
        self.rc._resolve_dut_count()
        self.assertEqual(self.rc.count_duts(), 2)
        self.assertEqual(self.rc.count_hardware(), 1)
        self.assertEqual(self.rc.count_process(), 1)

        self.rc._dut_requirements = [ResourceRequirements({"type": "process"}),
                                     ResourceRequirements({"type": "process"}),
                                     ResourceRequirements({"type": "hardware"})]
        self.rc._resolve_dut_count()
        self.assertEqual(self.rc.count_duts(), 3)
        self.assertEqual(self.rc.count_hardware(), 1)
        self.assertEqual(self.rc.count_process(), 2)

        self.rc._dut_requirements = []
        self.rc._resolve_dut_count()
        self.assertEqual(self.rc.count_duts(), 0)
        self.assertEqual(self.rc.count_hardware(), 0)
        self.assertEqual(self.rc.count_process(), 0)

    def test_dut_counts_invalid_fields(self):
        self.rc._dut_requirements = [ResourceRequirements({}),
                                     ResourceRequirements({"type": "process"}),
                                     ResourceRequirements({"type": "hardware"})]
        self.assertRaises(ValueError, self.rc._resolve_dut_count)

    def test_resolve_requirements(self):
        self.rc.resolve_configuration(self.testreqs)
        self.assertEqual(self.rc.get_dut_configuration()[0].get_requirements(),
                         self.testreqsresult[0])
        self.assertEqual(self.rc.get_dut_configuration()[1].get_requirements(),
                         self.testreqsresult[1])

    def test_dut_requirements_single(self):
        self.rc.resolve_configuration(
        {
            "requirements": {
                "duts": {
                    "*": {
                        "count": 1,
                        "nick": None
                    },
                    1: { "nick": "Router{i}"}
                }
            }
        })
        self.assertEqual([self.rc.get_dut_configuration()[0].get_requirements()], [
            {"type": "hardware", "allowed_platforms": [], "nick": "Router1"}
        ])

    def test_dut_requirements_three_duts(self):
        self.rc.resolve_configuration(
            {
                "requirements": {
                    "duts": {
                        "*": {"count": 3,
                              "allowed_platforms": ["K64F"],
                              "application": {"bin": "hex.bin"}
                              },
                        1: {"application": {"bin": "my_hex.bin"}},
                        2: {"application": {"bin": "my_hex2.bin"}}
                }
            }
        })
        self.assertEqual([req.get_requirements() for req in self.rc.get_dut_configuration()],
                         [{"type": "hardware",
                           "allowed_platforms": ["K64F"],
                           "application": {"bin": "my_hex.bin"},
                           "nick": None
                           },
                          {"type": "hardware",
                           "allowed_platforms": ["K64F"],
                           "application": {"bin": "my_hex2.bin"},
                           "nick": None
                           },
                          {"type": "hardware",
                           "allowed_platforms": ["K64F"],
                           "application": {"bin": "hex.bin"},
                           "nick": None
                           }
                          ]
                         )

    def test_dut_requirements_multiple_duts(self):
        self.rc.resolve_configuration(
            {"requirements":
                 {"duts":
                      {"*":
                           {"count": 100,
                            "allowed_platforms": ["K64F"],
                            "application": {"bin": "hex.bin"}
                            },
                       "1..50":
                           {"application": {"bin": "my_hex.bin"},
                            "nick": "DUT{i}"},
                       51: {"application": {"bin": "my_hex2.bin"},
                            "nick": "leader"},
                       "52..100": {"application": {"bin": "my_hex3.bin"}}
                       }
                  }
             }
        )
        self.assertEqual(len(self.rc.get_dut_configuration()), 100)
        self.assertEqual(self.rc.get_dut_configuration()[0].get_requirements(),
                         {"type": "hardware", "allowed_platforms": ["K64F"],
                          "application": {"bin": "my_hex.bin"}, "nick": "DUT1"})
        self.assertEqual(self.rc.get_dut_configuration()[50].get_requirements(),
                         {"type": "hardware", "allowed_platforms": ["K64F"],
                          "application": {"bin": "my_hex2.bin"}, "nick": "leader"})
        self.assertEqual(self.rc.get_dut_configuration()[51].get_requirements(),
                         {"type": "hardware", "allowed_platforms": ["K64F"],
                          "application": {"bin": "my_hex3.bin"}, "nick": None})

    def test_dut_requirements_locations(self):
        self.rc.resolve_configuration(
            {"requirements": {
                "duts": {
                    "*": {"count": 1},
                    1: {"location":
                            [1,
                             "{i}+{n}*{xy}"
                             ]
                        }
                }
            }
        })
        self.assertEqual([req.get_requirements() for req in self.rc.get_dut_configuration()],
                         [{"type": "hardware","allowed_platforms": [],
                           "location": [1, 2], "nick": None}])

    def test_dut_requirements_locations_i(self):
        self.rc.resolve_configuration(
        {
            "requirements": {
                "duts": {
                    "*": {"count": 5},
                    "1..5": {"location": [1, "{i}"]}
                }
            }
        })
        self.assertEqual([req.get_requirements() for req in self.rc.get_dut_configuration()], [
            {"type": "hardware", "allowed_platforms": [],
             "location": [1, 1], "nick": None},
            {"type": "hardware", "allowed_platforms": [],
             "location": [1, 2], "nick": None},
            {"type": "hardware", "allowed_platforms": [],
             "location": [1, 3], "nick": None},
            {"type": "hardware", "allowed_platforms": [],
             "location": [1, 4], "nick": None},
            {"type": "hardware", "allowed_platforms": [],
             "location": [1, 5], "nick": None}
        ])

    def test_dut_requirements_locations_circle(self):
        self.rc.resolve_configuration(
        {
            "requirements": {
                "duts": {
                    "*": {"count": 1},
                    1: {"location": ["10*math.cos((3.5*{i})*({pi}/180))",
                                     "10*math.sin((3.5*{i})*({pi}/180))"]}
                }
            }
        })
        self.assertEqual([req.get_requirements() for req in self.rc.get_dut_configuration()],
                         [{"type": "hardware","allowed_platforms": [],
                           "location": [9.981347984218667, 0.6104853953486088],
                           "nick": None}
        ])

    def test_dut_requirements_invalid_location(self):
        self.rc.resolve_configuration(
        {
            "requirements": {
                "duts": {
                    "*": {"count": 1},
                    1: {"location": ["1+/", "+/"]}
                }
            }
        })

    def test_dut_requirements_invalid_location_length(self):
        self.rc.resolve_configuration(
        {
            "requirements": {
                "duts": {
                    "*": {"count": 1},
                    1: {"location": ["1+1"]}
                }
            }
        })

    def test_dut_requirements_any_indexed_regression(self):
        self.rc.resolve_configuration(
            {
                "requirements": {
                    "duts": {
                        "*": {
                            "count": 2,
                            "allowed_platforms": [],
                            "type": "hardware"
                        },
                        "1": {
                            "allowed_platforms": ["Tplat1"],
                            "custom_key": "value"
                        },
                        "2": {
                            "allowed_platforms": ["Tplat2"],
                            "custom_key2": "value"
                        }
                    }
                }
            }
        )
        reqs = self.rc.get_dut_configuration()
        self.assertDictEqual(reqs[0].get_requirements(), {"allowed_platforms": ["Tplat1"],
                                                          "custom_key": "value",
                                                          "type": "hardware", "nick": None})
        self.assertDictEqual(reqs[1].get_requirements(), {"allowed_platforms": ["Tplat2"],
                                                          "custom_key2": "value",
                                                          "type": "hardware",
                                                          "nick": None})

    def test_setting_dut_parameters(self):
        self.rc.resolve_configuration(self.testreqs)
        conf = self.rc.get_dut_configuration(1)
        conf.set("test", "test")
        self.rc.set_dut_configuration(1, conf)
        res = self.testreqsresult
        res[1]["test"] = "test"
        self.assertEqual([req.get_requirements() for req in self.rc.get_dut_configuration()], res)

    def test_init_with_logger(self):
        logger = mock.Mock()
        testrc = ResourceConfig(logger=logger)
        self.assertEqual(testrc.logger, logger)
