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


Module for the HttpApi default plugin as well as a wrapper-class for the api.
"""

from icetea_lib.Plugin.PluginBase import PluginBase
from icetea_lib.TestStepError import TestStepFail
import icetea_lib.tools.HTTP.Api as HttpApi


class HttpApiPlugin(PluginBase):
    """
    Plugin class implementation
    """
    def __init__(self):
        super(HttpApiPlugin, self).__init__()
        self.logger = None
        self.bench = None

    def init(self, bench=None):
        self.bench = bench
        if self.bench is None:
            raise AttributeError("Bench instance not present!")
        if hasattr(bench, "logger"):
            self.logger = bench.logger

    def get_bench_api(self):
        return {"HttpApi": self.get_tc_api}

    def get_tc_api(self, host, headers=None, cert=None, logger=None):
        '''
        Gets HttpApi wrapped into a neat little package that raises TestStepFail
        if expected status code is not returned by the server.
        Default setting for expected status code is 200. Set expected to None when calling methods
        to ignore the expected status code parameter or
        set raiseException = False to disable raising the exception.
        '''
        if logger is None and self.logger:
            logger = self.logger
        return Api(host, headers, cert, logger)


class Api(HttpApi.HttpApi):
    """
    Wrapper for HttpApi.
    """
    def __init__(self, host, headers, cert, logger):  # pylint: disable=useless-super-delegation
        super(Api, self).__init__(host, headers, cert, logger)

    def _raise_fail(self, response, expected):
        """
        Raise a TestStepFail with neatly formatted error message
        """
        try:
            if self.logger:
                self.logger.error("Status code "
                                  "{} != {}. \n\n "
                                  "Payload: {}".format(response.status_code,
                                                       expected,
                                                       response.content))
            raise TestStepFail("Status code {} != {}.".format(response.status_code, expected))
        except TestStepFail:
            raise
        except:  # pylint: disable=bare-except
            if self.logger:
                self.logger.error("Status code "
                                  "{} != {}. \n\n "
                                  "Payload: {}".format(response.status_code,
                                                       expected,
                                                       "Unable to parse payload"))
            raise TestStepFail("Status code {} != {}.".format(response.status_code, expected))

    # pylint: disable=arguments-differ,too-many-arguments
    def get(self, path, headers=None, params=None, expected=200, raiseException=True, **kwargs):
        response = super(Api, self).get(path, headers, params, **kwargs)
        if expected is not None and response.status_code != expected:
            if raiseException:
                self._raise_fail(response, expected)
        return response

    def post(self, path, data=None, json=None, headers=None, expected=200,
             raiseException=True, **kwargs):
        response = super(Api, self).post(path, data, json, headers, **kwargs)
        if expected is not None and response.status_code != expected:
            if raiseException:
                self._raise_fail(response, expected)
        return response

    def put(self, path, data=None, headers=None, expected=200, raiseException=True, **kwargs):
        response = super(Api, self).put(path, data, headers, **kwargs)
        if expected is not None and response.status_code != expected:
            if raiseException:
                self._raise_fail(response, expected)
        return response

    def delete(self, path, headers=None, expected=200, raiseException=True, **kwargs):
        response = super(Api, self).delete(path, headers, **kwargs)
        if expected is not None and response.status_code != expected:
            if raiseException:
                self._raise_fail(response, expected)
        return response

    def patch(self, path, data=None, headers=None, expected=200, raiseException=True, **kwargs):
        response = super(Api, self).patch(path, data, headers, **kwargs)
        if expected is not None and response.status_code != expected:
            if raiseException:
                self._raise_fail(response, expected)
        return response
