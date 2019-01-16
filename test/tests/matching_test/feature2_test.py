# pylint: disable=missing-docstring

from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="ut_feature2_test",
                       title="unittest matching",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       component=["icetea_ut"],
                       feature=["feature2"],
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
