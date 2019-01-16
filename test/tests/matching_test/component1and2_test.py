# pylint: disable=missing-docstring,no-self-use

from icetea_lib.bench import Bench
from icetea_lib.TestStepError import TestStepFail


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="ut_2component_test",
                       title="unittest matching",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["icetea_ut", "component1", "component2"],
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 0
                               }
                           }
                       }
                      )

    def case(self):
        raise TestStepFail("This is a failing test case")
