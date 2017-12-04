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

# LISTING TESTS IN THIS FILE
#
# $ python icedtea.py --tcdir examples/multiple_test_cases_by_file_example --list
# TCs:
# +-------+------------------------------+---------+------------+---------+-------+-----------+
# | Index |             Name             |  Status |    Type    | Subtype | Group | Component |
# +-------+------------------------------+---------+------------+---------+-------+-----------+
# | 1     | multipleTests_SecondTestCase | unknown | functional |         |       |  ['None'] |
# | 2     | multipleTests_FirstTestCase  | unknown | functional |         |       |  ['None'] |
# +-------+------------------------------+---------+------------+---------+-------+-----------+
#
#
# EXECUTION OF TESTS IN THIS FILE
#
# $ python icedtea.py --tcdir examples/multiple_test_cases_by_file_example --tc all
# START TEST CASE EXECUTION: 'multipleTests_SecondTestCase'
# 09:29:10.770|TC     MainThread: Start Test case 'multipleTests_SecondTestCase'
# 09:29:10.770|TC     MainThread: ====setUpTestBench====
# 09:29:10.770|TC     MainThread: ------TC SET UP---------
# 09:29:10.770|TC     MainThread: MultipleTestsCaseExampleTestEnv.setup
# 09:29:10.770|TC     MainThread: ------TC START---------
# 09:29:10.770|TC     MainThread: not implemented
# Traceback (most recent call last):
#   File "C:\Work\me\tests\icedtea\icedtea_lib\bench.py", line 1154, in run
#     self.case()
#   File "C:\Work\me\tests\icedtea\examples\multiple_test_cases_by_file_example\multiple_tests_cases.py", line 109, in multipleTests_SecondTestCase
#     raise TestStepError( "not implemented" )
# TestStepError: not implemented
# 09:29:10.780|TC     MainThread: Test Case fails because of: not implemented
# 09:29:10.780|TC     MainThread: Exception details:
# 09:29:10.780|TC     MainThread: TC Name: C:\Work\me\tests\icedtea\icedtea_lib\bench.py
# 09:29:10.780|TC     MainThread: Line number: 1154
# 09:29:10.780|TC     MainThread: Line: self.case()
# 09:29:10.780|TC     MainThread: ------TC END-----------
# 09:29:10.780|TC     MainThread: ====TC TEAR DOWN====
# 09:29:10.780|TC     MainThread: MultipleTestsCaseExampleTestEnv.teardown
# 09:29:10.780|TC     MainThread: ====tearDownTestBench====
# 09:29:10.780|TC     MainThread: Test 'multipleTests_SecondTestCase' FAIL, reason: not implemented

# START TEST CASE EXECUTION: 'multipleTests_FirstTestCase'

# 09:29:10.790|TC     MainThread: Start Test case 'multipleTests_FirstTestCase'
# 09:29:10.790|TC     MainThread: ====setUpTestBench====
# 09:29:10.790|TC     MainThread: ------TC SET UP---------
# 09:29:10.790|TC     MainThread: MultipleTestsCaseExampleTestEnv.setup
# 09:29:10.790|TC     MainThread: ------TC START---------
# 09:29:10.790|TC     MainThread: ------TC END-----------
# 09:29:10.790|TC     MainThread: ====TC TEAR DOWN====
# 09:29:10.790|TC     MainThread: MultipleTestsCaseExampleTestEnv.teardown
# 09:29:10.790|TC     MainThread: ====tearDownTestBench====
# 09:29:10.790|TC     MainThread: Test 'multipleTests_FirstTestCase' PASS
# +------------------------------+---------+-----------------+-------------+----------+
# | Testcase                     | Verdict |   Fail Reason   | Skip Reason | duration |
# +------------------------------+---------+-----------------+-------------+----------+
# | multipleTests_SecondTestCase |   fail  | not implemented |             |   0.01   |
# | multipleTests_FirstTestCase  |   pass  |                 |             |   0.01   |
# +------------------------------+---------+-----------------+-------------+----------+
# +---------------+----------------+
# |    Summary    |                |
# +---------------+----------------+
# | Final Verdict |      FAIL      |
# |     count     |       2        |
# |      pass     |       1        |
# |      fail     |       1        |
# |    Duration   | 0:00:00.020000 |
# +---------------+----------------+


from icedtea_lib.bench import Bench
from icedtea_lib.bench import TestStepError
from icedtea_lib.tools.tools import test_case


# Test environment which will be shared by all tests cases in this file
# The environment is initialized by same setUp and terminate by tearDown
class MultipleTestsCaseExampleTestEnv(Bench):
    def __init__(self, **kwargs):
        testcase_args = {
            'title': "dummy",
            'status': "unknown",
            'type': "functional",
            'purpose': "dummy",
            'requirements': {
                "duts": {
                    '*': {
                        "count": 0,
                    }
                }
            }
        }

        testcase_args.update(kwargs)
        Bench.__init__(self, **testcase_args)

    def setup(self):
        self.logger.info("MultipleTestsCaseExampleTestEnv.setup")
        # setup code
        pass

    def teardown(self):
        # teardown code
        self.logger.info("MultipleTestsCaseExampleTestEnv.teardown")
        pass


# This test will by listed by the name "multipleTests_FirstTestCase"
@test_case(MultipleTestsCaseExampleTestEnv, name="multipleTests_FirstTestCase")
def aTest(test_env):
    pass


# This test will by listed by the name "multipleTests_SecondTestCase"
@test_case(MultipleTestsCaseExampleTestEnv)
def multipleTests_SecondTestCase(test_env):
    raise TestStepError("not implemented")
