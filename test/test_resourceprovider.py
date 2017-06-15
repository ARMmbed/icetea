"""
Copyright 2016 ARM Limited

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
import mock
from mbed_test.ResourceProvider.ResourceProvider import ResourceProvider
from mbed_test.ResourceProvider.exceptions import ResourceInitError
from mbed_test.ResourceProvider.Allocators.exceptions import AllocationError

#Stubbed methods in a mock object of ResourceConfig
class Mock_ResourceConfig():
    def __init__(self, verbose = False):
        self.chw_calls = 0
        self.cs_calls = 0
        self.cd_calls = 0
        self.verbose = verbose

    def count_hardware(self):
        self.chw_calls = self.chw_calls + 1
        if self.verbose:
            print("Called count_hardware. Calls to count_hardware: {}".format(self.chw_calls))
        if self.chw_calls == 1:
            return 1
        else:
            return 0


    def get_dut_configuration(self):
        return [
            {"1": {"type": "process", "allowed_platforms": [], "nick": "Leader"}},
            {"2": {"type": "process", "allowed_platforms": [], "nick": "Follower"}}
        ]

    def count_duts(self):
        self.cd_calls = self.cd_calls + 1
        if self.verbose:
            print("Called count_duts. Calls to count_duts: {}".format(self.cd_calls))
        if self.cd_calls < 9:
            return 1
        else:
            return 0


def mock_get_allocator():
    m = mock.Mock()
    args =  {"allocate.side_effect": [AllocationError]}
    m.configure_mock(**args)
    return m

def mock_get_allocator2():
    m = mock.Mock()
    args =  {"allocate.side_effect": [1]}
    m.configure_mock(**args)
    return m

def mock_duts():
    m = mock.Mock()
    args =  {"Close.return_value": 1}
    m.configure_mock(**args)
    return m

def mock_get_resource():
    m = mock.Mock()
    args =  {"Close.return_value": 1}
    m.configure_mock(**args)
    return m

class ResourceProvider_Testcase(unittest.TestCase):

    def setUp(self):
        self._resource_configuration= [
            {"1": {"type": "process", "allowed_platforms": [], "nlick": "Leader"}},
            {"2": {"type": "process", "allowed_platforms": [], "nick": "Follower"}}
        ]

    def tearDown(self):
        del self._resource_configuration

    @mock.patch("mbed_test.ResourceProvider.ResourceProvider.ResourceConfig")
    @mock.patch("mbed_test.ResourceProvider.ResourceProvider.LogManager.get_bench_logger")
    def test_initialize_duts(self, mock_logger, mock_config):
        mock_config.side_effect = [None, Mock_ResourceConfig()]
        #mock_allocator.side_effect = [AllocationError]
        rp = ResourceProvider([])
        with self.assertRaises(ResourceInitError):
            rp.initialize_duts()

        rp = ResourceProvider([])
        with self.assertRaises(ResourceInitError):
            rp.initialize_duts()

        with mock.patch.object(rp, "_ResourceProvider__get_allocator", mock_get_allocator):
            with self.assertRaises(ResourceInitError):
                rp._duts = [mock_duts()]
                rp.initialize_duts()

        with mock.patch.object(rp, "_ResourceProvider__get_allocator", mock_get_allocator2):
            with self.assertRaises(ResourceInitError):
                rp._duts = [mock_duts(), 2]
                rp.initialize_duts()



if __name__ == '__main__':
    unittest.main()
