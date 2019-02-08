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

from argparse import ArgumentTypeError
import os
import sys
import unittest

from icetea_lib.arguments import get_parser, get_tc_arguments, get_base_arguments, str_arg_to_bool



def _parse_arguments():
    parser = get_base_arguments(get_parser())
    parser = get_tc_arguments(parser)
    args, unknown = parser.parse_known_args()
    return args, unknown


class MyTestCase(unittest.TestCase):

    def test_args_from_file(self):
        sys.argv = ["filename.py", "--tc", "test_case_1", "--tcdir", "test_directory",
                    "--cfg_file",
                    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "data/conf_file.txt")),
                    "--suitedir",
                    "shouldoverwrite"]
        parser = get_parser()  # pylint: disable=unused-variable
        args, unknown = _parse_arguments()  # pylint: disable=unused-variable
        for arg in ["tc", "tcdir", "cfg_file", "baudrate", "suitedir"]:
            self.assertTrue(hasattr(args, arg))
        self.assertEqual(args.tc, "test_case_1")
        self.assertEqual(args.tcdir, "shouldoverwrite")
        self.assertEqual(args.baudrate, 9600)
        self.assertEqual(args.suitedir, "shouldoverwrite")

    def test_args_from_file_with_other_file(self):  # pylint: disable=invalid-name
        sys.argv = ["filename.py", "--cfg_file",
                    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "data/conf_file_2.txt"))]
        parser = get_parser()  # pylint: disable=unused-variable
        args, unknown = _parse_arguments()  # pylint: disable=unused-variable
        for arg in ["tcdir", "baudrate", "suitedir"]:
            self.assertTrue(hasattr(args, arg))
        self.assertEqual(args.tcdir, "shouldoverwrite")
        self.assertEqual(args.baudrate, 9600)
        self.assertEqual(args.suitedir, "shouldoverwrite")

    def test_args_from_file_with_file_infinite_recursion(self):  # pylint: disable=invalid-name
        sys.argv = ["filename.py", "--cfg_file",
                    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "data/conf_file_3.txt"))]
        parser = get_parser()  # pylint: disable=unused-variable
        args, unknown = _parse_arguments()  # pylint: disable=unused-variable
        for arg in ["tcdir", "baudrate", "suitedir"]:
            self.assertTrue(hasattr(args, arg))
        self.assertEqual(args.tcdir, "shouldoverwrite")

    def test_str2bool(self):
        positives_list = ["y", "Y", "t", "T", "1", "yes", "YES", "True", "true"]
        negatives_list = ["n", "N", "no", "No", "f", "F", "False", "false", "0"]
        for bool_to_conv in positives_list:
            self.assertTrue(str_arg_to_bool(bool_to_conv))
        for bool_to_conv in negatives_list:
            self.assertFalse(str_arg_to_bool(bool_to_conv))
        with self.assertRaises(ArgumentTypeError):
            str_arg_to_bool("2")
        with self.assertRaises(ArgumentTypeError):
            str_arg_to_bool("test")


if __name__ == '__main__':
    unittest.main()
