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


Plugin that adds assertion functions to test bench.
"""

from icetea_lib.Plugin.PluginBase import PluginBase
import icetea_lib.tools.asserts as asserts


class AssertPlugin(PluginBase):
    """
    Plugin for Asserts
    """
    def __init__(self):  # pylint: disable=useless-super-delegation
        super(AssertPlugin, self).__init__()
        self.bench = None

    def init(self, bench=None):
        """
        Store bench instance
        :param bench: Bench
        :return: Nothing
        :raises: AttributeError if bench is None
        """
        self.bench = bench
        if self.bench is None:
            raise AttributeError("Bench instance not present!")

    def get_bench_api(self):
        """
        Extend bench functionality with these new commands
        :return: Dictionary
        """
        # Extend bench functionality with these new commands
        ret_dict = dict()
        ret_dict["assertTraceDoesNotContain"] = asserts.assertTraceDoesNotContain
        ret_dict["assertTraceContains"] = asserts.assertTraceContains
        ret_dict["assertDutTraceDoesNotContain"] = self.assert_dut_trace_not_contains
        ret_dict["assertDutTraceContains"] = self.assert_dut_trace_contains
        ret_dict["assertTrue"] = asserts.assertTrue
        ret_dict["assertFalse"] = asserts.assertFalse
        ret_dict["assertNone"] = asserts.assertNone
        ret_dict["assertNotNone"] = asserts.assertNotNone
        ret_dict["assertEqual"] = asserts.assertEqual
        ret_dict["assertNotEqual"] = asserts.assertNotEqual
        ret_dict["assertJsonContains"] = asserts.assertJsonContains
        return ret_dict

    def assert_dut_trace_contains(self, k, message):
        """
        Wrapper to provice access to bench for assertDutTraceContains.
        :param k: index of dut
        :param message: Message that should be in traces
        :return: Nothing
        """
        asserts.assertDutTraceContains(k, message, bench=self.bench)

    def assert_dut_trace_not_contains(self, k, message):
        """
        Wrapper to provice access to bench for assertDutTraceDoesNotContain.
        :param k: index of dut
        :param message: Message that should not appear in traces
        :return: Nothing
        """
        asserts.assertDutTraceDoesNotContain(k, message, bench=self.bench)
