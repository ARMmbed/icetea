# pylint: disable=missing-docstring

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
import jsonmerge
import mock

from requests.exceptions import RequestException
from requests import Response

from icetea_lib.tools.HTTP.Api import HttpApi

# Schema to make sure header fields are overwritten
SCHEMA = {
    "properties": {
        "mergeStrategy": "overwrite"
    }
}


class MockedRequestsResponse(object):  # pylint: disable=too-few-public-methods
    def __init__(self, status_code=200, json_data=None):
        self.json_data = json_data if json_data else {"key1": "value1"}
        self.status_code = status_code
        self.url = ''
        self.headers = {"head": "ers"}
        self.text = "This is test text"
        self.request = self

    def json(self):
        return self.json_data


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.headers = {"accept-charset": "utf-8", "accept": "application/json"}
        self.host = "http://somesite.com"
        self.host2 = "http://somesite.com/api/"
        self.cert = "/path/to/cert.pem"
        self.http = None

    def test_init(self):
        self.http = HttpApi(self.host)
        self.assertEquals(self.http.host, self.host,
                          "HTTPApi not set up correctly, host names don't match")
        self. http = HttpApi(self.host, self.headers, self.cert)
        self.assertDictEqual(self.headers, self.http.defaultHeaders,
                             "HttpApi not set up correctly, headers not ok")
        self.assertEquals(self.cert, self.http.cert)

    # Test both new header field and overwrite
    def test_header_set(self):
        self.http = HttpApi(self.host, self.headers)
        # Test overwriting headers
        self.http.set_header("accept", "text/plain")
        self.assertEquals(self.http.defaultHeaders["accept"], "text/plain")
        # Test setting new headers
        self.http.set_header("accept-language", "en-US")
        self.assertEquals(self.http.defaultHeaders["accept-language"], "en-US")

    def test_header_merge(self):
        self.http = HttpApi(self.host, self.headers)
        headers = {"accept": "text/plain", "content-length": 348}
        ref = {"accept-charset": "utf-8", "accept": "text/plain", "content-length": 348}
        merger = jsonmerge.Merger(SCHEMA)
        heads = merger.merge(self.headers, headers)
        # Assert that new headers are the same as reference
        self.assertDictEqual(heads, ref, msg="Header merging does not work correctly")

    @mock.patch("icetea_lib.tools.HTTP.Api.requests.get")
    def test_url_combine(self, mock_get):
        self.http = HttpApi(self.host2)
        self.http.get("/test_path")
        mock_get.assert_called_with(self.host2 + "test_path", {}, headers={})
        mock_get.reset_mock()

        self.http.get("test_path")
        mock_get.assert_called_with(self.host2 + "test_path", {}, headers={})
        mock_get.reset_mock()

        self.http = HttpApi(self.host)
        self.http.get("test_path")
        mock_get.assert_called_with(self.host + "/test_path", {}, headers={})
        mock_get.reset_mock()

        self.http = HttpApi(self.host)
        self.http.get("/test_path")
        mock_get.assert_called_with(self.host + "/test_path", {}, headers={})

    @mock.patch("icetea_lib.tools.HTTP.Api.requests.get")
    def test_get(self, mock_requests_get):
        # First test successfull get request. Assert if get was called
        self.http = HttpApi(self.host)
        path = "/test"
        mock_requests_get.side_effect = iter([MockedRequestsResponse(),
                                              RequestException("Exception raised correctly"),
                                              MockedRequestsResponse(404),
                                              MockedRequestsResponse(200),
                                              MockedRequestsResponse(201)])
        resp = self.http.get(path)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_get.called, "Failed to call requests.get")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.get exception not raised properly"):
            self.http.get(path)

        mock_requests_get.reset_mock()
        path2 = "v2/"
        resp = self.http.get(path2)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_get.called, "Failed to call requests.get")

        mock_requests_get.reset_mock()
        path3 = "/v3/"
        self.http = HttpApi(self.host2)
        resp = self.http.get(path3)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_get.called, "Failed to call requests.get")

    @mock.patch("icetea_lib.tools.HTTP.Api.requests.post")
    def test_post(self, mock_requests_post):
        # Successfull post
        self.http = HttpApi(self.host)
        path = "/test"
        json = {"testkey1": "testvalue1"}
        mock_requests_post.side_effect = iter([MockedRequestsResponse(),
                                               RequestException("Exception raised correctly"),
                                               MockedRequestsResponse(404),
                                               MockedRequestsResponse(200),
                                               MockedRequestsResponse(201)])
        resp = self.http.post(path, json=json)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_post.called, "Failed to call requests.post")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.post exception not raised properly"):
            self.http.post(path, json=json)

        mock_requests_post.reset_mock()
        path2 = "v2/"
        resp = self.http.post(path2, json=json)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_post.called, "Failed to call requests.post")

        mock_requests_post.reset_mock()
        path3 = "/v3/"
        self.http = HttpApi(self.host2)
        resp = self.http.post(path3, json=json)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_post.called, "Failed to call requests.post")

    @mock.patch("icetea_lib.tools.HTTP.Api.requests.put")
    def test_put(self, mock_requests_put):
        # Successfull put
        self.http = HttpApi(self.host)
        path = "/test"
        data = {"testkey1": "testvalue1"}
        mock_requests_put.side_effect = iter([MockedRequestsResponse(),
                                              RequestException("Exception raised correctly"),
                                              MockedRequestsResponse(404),
                                              MockedRequestsResponse(200),
                                              MockedRequestsResponse(201)])
        resp = self.http.put(path, data=data)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_put.called, "Failed to call requests.put")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.put exception not raised properly"):
            self.http.put(path, data=data)

        mock_requests_put.reset_mock()
        path2 = "v2/"
        resp = self.http.put(path2, data=data)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_put.called, "Failed to call requests.put")

        mock_requests_put.reset_mock()
        path3 = "/v3/"
        self.http = HttpApi(self.host2)
        resp = self.http.put(path3, data=data)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_put.called, "Failed to call requests.put")

    @mock.patch("icetea_lib.tools.HTTP.Api.requests.patch")
    def test_patch(self, mock_requests_patch):
        # Successfull patch
        self.http = HttpApi(self.host)
        path = "/test"
        data = {"testkey1": "testvalue1"}
        mock_requests_patch.side_effect = iter([MockedRequestsResponse(),
                                                RequestException("Exception raised correctly"),
                                                MockedRequestsResponse(404),
                                                MockedRequestsResponse(200),
                                                MockedRequestsResponse(201)])
        resp = self.http.patch(path, data=data)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_patch.called, "Failed to call requests.patch")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException, msg="request.patch exception not raised properly"):
            self.http.patch(path, data=data)

        mock_requests_patch.reset_mock()
        path2 = "v2/"
        resp = self.http.patch(path2, data=data)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_patch.called, "Failed to call requests.patch")

        mock_requests_patch.reset_mock()
        path3 = "/v3/"
        self.http = HttpApi(self.host2)
        resp = self.http.patch(path3, data=data)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_patch.called, "Failed to call requests.patch")

    @mock.patch("icetea_lib.tools.HTTP.Api.requests.delete")
    def test_delete(self, mock_requests_delete):
        # Successfull delete
        self.http = HttpApi(self.host)
        path = "/test"
        mock_requests_delete.side_effect = iter([MockedRequestsResponse(),
                                                 RequestException("Exception raised correctly"),
                                                 MockedRequestsResponse(404),
                                                 MockedRequestsResponse(200),
                                                 MockedRequestsResponse(200)])
        resp = self.http.delete(path)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_delete.called, "Failed to call requests.delete")
        path = "/exception"
        # Assert that RequestException is raised
        with self.assertRaises(RequestException,
                               msg="request.delete exception not raised properly"):
            self.http.delete(path)

        mock_requests_delete.reset_mock()
        path2 = "v2/"
        resp = self.http.delete(path2)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_delete.called, "Failed to call requests.delete")

        mock_requests_delete.reset_mock()
        path3 = "/v3/"
        self.http = HttpApi(self.host2)
        resp = self.http.delete(path3)  # pylint: disable=unused-variable
        self.assertTrue(mock_requests_delete.called, "Failed to call requests.delete")

    @mock.patch("icetea_lib.tools.HTTP.Api.HttpApi.get")
    def test_huge_binary_content(self, mocked_get):
        var = os.urandom(10000000)
        for _ in range(6):
            var = var + os.urandom(10000000)
        response = Response()
        response._content = var  # pylint: disable=protected-access
        response.encoding = "utf-8"
        response.status_code = 200
        mocked_get.return_value = response
        self.http = HttpApi(self.host)
        resp = self.http.get("/")
        self.assertEqual(resp, response)


if __name__ == '__main__':
    unittest.main()
