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

from icedtea_lib.bench import Bench


'''
IcedTea framework usage example for implementing a test case.

Mandatory:
    1. def __init__():
        """
        This init function should call Bench init function.

        :param: configuration of test case, like name, title, status etc.
                In the example below, we listed all the configuration keyword.
                For more configuration details, please check doc/tc_api.md or sample.py.
                NOTE!: You can choose what you need from all the configurations.
        """

    2. def case():
        """
        Test case functionality should be implemented here.
        """


Optional:
    1. setup()
        """
        Prerequisites for test case execution: like setting up dut configurations, initializing network interfaces etc.
        """

    2. teardown()
        """
        Test case cleanup: like deleting temporary files, shutdown network interfaces etc.
        """
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="sample_testcase_func",
                       title="test case functions example usage",
                       status="development",
                       type="smoke",
                       purpose="show an example usage of IcedTea test case functions",
                       component=["IcedTea"],
                       requirements={
                            "duts": {
                                '*': {
                                    "count": 0,  # devices number
                                }
                            }
                        }
                       )

    def setup(self):
        self.logger.info("Here is your test case customized setUp!")

    def case(self):
        self.logger.info("Here is your test case content!")

    def teardown(self):
        self.logger.info("Here is your test case customized tearDown!")
