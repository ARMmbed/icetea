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
import mock

from icetea_lib.Plugin.plugins.HttpApi import Api as tc_api
from icetea_lib.TestStepError import TestStepFail


# Schema to make sure header fields are overwritten
schema = {
    "properties": {
        "mergeStrategy": "overwrite"
    }
}


class MockedRequestsResponse():
    def __init__(self, status_code=200, json_data={"key1": "value1"}):
        self.json_data = json_data
        self.status_code = status_code
        self.url = ''
        self.headers = {"head": "ers"}
        self.text = "This is test text"
        self.request = self

    def json(self):
        return self.json_data


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.host = "http://somesite.com"

    @mock.patch("icetea_lib.tools.HTTP.Api.HttpApi.get", side_effect=iter([
        MockedRequestsResponse(
        status_code=200), MockedRequestsResponse(status_code=404),
        MockedRequestsResponse(status_code=404)]))
    @mock.patch("icetea_lib.tools.HTTP.Api.HttpApi.put", side_effect=iter([
        MockedRequestsResponse(
        status_code=200), MockedRequestsResponse(status_code=404),
        MockedRequestsResponse(status_code=404)]))
    @mock.patch("icetea_lib.tools.HTTP.Api.HttpApi.post", side_effect=iter([
        MockedRequestsResponse(
        status_code=200), MockedRequestsResponse(status_code=404),
        MockedRequestsResponse(status_code=404)]))
    @mock.patch("icetea_lib.tools.HTTP.Api.HttpApi.delete", side_effect=iter([
        MockedRequestsResponse(
        status_code=200), MockedRequestsResponse(status_code=404),
        MockedRequestsResponse(status_code=404)]))
    @mock.patch("icetea_lib.tools.HTTP.Api.HttpApi.patch", side_effect=iter([
        MockedRequestsResponse(
        status_code=200), MockedRequestsResponse(status_code=404),
        MockedRequestsResponse(status_code=404)]))
    def test_tcapi(self, mock_patch, mock_delete, mock_post, mock_put, mock_get):
        self.http = tc_api(host=self.host, headers=None, cert=None, logger=None)
        self.assertEquals(self.http.get("/").status_code, 200)
        self.assertEquals(self.http.get("/", expected=200, raiseException=False).status_code, 404)
        with self.assertRaises(TestStepFail):
            self.http.get("/", expected=200, raiseException=True)

        path = "/test"
        data = {"testkey1": "testvalue1"}
        self.assertEquals(self.http.put(path, data).status_code, 200)
        self.assertEquals(self.http.put(path, data, expected=200, raiseException=False).status_code, 404)
        with self.assertRaises(TestStepFail):
            self.http.put(path, data,  expected=200, raiseException=True)

        self.assertEquals(self.http.post(path, json=data).status_code, 200)
        self.assertEquals(self.http.post(path, json=data, expected=200, raiseException=False).status_code, 404)
        with self.assertRaises(TestStepFail):
            self.http.post(path, json=data, expected=200, raiseException=True)

        self.assertEquals(self.http.delete(path).status_code, 200)
        self.assertEquals(self.http.delete(path, expected=200, raiseException=False).status_code, 404)
        with self.assertRaises(TestStepFail):
            self.http.delete(path, expected=200, raiseException=True)

        self.assertEquals(self.http.patch(path, data=data).status_code, 200)
        self.assertEquals(self.http.patch(path, data=data, expected=200, raiseException=False).status_code, 404)
        with self.assertRaises(TestStepFail):
            self.http.patch(path, data=data, expected=200, raiseException=True)


if __name__ == '__main__':
    unittest.main()
