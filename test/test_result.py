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

from icedtea_lib.Result import Result
from icedtea_lib.ResultList import ResultList


class ResultTestcase(unittest.TestCase):
    # RESULTLIST TESTCASES

    def test_append(self):
        # Test append for single Result
        rlist = ResultList()
        r1 = Result()
        rlist.append(r1)
        self.assertListEqual(rlist.data, [r1])

        # Test append for ResultList
        r2 = Result()
        rlist2 = ResultList()
        rlist2.append(r2)
        rlist.append(rlist2)
        self.assertListEqual(rlist.data, [r1, r2])

        # Test append TypeError
        with self.assertRaises(TypeError):
            rlist.append(["test"])

    # RESULT TESTCASES

    def test_init(self):
        di = {"retcode": 0}
        res = Result(kwargs=di)
        self.assertEqual(res.get_verdict(), "pass")

        di = {"retcode": 1}
        res = Result(kwargs=di)
        self.assertEqual(res.get_verdict(), "fail")

    def test_setVerdict(self):
        r = Result()
        r.set_verdict("pass", 0, 10)
        self.assertEqual(r.get_verdict(), "pass")
        self.assertEqual(r.retcode, 0)
        self.assertEqual(r.get_duration(), '0:00:10')
        self.assertEqual(r.get_duration(True), '10')

        with self.assertRaises(ValueError):
            r.set_verdict("wat")

    def test_haslogs(self):
        r = Result()
        r.logpath = os.path.join(os.path.dirname(__file__), "test_logpath")
        files = r.has_logs()
        self.assertTrue(files)
        self.assertEqual(len(files), 2)

        r = Result()
        r.logpath = None
        files = r.has_logs()
        self.assertListEqual(files, [])


if __name__ == '__main__':
    unittest.main()
