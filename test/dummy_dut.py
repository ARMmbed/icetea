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

import os
import sys
import subprocess


def compile_dummy_dut():
    """
    Compile the dummy dut.

    :return: Nothing
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if sys.platform == 'win32':
        dut_file = os.path.join(current_dir, "dut", "dummyDut.exe")
    else:
        dut_file = os.path.join(current_dir, "dut", "dummyDut")
    if not os.path.isfile(dut_file):
        subprocess.check_call(["make"], cwd=os.path.join(current_dir, "dut"))
