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

import json
import os
import unittest
import argparse
import mock

from icedtea_lib.TestSuite.TestcaseContainer import TestcaseContainer, TestStatus
from icedtea_lib.Result import Result
from icedtea_lib.bench import Bench


def mock_load_tc(*args, **kwargs):
    return None

def mock_raise_type(*args, **kwargs):
    raise TypeError()

def mock_raise_import(*args, **kwargs):
    raise ImportError()

class MockInstance:
    def __init__(self, name, version, type=None, skip_val=True, skip_info=None):
        self.info = skip_info if skip_info else {"only_type": "process"}
        self.config = {
                        "compatible":
                           {"framework":
                                {"name": name,
                                 "version": version}
                            },
                        "requirements":{
                           "duts": {
                               "*": {
                                    "type": type
                                }
                            }
                        }
                       }
        self.skip_val = skip_val

    def get_result(self):
        return Result()

    def get_test_name(self):
        return "IcedTea"

    def skip(self):
        return self.skip_val

    def skip_info(self):
        return self.info

    def skip_reason(self):
        return "test"

class TCContainerTestcase(unittest.TestCase):

    def setUp(self):
        with open(os.path.join("./icedtea_lib", 'tc_schema.json')) as data_file:
            self.tc_meta_schema = json.load(data_file)

        self.args_tc = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=False,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=None, tc="test_cmdline", tc_cfg=None, tcdir="examples", testtype=False, type="process",
            subtype=None, use_sniffer=False, valgrind=False, valgrind_tool=None, verbose=False, repeat=0, feature=None,
            suitedir="./test/suites", forceflash_once=True, forceflash=True, stop_on_failure=False, ignore_invalid_params=False)

    @mock.patch("icedtea_lib.TestSuite.TestcaseContainer.loadClass")
    def test_load_testcase_fails(self, mock_loadclass):
        tc = TestcaseContainer.find_testcases("examples.test_cmdline", "./examples", self.tc_meta_schema)[0]
        with self.assertRaises(TypeError):
            tc._load_testcase(1)
        mock_loadclass.side_effect = [ValueError, None]
        with self.assertRaises(ImportError):
            tc._load_testcase("test_case")
        with self.assertRaises(ImportError):
            tc._load_testcase("test_case")

    def test_check_major_version(self):
        tc = TestcaseContainer.find_testcases("examples.test_cmdline", "examples", self.tc_meta_schema)[0]
        self.assertFalse(tc._check_major_version("1.0.0", "0.9.1"))
        self.assertFalse(tc._check_major_version("1.0.0", ">0.0.2"))
        self.assertFalse(tc._check_major_version("1.0.0", ">=0.0.3"))

    @mock.patch("icedtea_lib.TestSuite.TestcaseContainer.get_fw_version")
    def test_version_checker(self, mock_fwver):
        mock_fwver.return_value = "0.9.0"
        tc = TestcaseContainer.find_testcases("examples.test_cmdline", "examples",
                                              self.tc_meta_schema)[0]
        self.assertIsNone(tc._check_version(MockInstance("IcedTea", "0.9.0")))
        res = tc._check_version(MockInstance("IcedTea", "0.2.2"))
        self.assertEqual(res.get_verdict(), "skip")
        mock_fwver.return_value = "0.2.2"
        self.assertIsNone(tc._check_version(MockInstance("IcedTea", "<0.9.0")))
        res = tc._check_version(MockInstance("IcedTea", ">0.9.0"))
        self.assertEqual(res.get_verdict(), "skip")
        mock_fwver.return_value = "0.9.0"
        self.assertIsNone(tc._check_version(MockInstance("IcedTea", ">=0.9.0")))
        mock_fwver.return_value = "0.9.1"
        self.assertIsNone(tc._check_version(MockInstance("IcedTea", ">=0.9.0")))

    def test_check_skip(self):
        tc = TestcaseContainer.find_testcases("examples.test_cmdline", "./examples", self.tc_meta_schema)[0]
        res = tc._check_skip(MockInstance("test", "0.9.0", "process"))
        self.assertFalse(res)
        self.assertFalse(tc._check_skip(MockInstance("test", "0.9.0", "hardware", skip_val=False)))

        res = tc._check_skip(MockInstance("test", "0.9.0", "process", True, {"test": "test"}))
        self.assertEqual(res.get_verdict(), "skip")

    def test_find_testcases(self):
        lst = TestcaseContainer.find_testcases("test.testbase.dummy_multiples", "./test/testbase", self.tc_meta_schema)
        self.assertEqual(len(lst), 2)
        lst = TestcaseContainer.find_testcases("test.testbase.dummy", "./test/testbase", self.tc_meta_schema)
        self.assertEqual(len(lst), 1)
        with self.assertRaises(TypeError):
            TestcaseContainer.find_testcases(1, "./test/testbase", self.tc_meta_schema)
        with self.assertRaises(ValueError):
            TestcaseContainer.find_testcases("", "./test/testbase", self.tc_meta_schema)

    def test_create_new_bench_instance(self):
        lst = TestcaseContainer.find_testcases("test.testbase.dummy", "./test/testbase", self.tc_meta_schema)
        inst = lst[0]._create_new_bench_instance("test.testbase.dummy")
        self.assertTrue(isinstance(inst, Bench))

    @mock.patch("icedtea_lib.TestSuite.TestcaseContainer.TestcaseContainer.get_instance")
    @mock.patch("icedtea_lib.TestSuite.TestcaseContainer.TestcaseContainer._check_version")
    @mock.patch("icedtea_lib.TestSuite.TestcaseContainer.TestcaseContainer._check_skip")
    @mock.patch("icedtea_lib.TestSuite.TestcaseContainer.get_tc_arguments")
    def test_run(self, mock_parser, mock_skip, mock_version, mock_instance):
        tc = TestcaseContainer.find_testcases("examples.test_cmdline", "./examples", self.tc_meta_schema)[0]
        #Initialize mocks
        parser = mock.MagicMock()
        instance = mock.MagicMock()
        instance.run = mock.MagicMock()
        instance.run.return_value = 0
        instance.get_result = mock.MagicMock()
        instance.get_result.return_value = Result()
        mock_instance.return_value = instance
        mock_skip.return_value = None
        mock_version.return_value = None
        parser.parse_known_args = mock.MagicMock()
        parser.parse_known_args.return_value = (mock.MagicMock(), [])
        mock_parser.return_value = parser
        # Mocked a succesful run
        tc.run()

        # Skip returns 1, tc should be skipped
        mock_skip.return_value = 1
        mock_version.return_value = None
        self.assertEqual(tc.status, TestStatus.FINISHED)

        tc.run()

        # Version mismatch
        mock_skip.return_value = None
        mock_version.return_value = 1
        self.assertEqual(tc.status, TestStatus.FINISHED)

        tc.run()

        # Unknown arguments
        mock_version.return_value = None
        parser.parse_known_args.return_value = (self.args_tc, [1])

        res = tc.run()
        self.assertEqual(tc.status, TestStatus.FINISHED)
        self.assertEqual(res.get_verdict(), 'inconclusive')

        r = Result()
        r.retcode = 1012
        instance.get_result.return_value = r
        instance.run.return_value = 1012
        parser.parse_known_args.return_value = (mock.MagicMock(), [])
        tc.run()

if __name__ == '__main__':
    unittest.main()
