# pylint: disable=missing-docstring,attribute-defined-outside-init

import os

from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_config_parse_corner_case",
                       title="Regression test for a corner case in config parsing",
                       status="released",
                       purpose="Regression test",
                       component=["configuration"],
                       type="regression",
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 33,
                                   "type": "process",
                                   "application": {"bin": os.path.abspath(
                                       os.path.join(__file__,
                                                    os.path.pardir,
                                                    os.path.pardir,
                                                    "dut", "dummyDut"))}
                               },
                               1: {"nick": "nick1", "location": [0.0, 0.0]},
                               2: {"nick": "nick2", "location": [10.0, 0.0]},
                               "3..32": {"nick": "nick_{i}", "location": [20.0, 0.0]},
                               33: {"nick": "nick33", "location": [50.0, 50.0]},

                           }
                       }
                      )

    def setup(self):
        pass

    def case(self):
        pass

    def teardown(self):
        pass
