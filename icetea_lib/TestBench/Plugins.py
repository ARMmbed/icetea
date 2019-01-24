# pylint: disable=no-member
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

Helpers for handling plugins.
"""

from pydash import get
from jsonmerge import merge

from icetea_lib.CliResponseParser import ParserManager
from icetea_lib.Plugin.PluginManager import PluginManager
from icetea_lib.Plugin.PluginManager import PluginException
from icetea_lib.tools.GenericProcess import GenericProcess


class Plugins(object):
    """
    This Mixer manage Test used Plugins.
    """
    def __init__(self, logger, env, args, config):
        super(Plugins, self).__init__()
        self._parser_manager = None
        self._pluginmanager = None
        self._logger = logger
        self._env = env
        self._args = args
        self._config = config

    def init(self, benchapi, logger=None):
        """
        Initialize Parser and Plugin managers.

        :return: Nothing
        """
        self._env = benchapi.env
        if logger:
            self._logger = logger
        self._parser_manager = ParserManager(self._logger)
        self._pluginmanager = PluginManager(responseparser=self._parser_manager,
                                            bench=benchapi,
                                            logger=self._logger)

    def load_plugins(self):
        """
        Initialize PluginManager and Load bench related plugins.

        :return: Nothing
        """
        self._pluginmanager.load_default_tc_plugins()
        self._pluginmanager.load_custom_tc_plugins(self._args.plugin_path)

    @property
    def pluginmanager(self):
        """
        Getter for PluginManager.

        :return: PluginManager
        """
        return self._pluginmanager

    @pluginmanager.setter
    def pluginmanager(self, value):
        """
        Setter for PluginManager.
        """
        self._pluginmanager = value

    # All required external services starting here
    def start_external_services(self):
        """
        Start ExtApps required by test case.

        :return: Nothing
        """
        apps = get(self._config, 'requirements.external.apps', [])
        for app in apps:
            # Check if we have an environment configuration for this app
            conf = app
            try:
                conf = merge(conf, self._env["extApps"][app["name"]])
            except KeyError:
                self._logger.warning("Unable to merge configuration for app %s", app,
                                     exc_info=True if not self._args.silent else False)

            if 'name' in app:
                try:
                    self.pluginmanager.start_external_service(app['name'], conf=conf)
                except PluginException:
                    self._logger.error("Failed to start requested external services.")
                    raise EnvironmentError("Failed to start requested external services.")
                self._logger.info("done")
            else:
                conf_path = None
                conf_cmd = None
                try:
                    conf_path = conf["path"]
                except KeyError:
                    self._logger.warning("No path defined for app %s", app)
                try:
                    conf_cmd = conf["cmd"]
                except KeyError:
                    self._logger.warning("No command defined for app %s", app)
                appname = 'generic'
                newapp = GenericProcess(name=appname, path=conf_path, cmd=conf_cmd)
                newapp.ignore_return_code = True
                newapp.start_process()

    def stop_external_services(self):
        """
        Stop external services started via PluginManager
        """
        self._logger.debug("Stop external services if any")
        self.pluginmanager.stop_external_services()

    def parse_response(self, cmd, response):
        """
        Parse a response for command cmd.

        :param cmd: Command
        :param response: Response
        :return: Parsed response (usually dict)
        """
        return self._parser_manager.parse(cmd, response)
