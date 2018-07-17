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


ReportHtml module, contains ReportHtml class that implement html reporting.
"""

from datetime import datetime
import os

from yattag import Doc

from icetea_lib.tools.tools import hex_escape_str, get_fw_version, get_fw_name
from icetea_lib.Reports.ReportBase import ReportBase


class ReportHtml(ReportBase):
    """
    ReportHtml class. Uses yattag to generate html reports of results.
    """
    def __init__(self, results):
        ReportBase.__init__(self, results)

    def generate(self, *args, **kwargs):
        """
        Implementation for the generate method defined in ReportBase.
        Generates a html report and saves it.

        :param args: 1 argument, which is the filename
        :param kwargs: 3 keyword arguments with keys 'title', 'heads' and 'refresh'
        :return: Nothing.
        """
        title = kwargs.get("title")
        heads = kwargs.get("heads")
        refresh = kwargs.get("refresh")
        filename = args[0]
        report = self._create(title, heads, refresh, path_start=os.path.dirname(filename))
        ReportHtml.save(report, filename)

    # pylint: disable=too-many-statements
    def _create(self, title, heads, refresh=None, path_start=None):
        """
        Internal create method, uses yattag to generate a html document with result data.

        :param title: Title of report
        :param heads: Headers for report
        :param refresh: If set to True, adds a HTTP-EQUIV="refresh" to the report
        :param path_start: path to file where this is report is to be stored.
        :return: yattag document.
        """
        # TODO: Refactor to make less complex
        doc, tag, text = Doc().tagtext()
        doc.asis('<!DOCTYPE html>')
        heads["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        heads["Pass rate"] = self.results.pass_rate()

        with tag('html'):
            with tag('head'):
                doc.asis(self.head)
                if refresh:
                    doc.asis('<META HTTP-EQUIV="refresh" CONTENT="' + str(refresh) + '">')
            with tag('body', id='body'):
                with tag('h1'):
                    text(title)
                with tag('table'):
                    for head in heads:
                        with tag('tr'):
                            with tag('th', width="100px"):
                                text(head)
                            with tag('td'):
                                text(heads[head])
                    with tag('tr'):
                        with tag('th'):
                            text('Executed')
                        with tag('td'):
                            text(str(self.summary["count"]))
                    with tag('tr'):
                        with tag('th'):
                            text('Pass:')
                        with tag('td'):
                            text(str(self.summary["pass"]))
                    with tag('tr'):
                        with tag('th'):
                            text('Fails:')
                        with tag('td'):
                            text(str(self.summary["fail"]))
                    with tag('tr'):
                        with tag('th'):
                            text('inconclusive:')
                        with tag('td'):
                            text(str(self.summary["inconclusive"]))
                    with tag('tr'):
                        with tag('th'):
                            text('Skip:')
                        with tag('td'):
                            text(str(self.summary["skip"]))
                    with tag('tr'):
                        with tag('th'):
                            text('Duration:')
                        with tag('td'):
                            text(self.duration_to_string(self.summary["duration"]))
                    with tag('tr'):
                        with tag('th'):
                            text('{} version:'.format(get_fw_name()))
                        with tag('td'):
                            text(get_fw_version())

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
                    for result in self.results:
                        if result.success:
                            klass = 'item_pass'
                        elif result.inconclusive:
                            klass = 'item_inconc'
                        else:
                            klass = 'item_fail'
                        with tag('tr', klass='item %s' % klass, onclick='showhide(this)'):
                            with tag('td', width="200px"):
                                text(result.get_tc_name())
                            with tag('td', width="100px"):
                                if result.success:
                                    color = 'green'
                                elif result.failure:
                                    color = 'red'
                                else:
                                    color = 'black'
                                with tag('font', color=color):
                                    text(result.get_verdict())
                            with tag('td', width="350px"):
                                text(hex_escape_str(result.fail_reason))
                            with tag('td', width="300px"):
                                text(result.skip_reason if result.skipped() else "")
                            with tag('td', width="100px"):
                                text(str(result.duration))
                        with tag('tr', klass='info hidden'):
                            with tag('td', colspan="5"):
                                if hasattr(result, 'tc_git_info') and \
                                        result.tc_git_info and \
                                        "scm_link" in result.tc_git_info:
                                    # add tc git info only when available
                                    link = result.tc_git_info['scm_link']
                                    with tag('a', href=link):
                                        text(link)
                                    doc.stag('br')
                                for fil in result.logfiles:
                                    filepath = os.path.relpath(fil, path_start)
                                    with tag('a', href=filepath):
                                        text(filepath)
                                    doc.stag('br')

        return doc.getvalue()

    @staticmethod
    def save(htmldoc, filename):
        """
        Static method which saves htmldoc with filename filename.

        :param htmldoc: yattag Document
        :param filename: file name/path
        :return: Nothing
        """
        with open(filename, 'w') as fil:
            fil.write(htmldoc)

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

        .item_inconc {
            background-color: #FFD733;
        }

        .item_inconc:hover {
            background-color: #FCFF58;
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