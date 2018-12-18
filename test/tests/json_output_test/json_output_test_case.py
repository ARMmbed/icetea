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

__author__ = 'joonik'


from icetea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="json_output_test",
                       title = "Test list output as json",
                       status="development",
                       type="acceptance",
                       purpose ="dummy",
                       component=["Icetea_ut"],
                       requirements={
                           "duts": {
                           }
                       }
        )

    def setup(self):
        pass

    def case(self):
        pass

    def teardown(self):
        pass