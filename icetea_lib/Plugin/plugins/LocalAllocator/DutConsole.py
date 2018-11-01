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

DutConsole module, contains DutConsole class which inherits DutProcess.
"""


# Disable "string statement has no effect" warning
# pylint: disable=W0105


from icetea_lib.Plugin.plugins.LocalAllocator.DutProcess import DutProcess


class DutConsole(DutProcess):
    """
        Configuration for DutConsole. The supported configuration parameters are:
        "type":             The type of console connection; possible values: "SSH" (default)
        "username":         The username that should be used for login; default is 'arm'
        "hostname":         The hostname or IP address of the remote host; default is 'localhost'
        "port":             Port for the console connection; default is 22
        "app":              The name of the executable that creates the connection;
            default is '/usr/bin/ssh'
        "cwd":              The directory where the executable is run;
            default is None (current directory)
        "args":             Extra arguments for the executable; default is '-tt'
        "shell":            The type of shell (if any) used at the remote host; default is 'bash'
    """

    conf = {
        "type": "SSH",
        "username": "arm",
        "hostname": "localhost",
        "app": "/usr/bin/ssh",
        "port": "22",
        "cwd": None,
        "args": "-tt",
        "shell": "bash"
     }

    def __init__(self, name, conf=None, params=None):
        DutProcess.__init__(self, name=name, params=None)
        self.config.update(self.conf)

        if conf != None:
            self.config.update(conf)

        # Set up SSH connection
        if self.config["type"] == "SSH":
            self.cmd = self.config["app"] + " " + \
                       self.config["args"] + " " + \
                       self.config["username"] + "@" + \
                       self.config["hostname"] + " -p " + \
                       self.config["port"]
            self.path = self.config["cwd"]

        self.ignore_return_code = True
        self.comport = self.cmd

    def init_cli(self):
        # Set up the Bash Unix shell
        if self.config["shell"] == "bash":
            self.execute_command("export PROMPT_COMMAND='RC=$?;echo \"retcode: $RC\";'")

    def prepareConnectionClose(self): #pylint: disable=C0103
        """
        Deprecated version of prepare_connection_close. Still present for backwards compatibility

        :return: Nothing
        """
        self.logger.warning("prepareConnectionClose deprecated, use prepare_connection_close")
        self.prepare_connection_close()

    def prepare_connection_close(self):
        # No actions...
        return

    def reset(self, method=None):
        # No actions...
        return

    def writeline(self, data, crlf="\n"):
        DutProcess.writeline(self, data, crlf)

    def print_info(self):
        info_string = "DutConsole {} \n".format(self.name)
        if self.config:
            info_string = info_string + "Configuration for this DUT:\n {} \n".format(self.config)
        if self.comport:
            info_string = info_string + "COM port: {} \n".format(self.comport)
        if self.location:
            info_string = info_string + "Location: x = {}, y = {} \n".format(self.location.x_coord,
                                                                             self.location.y_coord)

        self.logger.info(info_string)

    def get_config(self):
        return self.config

    def _flash_needed(self):
        pass
