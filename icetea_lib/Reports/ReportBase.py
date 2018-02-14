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

ReportBase module, contains the base class for other report types.
"""

import os
from datetime import timedelta
import icetea_lib.LogManager as LogManager

#pylint: disable=no-self-use

class ReportBase(object):
    """
    ReportBase is the baseclass of all other report types. It implements helpers related to
    reporting as well as the abstract generate-method.
    """
    def __init__(self, results):
        self.results = results
        self.summary = results.get_summary()

    def get_latest_filename(self, extension, basename="../latest."):
        """
        Generate filename with 'latest.' prefix.

        :param extension: Extension for file
        :param basename: Base file name
        :return: path to latest.basename.extension.
        """
        return os.path.join(LogManager.get_base_dir(), basename+extension)

    def get_current_filename(self, extension, basename="result."):
        """
        Generate filename for a report.

        :param extension: Extension for file name
        :param basename: Base file name
        :return: path to basename.extension
        """
        return os.path.join(LogManager.get_base_dir(), basename+extension)

    def generate(self, *args, **kwargs):
        """
        Abstract generate-method.
        """
        raise NotImplementedError("generate function missing")

    def duration_to_string(self, seconds):
        """
        Converts time in seconds to a timedelta and represents it as string.

        :param seconds: Time in seconds
        :return: str(datetime.timedelta)
        """
        delta = timedelta(seconds=seconds)
        return str(delta)
