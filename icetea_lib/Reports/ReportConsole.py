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

ReportConsole module, contains the ReportConsole class which implements reporting to console.
"""

from prettytable import PrettyTable
from icetea_lib.Reports.ReportBase import ReportBase
from icetea_lib.tools.tools import hex_escape_str


class ReportConsole(ReportBase):
    """
    ReportConsole class, implements generating and printing reports to the console using print
    method and PrettyTable module.
    """
    def __init__(self, results):
        ReportBase.__init__(self, results)

    def generate(self, *args, **kwargs):
        """
        Generates and prints the console report, which consists of a table of test cases ran as
        well as a summary table with passrate, number of test cases and statistics on
        passed/failed/inconclusive/skipped cases.

        :param args: arguments, not used
        :param kwargs: keyword arguments, not used
        :return: Nothing
        """
        # Generate TC result table
        table = PrettyTable(
            ["Testcase", "Verdict", "Fail Reason", "Skip Reason", "platforms", "duration",
             "Retried"])
        for result in self.results:
            table.add_row([
                result.get_tc_name(),
                result.get_verdict(),
                hex_escape_str(result.fail_reason)[:60],
                str(result.skip_reason) if result.skipped() else "",
                result.get_dut_models(),
                str(result.duration),
                "Yes" if result.retries_left != 0 else "No"
            ])
            # Print to console
        print(table)  # pylint: disable=superfluous-parens

        # Generate Summary table
        table = PrettyTable(['Summary', ''])
        final_verdict = "FAIL"
        if self.summary["fail"] == 0 and self.summary["inconclusive"] == 0:
            final_verdict = "PASS"
        elif self.results.clean_inconcs() and not self.results.clean_fails():
            final_verdict = "INCONCLUSIVE"
        elif self.summary["fail"] + self.summary["inconclusive"] == self.summary["retries"]:
            final_verdict = "PASS"
        table.add_row(["Final Verdict", final_verdict])
        table.add_row(["count", str(self.summary["count"])])

        table.add_row(["passrate", self.results.pass_rate()])
        table.add_row(["passrate excluding retries", self.results.pass_rate(include_retries=False)])
        if self.summary["pass"] > 0:
            table.add_row(["pass", str(self.summary["pass"])])
        if self.summary["fail"] > 0:
            table.add_row(["fail", str(self.summary["fail"])])
        if self.summary["skip"] > 0:
            table.add_row(["skip", str(self.summary["skip"])])
        if self.summary["inconclusive"] > 0:
            table.add_row(["inconclusive", str(self.summary["inconclusive"])])
        table.add_row(["Duration", self.duration_to_string(self.summary["duration"])])
        # Print to console
        print(table)  # pylint: disable=superfluous-parens
