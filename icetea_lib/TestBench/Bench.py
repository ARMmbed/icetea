# pylint: disable=no-member,attribute-defined-outside-init
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

Main test bench module. Contains the Bench class that subclasses a multitude of mixins.
"""

from icetea_lib.TestBench.BenchApi import BenchApi
from icetea_lib.TestBench.RunnerSM import RunnerSM
from icetea_lib.ReturnCodes import ReturnCodes
from icetea_lib.TestStepError import TestStepError, InconclusiveError


class Bench(BenchApi):
    """
    This is base Bench class which merge all subclasses together to one logical blob.
    Each subclasses (called Mixer) brings some functionality to Bench.
    Logger mixer brings self.logger -instance which are most widely used.
    RunnerMixer manage test execution in right order, like setup_bench, and teardown_bench -calling.
    See rest of Mixer functionality from theirs class descriptions.
    This class brings very top level API's, e.g. constructor
    for whole system and run -method which is called by TestManager when test begins.
    """

    def __init__(self, **kwargs):
        super(Bench, self).__init__(**kwargs)
        self.runner = None

    def run(self):
        """
        Run the test bench.

        :return: int (return code)
        """
        try:
            self._init()
            self.runner = RunnerSM(self, self.logger)
        except (TestStepError, InconclusiveError) as error:
            self.set_failure(ReturnCodes.RETCODE_FAIL_INCONCLUSIVE, str(error))
            self.logger.error(error)
            self.logger.info("Test case verdict: INCONCLUSIVE")
            return ReturnCodes.RETCODE_FAIL_INCONCLUSIVE
        skip = self.runner.check_skip()
        if skip is not None:
            return skip
        retval = self.runner.run()
        if retval in ReturnCodes.INCONCLUSIVE_RETCODES:
            verdict = "INCONCLUSIVE"
        elif retval == ReturnCodes.RETCODE_SKIP:
            verdict = "SKIP"
        elif retval == ReturnCodes.RETCODE_SUCCESS:
            verdict = "PASS"
        else:
            verdict = "FAIL"
        self.logger.info("Test case verdict: %s", verdict)
        return retval
