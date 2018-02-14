# pylint: disable=missing-docstring

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
import os

from icetea_lib.Result import Result
from icetea_lib.ResultList import ResultList


class ResultTestcase(unittest.TestCase):
    # RESULTLIST TESTCASES

    def test_append(self):
        # Test append for single Result
        rlist = ResultList()
        result1 = Result()
        rlist.append(result1)
        self.assertListEqual(rlist.data, [result1])

        # Test append for ResultList
        result2 = Result()
        rlist2 = ResultList()
        rlist2.append(result2)
        rlist.append(rlist2)
        self.assertListEqual(rlist.data, [result1, result2])

        # Test append TypeError
        with self.assertRaises(TypeError):
            rlist.append(["test"])

    # RESULT TESTCASES

    def test_init(self):
        dictionary = {"retcode": 0}
        res = Result(kwargs=dictionary)
        self.assertEqual(res.get_verdict(), "pass")

        dictionary = {"retcode": 1}
        res = Result(kwargs=dictionary)
        self.assertEqual(res.get_verdict(), "fail")

    def test_set_verdict(self):
        result = Result()
        result.set_verdict("pass", 0, 10)
        self.assertEqual(result.get_verdict(), "pass")
        self.assertEqual(result.retcode, 0)
        self.assertEqual(result.get_duration(), '0:00:10')
        self.assertEqual(result.get_duration(True), '10')

        with self.assertRaises(ValueError):
            result.set_verdict("wat")

    def test_haslogs(self):
        result = Result()
        result.logpath = os.path.join(os.path.dirname(__file__), "test_logpath")
        files = result.has_logs()
        self.assertTrue(files)
        self.assertEqual(len(files), 2)

        result = Result()
        result.logpath = None
        files = result.has_logs()
        self.assertListEqual(files, [])


if __name__ == '__main__':
    unittest.main()
