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

Testcase for demonstrating usage of HttpApi plugin.
"""

from icedtea_lib.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_http",
                       title="Test http methods",
                       status="development",
                       type="acceptance",
                       purpose="dummy",
                       requirements={
                           "duts": {
                           }}
                       )

    def setup(self):
        pass

    def case(self):
        #Initialize the HttpApi with the path to the server you want to contact
        http = self.HttpApi("https://www.mbed.com/en/")
        #Send get request to "https://mbed.com/", should respond with 200
        resp = http.get("/")
        if resp.status_code == 200:
            self.logger.info("mbed.com responded with status code 200!")
        #This should fail
        #resp = http.get("/", expected=201)

    def teardown(self):
        pass