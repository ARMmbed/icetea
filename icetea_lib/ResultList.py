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

ResultList module, contains the ResultList class, which is an object to store Result objects.
"""

from collections import Iterator

from icetea_lib.Reports.ReportJunit import ReportJunit
from icetea_lib.Reports.ReportHtml import ReportHtml
from icetea_lib.Reports.ReportConsole import ReportConsole
from icetea_lib.Result import Result


class ResultList(Iterator):
    """
    List of Result objects. Implements parts of Iterator interface to allow some ease of use.
    """
    def __init__(self):  # pylint: disable=super-init-not-called
        """
        Constructor for ResultList
        """
        self.data = []
        self.index = 0

    def append(self, result):
        """
        Append a new Result to the list
        :param result: Result to append
        :return: Nothing
        :raises: TypeError if result is not Result or ResultList
        """
        if isinstance(result, Result):
            self.data.append(result)
        elif isinstance(result, ResultList):
            self.data += result.data
        else:
            raise TypeError('unknown result type')

        # @todo this could be used to generate html table after each test..
        # self._save_html_report({"NOTE": "TESTS EXECUTION IS ONGOING.."}, reload=5)

    def save(self, heads):
        """
        Create reports in different formats.

        :param heads: html table extra values in title rows
        """
        # Junit
        self._save_junit()
        # HTML
        self._save_html_report(heads)
        # Console print
        self._print_console_summary()

    def _save_junit(self):
        """
        Save Junit report.

        :return: Nothing
        """
        report = ReportJunit(self)
        file_name = report.get_latest_filename("result.junit.xml", "")
        report.generate(file_name)

        file_name = report.get_latest_filename("junit.xml", "../")
        report.generate(file_name)

    def _save_html_report(self, heads=None, refresh=None):
        """
        Save html report.

        :param heads: headers as dict
        :param refresh: Boolean, if True will add a reload-tag to the report
        :return: Nothing
        """
        report = ReportHtml(self)
        heads = heads if heads else {}
        test_report_filename = report.get_current_filename("html")
        report.generate(test_report_filename, title='Test Results', heads=heads, refresh=refresh)

        # Update latest.html in the log root directory
        latest_report_filename = report.get_latest_filename("html")
        report.generate(latest_report_filename, title='Test Results', heads=heads, refresh=refresh)

    def _print_console_summary(self):
        """
        Print the console report.

        :return: Nothing
        """
        ReportConsole(self).generate()

    def success_count(self):
        """
        Amount of passed test cases in this list.

        :return: integer
        """
        return len([i for i, result in enumerate(self.data) if result.success])

    def failure_count(self):
        """
        Amount of failed test cases in this list.

        :return: integer
        """
        return len([i for i, result in enumerate(self.data) if result.failure])

    def inconclusive_count(self):
        """
        Amount of inconclusive test cases in this list.

        :return: integer
        """
        inconc_count = len([i for i, result in enumerate(self.data) if result.inconclusive])
        unknown_count = len([i for i, result in enumerate(self.data) if result.get_verdict() ==
                             "unknown"])
        return inconc_count + unknown_count

    def skip_count(self):
        """
        Amount of skipped test cases in this list.

        :return: integer
        """
        return len([i for i, result in enumerate(self.data) if result.skip])

    @property
    def skipped(self):
        return True if self.skip_count() == len(self) else False

    @property
    def inconclusive(self):
        return True if self.inconclusive_count() and not self.failure else False

    @property
    def success(self):
        return True if not self.inconclusive and not self.failure else False

    @property
    def failure(self):
        for item in self.data:
            if item.failure:
                return True
        return False

    def get_verdict(self):
        if self.success:
            return "pass"
        elif self.failure:
            return "fail"
        elif self.skipped:
            return "skip"
        else:
            return "inconclusive"

    def total_duration(self):
        """
        Sum of the durations of the tests in this list.

        :return: integer
        """
        durations = [result.duration for result in self.data]
        return sum(durations)

    def pass_rate(self, include_skips=False, include_inconclusive=False):
        """
        Calculate pass rate for tests in this list.

        :param include_skips: Boolean, if True skipped tc:s will be included. Default is False
        :param include_inconclusive: Boolean, if True inconclusive tc:s will be included.
        Default is False.
        :return: Percentage in format .2f %
        """
        total = self.count()
        success = self.success_count()
        try:
            if include_inconclusive and include_skips:
                val = 100.0*success/total
            elif include_inconclusive:
                inconcs = self.inconclusive_count()
                val = 100.0*success/(total-inconcs)
            elif include_skips:
                skipped = self.skip_count()
                val = 100.0*success/(total-skipped)
            else:
                failures = self.failure_count()
                val = 100.0*success/(failures+success)
        except ZeroDivisionError:
            val = 0
        return format(val, '.2f') + " %"

    def get_summary(self):
        """
        Get a summary of this ResultLists contents as dictionary.

        :return: dictionary
        """
        return {
            "count": self.count(),
            "pass": self.success_count(),
            "fail": self.failure_count(),
            "skip": self.skip_count(),
            "inconclusive": self.inconclusive_count(),
            "duration": self.total_duration(),
        }

    def count(self):
        """
        Return length of this list (amount of Results).

        :return: integer
        """
        return len(self)

    def __len__(self):
        """
        Return length of this list (amount of Results).

        :return: integer
        """
        return len(self.data)

    def __next__(self):
        """
        Get next Result from this list.

        :return: Result
        """
        return self.next()

    def next(self):
        """
        Implementation of next method from Iterator.

        :return: Result
        :raises: StopIteration if IndexError occurs.
        """
        try:
            result = self.data[self.index]
        except IndexError:
            self.index = 0
            raise StopIteration
        self.index += 1
        return result
