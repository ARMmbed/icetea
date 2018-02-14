# pylint: disable=missing-docstring,invalid-name

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

from jsonschema import validate, ValidationError


class ValidatorTestcase(unittest.TestCase):

    def setUp(self):
        with open(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               "..", "icetea_lib",
                                               'tc_schema.json'))) as data_file:
            self.tc_meta_schema = json.load(data_file)

    def test_validation_successful(self):
        meta = {"name": "test_case",
                "title": "test_case",
                "status": "development",
                "purpose": "unittest",
                "component": ["validator"],
                "type": "smoke",
                "requirements": {
                    "duts": {
                        "*": {
                            "count": 1,
                            "type": "process",
                            "platform_name": "test_plat",
                            "application": {
                                "version": "1.0.0",
                                "name": "app_name",
                                "bin": "binary",
                                "cli_ready_trigger": "trigger",
                                "cli_ready_trigger_timeout": 10,
                                "init_cli_cmds": [],
                                "post_cli_cmds": [],
                                "bin_args": ["arg1", "arg2"]
                                },
                            "location": [],
                            }
                        }
                    },
                "external": {
                    "ExtApp": "ExtAppName"
                    }
               }
        validate(meta, self.tc_meta_schema)

    def test_validation_successful_with_extra_fields_and_missing_fields(self):
        meta = {"extra_field": {"This field does not exist in the schema": "data"}}

        validate(meta, self.tc_meta_schema)

    def test_validation_causes_error(self):
        meta = {"name": "test_case",
                "title": "test_case",
                "status": "development",
                "purpose": "unittest",
                "component": "validator",  # This should cause an error
                "type": "smoke",
                "requirements": {
                    "duts": {
                        "*": {
                            "count": 1,
                            "type": "process",
                            "platform_name": "test_plat",
                            "application": {
                                "version": "1.0.0",
                                "name": "app_name",
                                "bin": "binary",
                                "cli_ready_trigger": "trigger",
                                "cli_ready_trigger_timeout": 10,
                                "init_cli_cmds": [],
                                "post_cli_cmds": [],
                                "bin_args": ["arg1", "arg2"]
                                },
                            "location": [0.0, 0.0],
                            }
                        }
                    },
                "external": {
                    "ExtApp": "ExtAppName"
                }
               }
        with self.assertRaises(ValidationError):
            validate(meta, self.tc_meta_schema)

        meta["component"] = ["validator"]
        meta["status"] = "Not_exists" # This should cause an error

        with self.assertRaises(ValidationError):
            validate(meta, self.tc_meta_schema)


if __name__ == '__main__':
    unittest.main()
