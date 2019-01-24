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

PluginManager class implements searching, importing, handling and registering plugins.
"""

import importlib
import sys
import os

from icetea_lib.Plugin.PluginBase import PluginTypes, PluginBase, RunPluginBase
from icetea_lib.Plugin.plugins.default_plugins import default_plugins


class PluginException(Exception):
    """
    Plugin Exception
    """
    pass


class PluginManager(object): # pylint: disable=too-many-instance-attributes
    """
    class PluginManager. The job of this class is to load and register plugins
    for Icetea.

    Loads modules like we load Testcases. That instance is then used to
    get the plugin contents as a dict.

    The contents of this dict are registered to relevant parts of Icetea
    according to the type of plugin we are dealing with.
    """

    def __init__(self, responseparser=None, bench=None, logger=None):
        self.logger = logger
        if self.logger is None:
            import logging
            self.logger = logging.getLogger("PluginManager")
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())
                self.logger.setLevel(logging.INFO)
        self.responseparser = responseparser
        self.bench = bench
        self._external_services = {}
        self._started_services = []
        self.registered_plugins = []
        self._allocators = {}
        self.plugin_types = {PluginTypes.BENCH: self._register_bench_extension,
                             PluginTypes.PARSER: self._register_dataparser,
                             PluginTypes.EXTSERVICE: self._register_external_service,
                             PluginTypes.ALLOCATOR: self._register_allocator}

    def register_tc_plugins(self, plugin_name, plugin_class):
        """
        Loads a plugin as a dictionary and attaches needed parts to correct areas for testing
        parts.

        :param plugin_name: Name of the plugins
        :param plugin_class: PluginBase
        :return: Nothing
        """
        if plugin_name in self.registered_plugins:
            raise PluginException("Plugin {} already registered! Duplicate "
                                  "plugins?".format(plugin_name))
        self.logger.debug("Registering plugin %s", plugin_name)
        plugin_class.init(bench=self.bench)
        if plugin_class.get_bench_api() is not None:
            register_func = self.plugin_types[PluginTypes.BENCH]
            register_func(plugin_name, plugin_class)
        if plugin_class.get_parsers() is not None:
            register_func = self.plugin_types[PluginTypes.PARSER]
            register_func(plugin_name, plugin_class)
        if plugin_class.get_external_services() is not None:
            register_func = self.plugin_types[PluginTypes.EXTSERVICE]
            register_func(plugin_name, plugin_class)

        self.registered_plugins.append(plugin_name)

    def register_run_plugins(self, plugin_name, plugin_class):
        """
        Loads a plugin as a dictionary and attaches needed parts to correct Icetea run
        global parts.

        :param plugin_name: Name of the plugins
        :param plugin_class: PluginBase
        :return: Nothing
        """
        if plugin_name in self.registered_plugins:
            raise PluginException("Plugin {} already registered! "
                                  "Duplicate plugins?".format(plugin_name))
        self.logger.debug("Registering plugin %s", plugin_name)
        if plugin_class.get_allocators():
            register_func = self.plugin_types[PluginTypes.ALLOCATOR]
            register_func(plugin_name, plugin_class)
        self.registered_plugins.append(plugin_name)

    def get_allocator(self, allocator_name):
        """
        Get a registered allocator based on allocator_name.

        :param allocator_name: Name of allocator to get
        :return: BaseAllocator
        """
        if allocator_name in self._allocators:
            return self._allocators[allocator_name]
        return None

    def load_default_tc_plugins(self):
        """
        Load default test case level plugins from icetea_lib.Plugin.plugins.default_plugins.

        :return: Nothing
        """
        for plugin_name, plugin_class in default_plugins.items():
            if issubclass(plugin_class, PluginBase):
                try:
                    self.register_tc_plugins(plugin_name, plugin_class())
                except PluginException as error:
                    self.logger.debug(error)
                    continue

    def load_custom_tc_plugins(self, plugin_path=None):
        """
        Load custom test case level plugins from plugin_path.

        :param plugin_path: Path to file, which contains the imports and mapping for plugins.
        :return: None if plugin_path is None or False or something equivalent to those.
        """
        if not plugin_path:
            return
        directory = os.path.dirname(plugin_path)
        sys.path.append(directory)
        modulename = os.path.split(plugin_path)[1]
        # Strip of file extension.
        if "." in modulename:
            modulename = modulename[:modulename.rindex(".")]
        try:
            module = importlib.import_module(modulename)
        except ImportError:
            raise PluginException("Unable to import custom plugin information from {}.".format(
                plugin_path))
        for plugin_name, plugin_class in module.plugins_to_load.items():
            if issubclass(plugin_class, PluginBase):
                try:
                    self.register_tc_plugins(plugin_name, plugin_class())
                except PluginException as error:
                    self.logger.debug(error)
                    continue

    def load_default_run_plugins(self):
        """
        Load default run level plugins from icetea_lib.Plugin.plugins.default_plugins.

        :return: Nothing
        """
        for plugin_name, plugin_class in default_plugins.items():
            if issubclass(plugin_class, RunPluginBase):
                try:
                    self.register_run_plugins(plugin_name, plugin_class())
                except PluginException as error:
                    self.logger.debug(error)
                    continue

    def load_custom_run_plugins(self, plugin_path=None):
        """
        Load custom run level plugins from plugin_path.

        :param plugin_path: Path to file, which contains the imports and mapping for plugins.
        :return: None if plugin_path is None or False or something equivalent to those.
        """
        if not plugin_path:
            return
        directory = os.path.dirname(plugin_path)
        sys.path.append(directory)
        modulename = os.path.split(plugin_path)[1]
        # Strip of file extension.
        if "." in modulename:
            modulename = modulename[:modulename.rindex(".")]
        try:
            module = importlib.import_module(modulename)
        except ImportError:
            raise PluginException("Unable to import custom plugin information from {}.".format(
                plugin_path))
        for plugin_name, plugin_class in module.plugins_to_load.items():
            if issubclass(plugin_class, RunPluginBase):
                try:
                    self.register_run_plugins(plugin_name, plugin_class())
                except PluginException as error:
                    self.logger.debug(error)
                    continue

    def start_external_service(self, service_name, conf=None):
        """
        Start external service service_name with configuration conf.

        :param service_name: Name of service to start
        :param conf:
        :return: nothing
        """
        if service_name in self._external_services:
            ser = self._external_services[service_name]
            service = ser(service_name, conf=conf, bench=self.bench)
            try:
                service.start()
            except PluginException:
                self.logger.exception("Starting service %s caused an exception!", service_name)
                raise PluginException("Failed to start external service {}".format(service_name))
            self._started_services.append(service)
            setattr(self.bench, service_name, service)
        else:
            self.logger.warning("Service %s not found. Check your plugins.", service_name)

    def stop_external_services(self):
        """
        Stop all external services.

        :return: Nothing
        """
        for service in self._started_services:
            self.logger.debug("Stopping application %s", service.name)
            try:
                service.stop()
            except PluginException:
                self.logger.exception("Stopping external service %s caused and exception!",
                                      service.name)
        self._started_services = []

    def _register_bench_extension(self, plugin_name, plugin_instance):
        """
        Register a bench extension.

        :param plugin_name: Plugin name
        :param plugin_instance: PluginBase
        :return: Nothing
        """
        for attr in plugin_instance.get_bench_api().keys():
            if hasattr(self.bench, attr):
                raise PluginException("Attribute {} already exists in bench! Unable to add "
                                      "plugin {}.".format(attr, plugin_name))
            setattr(self.bench, attr, plugin_instance.get_bench_api().get(attr))

    def _register_dataparser(self, plugin_name, plugin_instance):
        """
        Register a parser.

        :param plugin_name: Parser name
        :param plugin_instance: PluginBase
        :return: Nothing
        """
        for parser in plugin_instance.get_parsers().keys():
            if self.responseparser.has_parser(parser):
                raise PluginException("Parser {} already registered to parsers! Unable to "
                                      "add parsers from {}.".format(parser, plugin_name))
            self.responseparser.add_parser(parser, plugin_instance.get_parsers().get(parser))

    def _register_external_service(self, plugin_name, plugin_instance):
        """
        Register an external service.

        :param plugin_name: Service name
        :param plugin_instance: PluginBase
        :return:
        """
        for attr in plugin_instance.get_external_services().keys():
            if attr in self._external_services:
                raise PluginException("External service with name {} already exists! Unable to add "
                                      "services from plugin {}.".format(attr, plugin_name))
            self._external_services[attr] = plugin_instance.get_external_services().get(attr)

    def _register_allocator(self, plugin_name, plugin_instance):
        """
        Register an allocator.

        :param plugin_name: Allocator name
        :param plugin_instance: RunPluginBase
        :return:
        """
        for allocator in plugin_instance.get_allocators().keys():
            if allocator in self._allocators:
                raise PluginException("Allocator with name {} already exists! unable to add "
                                      "allocators from plugin {}".format(allocator, plugin_name))
            self._allocators[allocator] = plugin_instance.get_allocators().get(allocator)
