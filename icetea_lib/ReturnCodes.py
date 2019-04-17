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

Bench module. This does all the things and is in dire need of refactoring to reduce complexity
and speed up further development and debugging.
"""


class ReturnCodes(object): #pylint: disable=no-init,too-few-public-methods
    #pylint: disable=invalid-name
    """
    Enum for Bench return codes.
    """
    RETCODE_SKIP = -1
    RETCODE_SUCCESS = 0
    RETCODE_FAIL_SETUP_BENCH = 1000
    RETCODE_FAIL_SETUP_TC = 1001
    RETCODE_FAIL_MISSING_DUTS = 1002
    RETCODE_FAIL_UNDEFINED_REQUIRED_DUTS_COUNT = 1003
    RETCODE_FAIL_DUT_CONNECTION_FAIL = 1004
    RETCODE_FAIL_TC_EXCEPTION = 1005
    RETCODE_FAIL_TEARDOWN_TC = 1006
    RETCODE_FAIL_INITIALIZE_BENCH = 1007
    RETCODE_FAIL_NO_PRELIMINARY_VERDICT = 1010
    RETCODE_FAIL_TEARDOWN_BENCH = 1011
    RETCODE_FAIL_ABORTED_BY_USER = 1012
    RETCODE_FAIL_UNKNOWN = 1013
    RETCODE_FAIL_INCONCLUSIVE = 1014
    RETCODE_FAIL_TC_NOT_FOUND = 1015

    INCONCLUSIVE_RETCODES = [RETCODE_FAIL_ABORTED_BY_USER,
                             RETCODE_FAIL_INITIALIZE_BENCH,
                             RETCODE_FAIL_TEARDOWN_BENCH,
                             RETCODE_FAIL_SETUP_BENCH,
                             RETCODE_FAIL_DUT_CONNECTION_FAIL,
                             RETCODE_FAIL_INCONCLUSIVE,
                             RETCODE_FAIL_TC_NOT_FOUND]
    ALL_RETCODES = [RETCODE_SKIP,
                    RETCODE_SUCCESS,
                    RETCODE_FAIL_SETUP_BENCH,
                    RETCODE_FAIL_SETUP_TC,
                    RETCODE_FAIL_MISSING_DUTS,
                    RETCODE_FAIL_UNDEFINED_REQUIRED_DUTS_COUNT,
                    RETCODE_FAIL_DUT_CONNECTION_FAIL,
                    RETCODE_FAIL_TC_EXCEPTION,
                    RETCODE_FAIL_TEARDOWN_BENCH,
                    RETCODE_FAIL_TEARDOWN_TC,
                    RETCODE_FAIL_INITIALIZE_BENCH,
                    RETCODE_FAIL_NO_PRELIMINARY_VERDICT,
                    RETCODE_FAIL_ABORTED_BY_USER,
                    RETCODE_FAIL_UNKNOWN,
                    RETCODE_FAIL_INCONCLUSIVE,
                    RETCODE_FAIL_TC_NOT_FOUND]
