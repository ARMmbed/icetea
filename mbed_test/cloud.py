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

import unittest
import jsonmerge

from Result import Result


#Converter for results to db format
class CloudResult:
    # Constructor for Result line
    def __init__(self):
        pass

    def getResultObject(self):
        return self.__result

    def createResultObject(self, result):
        # create cloud object
        self.__result = {
            'tcid': result.getTestcaseName(),
            'campaign': result.campaign,
            'cre': {
                'user': result.tester
            },
            'job': {
                'id': result.jobId
            },
            'exec': {
                'verdict': result.getVerdict(),
                'duration': result.duration,
                'dut': {
                    'count': result.dutCount,
                    'type': result.dutType,
                    'vendor': result.dutVendor,
                    'model': result.dutModel,
                    'sn': result.dutSn,
                },
                'sut': {
                    'branch': result.branch,
                    'commitId': result.commitId,
                    # 'buildDate': result.build_date,
                    'buildUrl': result.buildUrl,
                    'gitUrl': result.gitUrl,
                    'cut': result.component,  # Component Under Uest
                    'fut': result.feature  # Feature Under Test
                },
                'env': {
                    'framework': {
                        'name': result.fw_name,
                        'ver': result.fw_version
                    }
                }
            }
        }

        self.__testcase = {
            'tcid': result.tc_metadata['name']
        }
        return self.__result


# Cloud connection class
class Cloud:

    __version = 0
    __api = "/api/v"

    def __init__(self, host = "localhost", port=3000, module=None):
        try:
            if module:
                self.module = __import__(module, globals(), fromlist=[""])
                if not hasattr(self.module, "create"):
                    raise ImportError("Cloud module was imported but it does not contain a method to create a client.")
                else:
                    self.client = self.module.create(host, port, CloudResult().createResultObject,
                                                self._convert_to_db_tc_metadata)
            else:
                self.client = None
        except ImportError:
            self.client = None
            raise


    def get_suite(self, suite, options=''):
        if self.client:
            suite = self.client.get_suite(suite, options)
            return suite
        else:
            return None

    def get_campaign_id(self, campaignName):
        if self.client:
            try:
                return self.client.get_campaign_id(campaignName)
            except KeyError:
                raise
        else:
            return None


    def get_campaigns(self):
        if self.client:
            return self.client.get_campaigns()
        else:
            return None


    def get_campaign_names(self):
        if self.client:
            return self.client.get_campaign_names()
        else:
            return None


    def updateTestcase(self, metadata):
        if self.client:
            return self.client.update_testcase(metadata)
        else:
            return None


    # send results to the cloud
    def sendResult(self, result):
        if self.client:
            response_data = self.client.upload_results(result)
            if response_data:
                return response_data
            else:
                return None
        else:
            return None

    #Converter for testcase metadata to db format
    def _convert_to_db_tc_metadata(self, tc_metadata):
        dbMeta = tc_metadata

        status = dbMeta['status']
        del dbMeta['status']
        dbMeta = jsonmerge.merge( dbMeta, {'other_info': {}, 'status': {'value': status}} )

        dbMeta['tcid'] = dbMeta['name']
        del dbMeta['name']

        dbMeta['other_info']['title'] = dbMeta['title']
        del dbMeta['title']


        dbMeta['requirements']['node'] = { 'count': 1 }
        try:
            count = dbMeta['requirements']['duts']['*']['count']
            dbMeta['requirements']['node']['count'] = count
        except:
            pass

        if 'feature' in dbMeta:
            dbMeta['other_info']['features'] = dbMeta['feature']
            del dbMeta['feature']
        else:
            dbMeta['other_info']['features'] = ['unknown']

        dbMeta['other_info']['components'] = dbMeta['component']
        del dbMeta['component']
        #dbMeta['other_info']['purpose'] = dbMeta['purpose']
        #del dbMeta['purpose']

        #type="smoke", # allowed values: installation, compatibility, smoke, regression, acceptance, alpha, beta, destructive, performance
        return dbMeta




class TestVerify(unittest.TestCase):
    def test_newTc(self):
        cloud = Cloud()
        tc_metadata = {
            'name': 'sample',
            'purpose': 'sample test case',
            'title': 'Sample',
            'status': 'unknown'
            }
        result = Result( {"retcode":0, "fw_name":"clitest", "fw_version":"1.2", "tc_metadata":tc_metadata})
        cloud.updateTestcase( result.tc_metadata )

    #def test_sendResult(self):
    #    cloud = Cloud()
    #    tc_metadata = {'name': 'sample2'}
    #    result = Result( retcode=0, framework="clitest:1.2", metadata=tc_metadata, logpath='./log')
    #    cloud.sendResult(result)

if __name__=='__main__':
    unittest.main()
