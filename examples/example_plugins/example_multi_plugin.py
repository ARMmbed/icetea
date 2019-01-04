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
It demonstrated the implementation of external service type plugins and response parsers.
"""
# pylint: disable=missing-docstring,no-self-use,unnecessary-pass,useless-super-delegation

from icetea_lib.Plugin.PluginBase import PluginBase


class ExamplePlugin(PluginBase):
    def __init__(self):
        super(ExamplePlugin, self).__init__()

    def get_external_services(self):
        """
        :return: dict
        """
        return {"ExampleService": ExampleService}

    def get_parsers(self):
        """
        :return: dict
        """
        return {"ExampleParserPlugin": self.example_parser}

    def example_parser(self, data):
        """
        A simple example parser that looks for one occurence of string 'one'.
        :param data: line of data as string
        :return: dict
        """
        parsed = PluginBase.find_one(data, "one")
        return {"one_found": parsed}


class ExampleService(object):
    def __init__(self, name, **kwargs):
        """
        :param name: Name of the service
        :param kwargs: kwargs 'conf' and 'bench'
        """
        self.name = name
        self.conf = kwargs["conf"]
        self.bench = kwargs["bench"]

    def start(self):
        pass

    def stop(self):
        pass
