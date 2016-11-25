from mbed_clitest.bench import Bench, TestStepFail
from mbed_clitest.tools import test_case

"""
    Example testcase file that implements multiple cases that share a setUp and tearDown function.
"""
class MultipleTestcase(Bench):
    def __init__(self, **kwargs):
        tc_args = {
            'title': "dummy",
            'status': "unknown",
            'type': "functional",
            'purpose': "dummy",
            'requirements': {
                "duts": {
                    '*': { #requirements for all nodes
                        "count":0,
                    }
                }
            }
        }
        tc_args.update(kwargs)
        Bench.__init__(self, **tc_args)

    def setUp(self):
        pass

    def tearDown(self):
        pass


@test_case(MultipleTestcase, name="passing_case")
def passcase(test_env):
    pass

@test_case(MultipleTestcase, name="fail_case")
def fail_case(test_env):
    raise TestStepFail("This must fail!")