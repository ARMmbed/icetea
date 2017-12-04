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

import unittest
import os
import copy

from icedtea_lib.tools.tools import remove_empty_from_dict


def create_result_object(result):
    # create cloud object
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
                'cut': result.component, # Component Under Uest
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

    if len(result.dut_vendor) > 0 and result.dut_vendor[0]:
        _result["exec"]["dut"]["vendor"] = result.dut_vendor[0]
    if len(result.dut_models) > 0 and result.dut_models[0]:
        _result["exec"]["dut"]["model"] = result.dut_models[0]

    if len(result.dut_models) == 1 and len(result.dut_resource_id) == 1:
        _result["exec"]["dut"]["sn"] = result.dut_resource_id[0]

    return remove_empty_from_dict(_result)


def append_logs_to_result_object(result_obj, result):
    logs = result.has_logs()
    result_obj["exec"]["logs"] = []
    if logs and len(result.logfiles) > 0:
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
                    with open(log, "r") as file:
                        data = file.read()
                    dic = {"data": data, "name": name, "from": typ}
                    result_obj["exec"]["logs"].append(dic)
                except OSError as e:
                    pass
            else:
                continue


def create_result_object_with_logs(result):
    _result = create_result_object(result)
    append_logs_to_result_object(_result, result)
    return _result


# Cloud connection class
class Cloud(object):

    __version = 0
    __api = "/api/v"

    def __init__(self, host=None, module=None, result_converter=None, tc_converter=None,
                 logger=None, args=None):
        self.args = args
        self.logger = logger

        # Try to fetch cloud provider from ENV variables
        if not module:
            module = os.environ.get("ICEDTEA_CLOUD_PROVIDER", 'opentmi-client')
        self.module = __import__(module, globals(), fromlist=[""])

        # Parse host and port from combined host
        if host is None:
            host = self._resolve_host()
        host, port = self._find_port(host)

        # Ensure result converter has an implementation
        resconv = result_converter
        if resconv is None:
            resconv = create_result_object_with_logs if (
            self.args and self.args.with_logs) else create_result_object

        # Ensure testcase converter has an implementation
        tc_conv = tc_converter if tc_converter else self._convert_to_db_tc_metadata

        # Setup client
        try:
            self._client = self.module.create(host, port, resconv, tc_conv)
            self._client.set_logger(logger)
        except AttributeError:
            raise ImportError("Cloud module was imported but it does not "
                              "contain a method to create a client.")

    def _resolve_host(self):
        node_name = os.environ.get('NODE_NAME', '')
        if node_name.startswith('aws'):
            _host = os.environ.get('OPENTMI_ADDRESS_PRIVATE', None)
        else:
            _host = os.environ.get('OPENTMI_ADDRESS_PUBLIC', None)

        if _host is None:
            _host = os.environ.get("ICEDTEA_CLOUD_HOST", "localhost:3000")

        return _host

    def _find_port(self, host):
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
        return self._client.get_suite(suite, options)

    def get_campaign_id(self, campaign_name):
        return self._client.get_campaign_id(campaign_name)

    def get_campaigns(self):
        return self._client.get_campaigns()

    def get_campaign_names(self):
        return self._client.get_campaign_names()

    def update_testcase(self, metadata):
        return self._client.update_testcase(metadata)

    # send results to the cloud
    def send_result(self, result):
        response_data = self._client.upload_results(result)
        if response_data:
            if self.logger is not None:
                self.logger.info("Results sent to the server. ID: {}".format(response_data["_id"]))
            return response_data
        else:
            if self.logger is not None:
                self.logger.info("Server didn't respond or client initialization has failed.")
            return None

    def _convert_to_db_tc_metadata(self, tc_metadata):
        dbMeta = copy.deepcopy(tc_metadata)

        # tcid is a mandatory field, it should throw an error if it is missing
        dbMeta['tcid'] = dbMeta['name']
        del dbMeta['name']

        # Encapsulate current status inside dictionary
        if 'status' in dbMeta:
            status = dbMeta['status']
            del dbMeta['status']
            dbMeta['status'] = {'value': status}

        # Node and dut information
        if 'requirements' in dbMeta:
            dbMeta['requirements']['node'] = {'count': 1}
            try:
                count = dbMeta['requirements']['duts']['*']['count']
                dbMeta['requirements']['node']['count'] = count
            except:
                pass

        # Collect and pack other info from meta
        dbMeta['other_info'] = {}
        if 'title' in dbMeta:
            dbMeta['other_info']['title'] = dbMeta['title']
            del dbMeta['title']

        if 'feature' in dbMeta:
            dbMeta['other_info']['features'] = dbMeta['feature']
            del dbMeta['feature']
        else:
            dbMeta['other_info']['features'] = ['unknown']

        if 'component' in dbMeta:
            dbMeta['other_info']['components'] = dbMeta["component"]
            del dbMeta['component']

        return dbMeta


if __name__ == '__main__':
    unittest.main()
