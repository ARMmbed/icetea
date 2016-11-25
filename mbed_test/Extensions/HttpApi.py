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
HTTP API extension for use with mbed test.
'''
from mbed_test.Extensions.HTTP import Api as api
from mbed_test.TestStepError import TestStepFail


class HttpApi():
    def __init__(self, bench):
        self.bench = bench
        self.logger = bench.logger
        setattr(self.bench, "HttpApi", self.getTestcaseApi)


    def getTestcaseApi(self, host, headers=None, cert=None, logger=None):
        '''
        Gets HttpApi wrapped into a neat little package that raises TestStepFail if expected status code is not returned
        by the server. Default setting for expected status code is 200. Set expected to None when calling methods
        to ignore the expected status code parameter or set raiseException = False to disable raising the exception.
        '''
        return Api(host, headers, cert, self.logger) if not logger else Api(host, headers, cert, logger)

class Api(api.HttpApi):
    def __init__(self, host, headers, cert, logger):
        super(self.__class__, self).__init__(host, headers, cert, logger)

    def get(self, path, headers=None, params=None, expected=200, raiseException=True, **kwargs):
        response = super(Api, self).get(path, headers, params, **kwargs)
        try:
            self.logger.debug("Server response content: {}".format(response.json()))
        except ValueError:
            pass
        if expected is not None and response.status_code != expected:
            if raiseException:
                raise TestStepFail("Status code {} != {}".format(response.status_code, expected))
            else:
                self.logger.debug("Status code {} != {}".format(response.status_code, expected))
                return response
        else:
            return response

    def post(self, path, data=None, json=None, headers=None, expected=200, raiseException=True,**kwargs):
        response = super(self.__class__, self).post(path, data, json, headers, **kwargs)
        try:
            self.logger.debug("Server response content: {}".format(response.json()))
        except ValueError:
            pass
        if expected is not None and response.status_code != expected:
            if raiseException:
                raise TestStepFail("Status code {} != {}".format(response.status_code, expected))
            else:
                self.logger.debug("Status code {} != {}".format(response.status_code, expected))
                return response
        else:
            return response

    def put(self, path, data=None, headers=None, expected=200, raiseException=True, **kwargs):
        response = super(self.__class__, self).put(path, data, headers, **kwargs)
        try:
            self.logger.debug("Server response content: {}".format(response.json()))
        except ValueError:
            pass
        if expected is not None and response.status_code != expected:
            if raiseException:
                raise TestStepFail("Status code {} != {}".format(response.status_code, expected))
            else:
                self.logger.debug("Status code {} != {}".format(response.status_code, expected))
                return response
        else:
            return response

    def delete(self, path, headers=None, expected=200, raiseException=True, **kwargs):
        response = super(self.__class__, self).delete(path, headers, **kwargs)
        try:
            self.logger.debug("Server response content: {}".format(response.json()))
        except ValueError:
            pass
        if expected is not None and response.status_code != expected:
            if raiseException:
                raise TestStepFail("Status code {} != {}".format(response.status_code, expected))
            else:
                self.logger.debug("Status code {} != {}".format(response.status_code, expected))
                return response
        else:
            return response
