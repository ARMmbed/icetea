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
import mock
import jsonmerge
from requests.exceptions import RequestException
from mbed_clitest.Extensions.HTTP.Api import HttpApi
from mbed_clitest.TestStepError import TestStepFail
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

    def json(self):
        return self.json_data


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.headers = {"accept-charset": "utf-8", "accept": "application/json"}
        self.host = "http://somesite.com"
        self.cert = "/path/to/cert.pem"


    def test_init(self):
        self.http = HttpApi(self.host)
        self.assertEquals(self.http.host, self.host, "HTTPApi not set up correctly, host names don't match")
        self. http = HttpApi(self.host, self.headers, self.cert)
        self.assertDictEqual(self.headers, self.http.defaultHeaders, "HttpApi not set up correctly, headers not ok")
        self.assertEquals(self.cert, self.http.cert)

    # Test both new header field and overwrite
    def test_header_set(self):
        self.http = HttpApi(self.host, self.headers)
        #Test overwriting headers
        self.http.set_header("accept", "text/plain")
        self.assertEquals(self.http.defaultHeaders["accept"], "text/plain")
        #Test setting new headers
        self.http.set_header("accept-language", "en-US")
        self.assertEquals(self.http.defaultHeaders["accept-language"], "en-US")


    def test_header_merge(self):
        self.http = HttpApi(self.host, self.headers)
        headers = {"accept": "text/plain", "content-length": 348}
        ref = {"accept-charset": "utf-8", "accept": "application/json", "accept": "text/plain", "content-length": 348}
        merger = jsonmerge.Merger(schema)
        heads = merger.merge(self.headers, headers)
        #Assert that new headers are the same as reference
        self.assertDictEqual(heads, ref, msg="Header merging does not work correctly")


    @mock.patch("mbed_clitest.Extensions.HTTP.Api.requests.get")
    def test_get(self, mock_requests_get):
        #First test successfull get request. Assert if get was called
        self.http = HttpApi(self.host)
        path = "/test"
        mock_requests_get.side_effect = [MockedRequestsResponse(), RequestException("Exception raised correctly"),
                                         MockedRequestsResponse(404), MockedRequestsResponse(200),
                                         MockedRequestsResponse(201)]
        resp = self.http.get(path)
        self.assertTrue(mock_requests_get.called, "Failed to call requests.get")
        path = "/exception"
        #Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.get exception not raised properly"):
            self.http.get(path)



    @mock.patch("mbed_clitest.Extensions.HTTP.Api.requests.post")
    def test_post(self, mock_requests_post):
        #Successfull post
        self.http = HttpApi(self.host)
        path = "/test"
        json = {"testkey1": "testvalue1"}
        mock_requests_post.side_effect = [MockedRequestsResponse(), RequestException("Exception raised correctly"),
                                          MockedRequestsResponse(404), MockedRequestsResponse(200),
                                          MockedRequestsResponse(201)]
        resp = self.http.post(path, json=json)
        self.assertTrue(mock_requests_post.called, "Failed to call requests.post")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.post exception not raised properly"):
            self.http.post(path, json=json)



    @mock.patch("mbed_clitest.Extensions.HTTP.Api.requests.put")
    def test_put(self, mock_requests_put):
        #Successfull put
        self.http = HttpApi(self.host)
        path = "/test"
        data = {"testkey1": "testvalue1"}
        mock_requests_put.side_effect = [MockedRequestsResponse(), RequestException("Exception raised correctly"),
                                          MockedRequestsResponse(404), MockedRequestsResponse(200),
                                          MockedRequestsResponse(201)]
        resp = self.http.put(path, data=data)
        self.assertTrue(mock_requests_put.called, "Failed to call requests.put")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.put exception not raised properly"):
            self.http.put(path, data=data)


    @mock.patch("mbed_clitest.Extensions.HTTP.Api.requests.delete")
    def test_delete(self, mock_requests_delete):
        #Successfull delete
        self.http = HttpApi(self.host)
        path = "/test"
        mock_requests_delete.side_effect = [MockedRequestsResponse(), RequestException("Exception raised correctly"),
                                          MockedRequestsResponse(404), MockedRequestsResponse(200),
                                          MockedRequestsResponse(200)]
        resp = self.http.delete(path)
        self.assertTrue(mock_requests_delete.called, "Failed to call requests.delete")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.delete exception not raised properly"):
            self.http.delete(path)



if __name__ == '__main__':
    unittest.main()
