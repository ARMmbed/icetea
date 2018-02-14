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

Example output formats:

<?xml version="1.0" encoding="UTF-8"?>
<testsuite>
  <!-- if your classname does not include a dot, the package defaults to "(root)" -->
  <testcase name="my testcase" classname="my package.my classname" time="29">
    <!-- If the test didn't pass, specify ONE of the following 3 cases -->
    <!-- option 1 --> <skipped />
    <!-- option 2 --> <failure message="my failure message">my stack trace</failure>
    <!-- option 3 --> <error message="my error message">my crash report</error>
    <system-out>system-out tag contents</system-out>
    <system-err>system-err tag contents</system-err>
  </testcase>
</testsuite>


<?xml version="1.0" encoding="UTF-8"?>
<testsuite errors="0" failures="0" name="test_searcher.TestVerify-20150721090813"
tests="3" time="0.001">
    <properties/>
    <system-out><![CDATA[]]>	</system-out>
    <system-err><![CDATA[]]>	</system-err>
    <testcase classname="test_searcher.TestVerify" name="test_default" time="0.001"/>
    <testcase classname="test_searcher.TestVerify" name="test_invert" time="0.000"/>
    <testcase classname="test_searcher.TestVerify" name="test_regex" time="0.000"/>
</testsuite>


# just for example
from Result import Result
if __name__=='__main__':
    results = [
                Result({ "testcase": "test-case-A1", "verdict": "PASS", "duration":20}),
                Result({ "testcase": "test-case-A2", "verdict": "PASS", "duration":50}),
                Result({ "testcase": "test-case-A3", "verdict": "PASS", "duration":120}),
                Result({ "testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "
                duration":120}),
                Result({ "testcase": "test-case-A4", "verdict": "INCONCLUSIVE",
                "reason": "WIN blue screen", "duration":1220}),
              ]
    junit = Junit(results)
    junit.save("./../log/result.junit.xml")
"""

from yattag import Doc, indent
from icetea_lib.tools.tools import hex_escape_str
from icetea_lib.Reports.ReportBase import ReportBase


class ReportJunit(ReportBase):
    """
    ReportJunit class. Generates the Junit xml report from results using yattag.
    """
    def __init__(self, results):
        ReportBase.__init__(self, results)

    def generate(self, *args, **kwargs):
        """
        Implementation for generate method from ReportBase. Generates the xml and saves the
        report in Junit xml format.

        :param args: 1 argument, filename is used.
        :param kwargs: Not used
        :return: Nothing
        """
        xmlstr = str(self)
        filename = args[0]
        with open(filename, 'w') as fil:
            fil.write(xmlstr)

        with open(self.get_latest_filename('junit.xml'), "w") as latest_report:
            latest_report.write(xmlstr)

    def __str__(self):
        """
        Generates the xml string for Junit report.

        :return: Report as xml string.
        """
        return ReportJunit.__generate(self.results)

    def to_string(self):
        """
        Generates the xml string for Junit report.

        :return: Report as xml string.
        """
        return str(self)

    # pylint: disable=too-many-branches
    @staticmethod
    def __generate(results):
        """
        Static method which generates the Junit xml string from results

        :param results: Results as ResultList object.
        :return: Junit xml format string.
        """
        doc, tag, text = Doc().tagtext()

        # Counters for testsuite tag info
        count = 0
        fails = 0
        errors = 0
        skips = 0

        for result in results:
            # Loop through all results and count the ones that were not later retried.
            if result.passed() is False:
                if result.retries_left > 0:
                    # This will appear in the list again, move on
                    continue
            count += 1
            if result.passed():
                # Passed, no need to increment anything else
                continue
            elif result.skipped():
                skips += 1
            elif result.was_inconclusive():
                errors += 1
            else:
                fails += 1

        with tag('testsuite',
                 tests=str(count),
                 failures=str(fails),
                 errors=str(errors),
                 skipped=str(skips)):
            for result in results:
                if result.passed() is False and result.retries_left > 0:
                    continue
                class_name = result.get_tc_name()
                models = result.get_dut_models()
                if models:
                    class_name = class_name + "." + models
                name = result.get_toolchain()
                with tag('testcase', classname=class_name, name=name,
                         time=result.get_duration(seconds=True)):
                    if result.stdout:
                        with tag('system-out'):
                            text(result.stdout)
                    if result.passed():
                        continue
                    elif result.skipped():
                        with tag('skipped'):
                            text(result.skip_reason)
                    elif result.was_inconclusive():
                        with tag('error', message=hex_escape_str(result.fail_reason)):
                            text(result.stderr)
                    else:
                        with tag('failure', message=hex_escape_str(result.fail_reason)):
                            text(result.stderr)
        return indent(
            doc.getvalue(),
            indentation=' '*4
        )
