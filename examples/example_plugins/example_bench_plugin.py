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

This is an example plugin that implements no real functionality.
It demonstrated the implementation of a BenchExtension type plugin.
"""

from icetea_lib.Plugin.PluginBase import PluginBase
from icetea_lib.Plugin.PluginManager import PluginException


class BenchPlugin(PluginBase):
    def __init__(self):
        super(BenchPlugin, self).__init__()

    def init(self, bench=None):
        """
        This function provides access to the test bench object.
        :param bench: Bench
        :return: Nothing
        """
        if bench is None:
            raise PluginException("Bench not provided!")
        self.bench = bench

    def get_bench_api(self):
        """
        This function should return a dictionary. The keys are added to Bench as attributes and
        their values are set as the values of the attribute. In a test case, calling
        self.plugin_func() should result in a call to example_plugin_function.
        :return: dict
        """
        return {"plugin_func": self.example_plugin_function,
                "plugin_class": ExamplePluginClass}

    def example_plugin_function(self):
        pass


class ExamplePluginClass(object):
    def __init__(self, *args, **kwargs):
        pass
