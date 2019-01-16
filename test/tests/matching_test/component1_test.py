# pylint: disable=missing-docstring

from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="ut_component1_test",
                       title="unittest matching",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["icetea_ut", "component1"],
                       requirements={
                           "duts": {
                               '*': {
                                   "count": 0
                               }
                           }
                       }
                      )

    def case(self):
        pass
