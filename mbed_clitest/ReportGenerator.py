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

import os
from datetime import datetime
from datetime import timedelta
from yattag import Doc
from prettytable import PrettyTable
from mbed_clitest import LogManager


from mbed_clitest.Result import Result

head = """
<style type="text/css">
    .item {
        border-top: 2px solid #505050;
        border-bottom: 1px solid #A0A0A0;
        border-left: 1px solid #A0A0A0;
        border-right: 1px solid #A0A0A0;
    }

    .item:hover {
        cursor: pointer;
    }

    .item_fail {
        background-color: #FFC0C0;
    }

    .item_fail:hover {
        background-color: #FFCFCF;
    }

    .item_pass {
        background-color: #C0FFC0;
    }

    .item_pass:hover {
        background-color: #CFFFCF;
    }

    .info {
        display: ;
        background: transparent;
        border-left: 1px solid #A0A0A0;
        border-right: 1px solid #A0A0A0;
        border-bottom: 2px solid #505050;
    }

    .hidden {
        display: None;
    }

    .visible_info td {
        padding-left: 1em;
    }

</style>
<script type="text/javascript">
    function showhide(which) {
        n = which.parentNode.rows[which.rowIndex + 1];
        if (n != null) {
            if (n.classList.contains("hidden")) {
                n.classList.remove("hidden")
            }
            else {
                n.classList.add("hidden")
            }
        }
    }
</script>"""

def getSummary(results):
    __count = len(results)
    __pass = 0
    __skip = 0
    __totalExecutionDuration = 0
    for result in results:
        verdict = result.getVerdict()
        __totalExecutionDuration += result.duration
        if verdict == 'pass':  __pass = __pass + 1
        if verdict == 'skip':  __skip = __skip + 1
    __fail = __count - __pass - __skip
    return {
        "count": __count,
        "pass": __pass,
        "fail": __fail,
        "skip": __skip,
        "duration": __totalExecutionDuration,
    }

def durationToStr(seconds):
    delta = timedelta(seconds=seconds)
    return str(delta)

def ReportGenerator(title, heads, results):
    global head
    doc, tag, text = Doc().tagtext()

    doc.asis('<!DOCTYPE html>')
    summary = getSummary(results)

    heads["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with tag('html'):
        with tag('head'):
            doc.asis(head)
        with tag('body', id = 'body'):
            with tag('h1'):
                text(title)
            with tag('table'):
                for head in heads:
                    with tag('tr'):
                        with tag('th', width="100px"):
                            text(head)
                        with tag('td'):
                            text( heads[head] )
                with tag('tr'):
                    with tag('th'):
                        text('Executed')
                    with tag('td'):
                        text( str(summary["count"]) )
                with tag('tr'):
                    with tag('th'):
                        text('Pass:')
                    with tag('td'):
                        text( str(summary["pass"]) )
                with tag('tr'):
                    with tag('th'):
                        text('Fails:')
                    with tag('td'):
                        text( str(summary["fail"]) )
                with tag('tr'):
                    with tag('th'):
                        text('Skip:')
                    with tag('td'):
                        text( str(summary["skip"]) )
                with tag('tr'):
                    with tag('th'):
                        text('Duration:')
                    with tag('td'):
                        text( durationToStr(summary["duration"]) )

            with tag('table', style='border-collapse: collapse;'):
                with tag('tr'):
                    with tag('th'):
                        text("Test Case")
                    with tag('th'):
                        text("Verdict")
                    with tag('th'):
                        text("Fail Reason")
                    with tag('th'):
                        text("Skip Reason")
                    with tag('th'):
                        text("Duration")
                for result in results:
                    verdict = result.getVerdict()
                    cl = 'item_pass' if verdict == 'pass' else 'item_fail'
                    with tag('tr', klass='item %s' % cl, onclick='showhide(this)'):
                        with tag('td', width="200px"):
                            text(result.getTestcaseName())
                        with tag('td', width="70px"):
                            color = 'green' if verdict == 'pass' else 'red'
                            with tag('font', color=color):
                                text(verdict)
                        with tag('td', width="300px"):
                            text(result.fail_reason)
                        with tag('td', width="300px"):
                            text(result.skip_reason)
                        with tag('td', width="100px"):
                            text(str(result.duration))
                    with tag('tr', klass='info hidden'):
                        with tag('td', colspan="5"):
                            if hasattr(result, 'tc_git_info') and result.tc_git_info and "scm_link" in result.tc_git_info:
                                link = result.tc_git_info['scm_link']
                                with tag('a', href=link):
                                    text(link)
                                doc.stag('br')
                            for f in result.logfiles:
                                with tag('a', href=f):
                                    text(f)
                                doc.stag('br')

    return doc.getvalue()

def StoreReport(htmldoc, filename):
    f = open( filename, 'w' )
    f.write( htmldoc )
    # Create redirecting latest result page to log directory
    latest_report_filename = os.path.join(LogManager.get_base_dir(), "../latest.html")
    with open(latest_report_filename, "w") as latest_report:
        latest_report.write('<html><head><meta http-equiv="refresh" content="0; url=../%s" /></head></html>' % filename)

def PrintReport( results = [] ):
    # Generate TC result table
    x = PrettyTable(["Testcase", "Verdict", "Fail Reason", "Skip Reason", "duration"])
    x.align["Testcase"] = "l" # Left align city names
    summary = getSummary(results)
    for result in results:
        x.add_row([ result.getTestcaseName(), result.getVerdict(), result.fail_reason[:30], str(result.skip_reason), str(result.duration)])
    print(x)

    # Generate Summary table
    x = PrettyTable(['Summary',''])
    finalVerdict = "FAIL"
    if summary["fail"] == 0:
        finalVerdict = "PASS"
    x.add_row(["Final Verdict", finalVerdict])
    x.add_row(["count", str(summary["count"])])

    x.add_row(["pass", str(summary["pass"])])
    if summary["fail"]>0:
        x.add_row(["fail", str(summary["fail"])])
    if summary["skip"]>0:
        x.add_row(["skip", str(summary["skip"])])
    x.add_row(["Duration", durationToStr(summary["duration"])])
    print(x)

if __name__ == '__main__':
    htmldoc = ReportGenerator('Results',
        {   "Date" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Build': 'build-a',
        },
        [
            { "testcase": "test-case-A1", "verdict": "PASS"},
            { "testcase": "test-case-A2", "verdict": "PASS"},
            { "testcase": "test-case-A3", "verdict": "FAIL", "reason": "unknown"},
        ]
    )
    StoreReport( 'report.html', htmldoc )
