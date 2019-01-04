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


from icetea_lib.Plugin.plugins.Asserts import AssertPlugin
from icetea_lib.Plugin.plugins.default_parsers import DefaultParsers
from icetea_lib.Plugin.plugins.FileApi import FileApiPlugin
from icetea_lib.Plugin.plugins.HttpApi import HttpApiPlugin
from icetea_lib.Plugin.plugins.plugin_localallocator import LocalAllocatorPlugin

default_plugins = {  # pylint: disable=invalid-name
    "AssertPlugin": AssertPlugin,
    "default_parsers": DefaultParsers,
    "FileApi": FileApiPlugin,
    "HttpApi": HttpApiPlugin,
    "LocalAllocator": LocalAllocatorPlugin
}
