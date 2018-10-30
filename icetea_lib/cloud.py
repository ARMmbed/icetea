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

Cloud adapter for Icetea.
"""

import unittest
import os
import copy

from icetea_lib.tools.tools import remove_empty_from_dict, get_pkg_version


def create_result_object(result):
    """
    Create cloud result object from Result.

    :param result: Result
    :return: dictionary
    """
    _result = {
        'tcid': result.get_tc_name(),
        'campaign': result.campaign,
        'cre': {
            'user': result.tester
        },
        'job': {
            'id': result.job_id
        },
        'exec': {
            'verdict': result.get_verdict(),
            'duration': result.duration,
            'note': result.get_fail_reason(),
            'dut': {
                'count': result.dut_count,
                'type': result.dut_type
            },
            'sut': {
                'branch': result.build_branch,
                'commitId': result.buildcommit,
                'buildDate': result.build_date,
                'buildSha1': result.build_sha1,
                'buildUrl': result.build_url,
                'gitUrl': result.build_git_url,
                'cut': result.component,  # Component Under Uest
                'fut': result.feature    # Feature Under Test
            },
            'env': {
                'framework': {
                    'name': result.fw_name,
                    'ver': result.fw_version
                }
            },
            "logs": []
        }
    }

    if result.dut_resource_id:
        _result["exec"]["dut"]["sn"] = result.dut_resource_id

    if result.dut_vendor and result.dut_vendor[0]:
        _result["exec"]["dut"]["vendor"] = result.dut_vendor[0]
    if result.dut_models and result.dut_models[0]:
        _result["exec"]["dut"]["model"] = result.dut_models[0]
    # pylint: disable=len-as-condition
    if len(result.dut_models) == 1 and len(result.dut_resource_id) == 1:
        _result["exec"]["dut"]["sn"] = result.dut_resource_id[0]

    return remove_empty_from_dict(_result)


def append_logs_to_result_object(result_obj, result):
    """
    Append log files to cloud result object from Result.

    :param result_obj: Target result object
    :param result: Result
    :return: Nothing, modifies result_obj in place.
    """
    logs = result.has_logs()
    result_obj["exec"]["logs"] = []
    if logs and result.logfiles:
        for log in logs:
            typ = None
            parts = log.split(os.sep)
            if "bench" in parts[len(parts) - 1]:
                typ = "framework"
            # elif "Dut" in parts[len(parts)-1]:
            #    typ = "dut"

            if typ is not None:
                name = parts[len(parts) - 1]
                try:
                    with open(log, "r") as file_name:
                        data = file_name.read()
                    dic = {"data": data, "name": name, "from": typ}
                    result_obj["exec"]["logs"].append(dic)
                except OSError:
                    pass
            else:
                continue


def create_result_object_with_logs(result):
    """
    Create the result dictionary and append logs as well.
    :param result: Result
    :return: dictionary
    """
    _result = create_result_object(result)
    append_logs_to_result_object(_result, result)
    return _result


# Cloud connection class
class Cloud(object):
    """
    Cloud adapter. Originally designed to work with python client for Opentmi.
    """

    __version = 0
    __api = "/api/v"

    @staticmethod
    def _convert_to_db_tc_metadata(tc_metadata):
        """
        Convert tc_metadata to match Opentmi metadata format
        :param tc_metadata: metadata as dict
        :return: converted metadata
        """
        db_meta = copy.deepcopy(tc_metadata)

        # tcid is a mandatory field, it should throw an error if it is missing
        db_meta['tcid'] = db_meta['name']
        del db_meta['name']

        # Encapsulate current status inside dictionary
        if 'status' in db_meta:
            status = db_meta['status']
            del db_meta['status']
            db_meta['status'] = {'value': status}

        # Node and dut information
        if 'requirements' in db_meta:
            db_meta['requirements']['node'] = {'count': 1}
            try:
                count = db_meta['requirements']['duts']['*']['count']
                db_meta['requirements']['node']['count'] = count
            except KeyError:
                pass

        # Collect and pack other info from meta
        db_meta['other_info'] = {}
        if 'title' in db_meta:
            db_meta['other_info']['title'] = db_meta['title']
            del db_meta['title']

        if 'feature' in db_meta:
            db_meta['other_info']['features'] = db_meta['feature']
            del db_meta['feature']
        else:
            db_meta['other_info']['features'] = ['unknown']

        if 'component' in db_meta:
            db_meta['other_info']['components'] = db_meta["component"]
            del db_meta['component']

        return db_meta

    # pylint: disable=too-many-arguments
    def __init__(self, host=None, module=None, result_converter=None, tc_converter=None,
                 logger=None, args=None):

        self.args = args
        self.logger = logger

        # Try to fetch cloud provider from ENV variables
        if not module:
            module = os.environ.get("ICETEA_CLOUD_PROVIDER", 'opentmi-client')
        self.module = __import__(module, globals(), fromlist=[""])

        version = get_pkg_version(module)
        if self.logger and version is not None:
            self.logger.info("using {} version {}".format(module, version))
        else:
            if self.logger:
                self.logger.warning("Unable to parse cloud module version")

        # Parse host and port from combined host
        if host is None:
            host = self._resolve_host()
        host, port = self._find_port(host)

        # Ensure result converter has an implementation
        resconv = result_converter
        if resconv is None:
            if self.args and self.args.with_logs:
                resconv = create_result_object_with_logs
            else:
                resconv = create_result_object

        # Ensure testcase converter has an implementation
        tc_conv = tc_converter if tc_converter else self._convert_to_db_tc_metadata

        # Setup client
        try:
            self._client = self.module.create(host, port, resconv, tc_conv)
            self._client.set_logger(logger)
        except AttributeError:
            raise ImportError("Cloud module was imported but it does not "
                              "contain a method to create a client.")

    def _resolve_host(self):  # pylint: disable=no-self-use
        """
        Resolve cloud provider host name. Defaults to environment variables
        OPENTMI_ADDRESS_PRIVATE or OPENTMI_ADDRESS_PUBLIC if environment variable NODE_NAME
        starts with 'aws'. Otherwise gets ICETEA_CLOUD_HOST environment variable OR
        localhost:3000 if that one does not exist.
        :return: Cloud host information
        """
        node_name = os.environ.get('NODE_NAME', '')
        if node_name.startswith('aws'):
            _host = os.environ.get('OPENTMI_ADDRESS_PRIVATE', None)
        else:
            _host = os.environ.get('OPENTMI_ADDRESS_PUBLIC', None)

        if _host is None:
            _host = os.environ.get("ICETEA_CLOUD_HOST", "localhost:3000")

        return _host

    def _find_port(self, host):  # pylint: disable=no-self-use
        """
        Finds port number from host. Defaults to 3000 if not found
        :param host: host as string
        :return: (host, port)
        """
        ind = host.rfind(":")
        if ind != -1:
            try:
                port = int(host[ind + 1:])
                host = host[:ind]
            except ValueError:
                port = 3000
        else:
            port = 3000
        return host, port

    def get_suite(self, suite, options=''):
        """
        Calls cloud client method get_suite
        :param suite: passed to cloud client
        :param options: passed to cloud client
        :return: _client.get_suite(suite, options)
        """
        return self._client.get_suite(suite, options)

    def get_campaign_id(self, campaign_name):
        """
        Calls client method get_campaign_id
        :param campaign_name: passed to cloud client
        :return: _client.get_campaign_id(campaign_name)
        """
        return self._client.get_campaign_id(campaign_name)

    def get_campaigns(self):
        """
        Calls client method get_campaigns
        :return: _client.get_campaigns()
        """
        return self._client.get_campaigns()

    def get_campaign_names(self):
        """
        Calls client method get_campaign_names
        :return: _client.get_campaign_names()
        """
        return self._client.get_campaign_names()

    def update_testcase(self, metadata):
        """
        Updates test case metadata with
        :param metadata: Test case metadata
        :return: _client.update_testcase(metadata)
        """
        return self._client.update_testcase(metadata)

    def send_result(self, result):
        """
        Send results to the cloud
        :param result: result dictionary
        :return: response from _client.upload_results(result) or None if something went wrong
        """
        response_data = self._client.upload_results(result)
        if response_data:
            if self.logger is not None:
                self.logger.info("Results sent to the server. ID: {}".format(response_data["_id"]))
            return response_data
        else:
            if self.logger is not None:
                self.logger.info("Server didn't respond or client initialization has failed.")
            return None




if __name__ == '__main__':
    unittest.main()
