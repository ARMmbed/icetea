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

'''

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
<testsuite errors="0" failures="0" name="test_searcher.TestVerify-20150721090813" tests="3" time="0.001">
    <properties/>
    <system-out><![CDATA[]]>	</system-out>
    <system-err><![CDATA[]]>	</system-err>
    <testcase classname="test_searcher.TestVerify" name="test_default" time="0.001"/>
    <testcase classname="test_searcher.TestVerify" name="test_invert" time="0.000"/>
    <testcase classname="test_searcher.TestVerify" name="test_regex" time="0.000"/>
</testsuite>
'''

from Result import Result
from yattag import Doc, indent
import os
import mbed_clitest.LogManager as LogManager

class Junit:
    def __init__(self, results):
        self.__results = results

    def save(self, filename):
        xmlstr = self.get_xmlstr()
        #print("%s:"%filename)
        #print(xmlstr)
        with open( filename, 'w') as f:
            f.write( xmlstr )
        latest_fileName = os.path.join(LogManager.get_base_dir(), "../latest.junit.xml")
        with open(latest_fileName, "w") as latest_report:
            latest_report.write(xmlstr)

    def get_xmlstr(self):
        return self.__generate(self.__results)

    def __generate(self, results):
        doc, tag, text = Doc().tagtext()
        stat = self.__get_stats(results)
        with tag('testsuite', tests=stat["tests"], failures=stat["failures"], skipped=stat['skipped']):
            for result in results:
                className = ''
                with tag('testcase', classname=className, name=result.getTestcaseName(), time=result.getDuration(seconds=True)):
                    if result.stdout != '':
                        with tag('system-out'):
                            text(result.stdout)
                    if result.getVerdict() != 'pass':
                        if result.getVerdict() == 'skip':
                            with tag('skipped'):
                                text(result.skip_reason)
                        else:
                            with tag('failure', message=result.fail_reason):
                                text(result.stderr)
                                pass
        return indent(
            doc.getvalue(),
            indentation = ' '*4
        )

    def __get_stats(self, results):
        passes = 0
        skipped = 0
        failures = 0
        tests = len(results)
        for result in results:
            if result.getVerdict() == 'pass':
                passes += 1
            elif result.getVerdict() == 'skip':
                skipped += 1
            else:
                failures += 1
        return {'tests': str(tests), 'passes': str(passes), 'skipped': str(skipped), 'failures': str(failures) }

# just for example
if __name__=='__main__':
    results = [
                Result({ "testcase": "test-case-A1", "verdict": "PASS", "duration":20}),
                Result({ "testcase": "test-case-A2", "verdict": "PASS", "duration":50}),
                Result({ "testcase": "test-case-A3", "verdict": "PASS", "duration":120}),
                Result({ "testcase": "test-case-A4", "verdict": "FAIL", "reason": "unknown", "duration":120}),
                Result({ "testcase": "test-case-A4", "verdict": "INCONCLUSIVE", "reason": "WIN blue screen", "duration":1220}),
              ]
    junit = Junit(results)
    junit.save("./../log/result.junit.xml")
