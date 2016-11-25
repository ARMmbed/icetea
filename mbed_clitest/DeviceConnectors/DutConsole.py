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

from mbed_clitest.DeviceConnectors.DutProcess import DutProcess

"""
    Configuration for DutConsole. The supported configuration parameters are:
    "type":             The type of console connection; possible values: "SSH" (default)
    "username":         The username that should be used for login; default is 'arm'
    "hostname":         The hostname or IP address of the remote host; default is 'localhost'
    "port":             Port for the console connection; default is 22
    "app":              The name of the executable that creates the connection; default is '/usr/bin/ssh'
    "cwd":              The directory where the executable is run; default is None (current directory)
    "args":             Extra arguments for the executable; default is '-tt'
    "shell":            The type of shell (if any) used at the remote host; default is 'bash'
"""
class DutConsole(DutProcess):
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

    def __init__(self, name, conf=None):
        DutProcess.__init__(self, name=name)

        if conf != None:
            self.conf.update(conf)

        # Set up SSH connection
        if self.conf["type"] == "SSH":
            self.cmd = self.conf["app"] + " " + self.conf["args"] + " " + self.conf["username"] + "@" + self.conf["hostname"] + " -p " + self.conf["port"]
            self.path = self.conf["cwd"]

        self.ignoreReturnCode = True
        self.comport = self.cmd

    def initCLI(self):
        # Set up the Bash Unix shell
        if self.conf["shell"] == "bash":
            self.executeCommand("export PROMPT_COMMAND='RC=$?;echo \"retcode: $RC\";'")

    def prepareConnectionClose(self):
        # No actions...
        return

    def reset(self, method=None):
        # No actions...
        return

    def writeline(self, data):
        DutProcess.writeline(self, data, "\n")

    def printInfo(self):
        info_string = "DutConsole {} \n".format(self.name)
        if self.config:
            info_string = info_string + "Configuration for this DUT:\n {} \n".format(self.config)
        if self.conf:
            info_string = info_string + "DutConsole specific configuration:\n {} \n".format(self.conf)
        if self.comport:
            info_string = info_string + "COM port: {} \n".format(self.comport)
        if self.location:
            info_string = info_string + "Location: x = {}, y = {} \n".format(self.location.x, self.location.y)

        self.logger.info(info_string)


