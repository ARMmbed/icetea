# pylint: disable=missing-docstring,pointless-string-statement,wrong-import-position
# pylint: disable=redefined-outer-name
from __future__ import unicode_literals

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

REST API methods for use with Icetea. Implements GET, PUT, POST and DELETE methods for now.
Also includes helper functions to set values for default headers, cert and host address.

Basic logger also included, can be easily replaced by custom loggers when constructing
HttpApi object or later with setter.

@Author: Joonas Nikula
"""

import json
import urllib
import requests
from six import binary_type, string_types
import jsonmerge

from icetea_lib.tools.tools import combine_urls, initLogger


# Schema to make sure header fields are overwritten
SCHEMA = {
    "properties": {
        "mergeStrategy": "overwrite"
    }
}


class HttpApi(object):
    # pylint: disable=invalid-name
    def __init__(self, host, defaultHeaders=None, cert=None, logger=None):
        self.logger = initLogger("HttpApi") if logger is None else logger
        self.defaultHeaders = {} if defaultHeaders is None else defaultHeaders
        self.host = host
        self.cert = cert
        self.logger.info("HttpApi initialized")

    def set_logger(self, logger):
        """
        Sets a custom logger that is to be used with the HttpApi class.

        :param logger: custom logger to use to log HttpApi log messages
        :return: Nothing
        """
        self.logger = logger

    def set_header(self, key, value):
        """
        Sets a new value for a header field in defaultHeader.
        Replaces old value if the key already exists.

        :param key: HTTP header key name
        :param value:HTTP header key value
        :return: Nothing, modifies defaultHeaders in place
        """
        self.defaultHeaders[key] = value

    def set_cert(self, cert):
        """
        Setter for certificate field. Valid values are either a string
        containing path to certificate .pem file or Tuple, ('cert', 'key') pair.

        :param cert: Valid values are either a string containing path to certificate .pem file
        or Tuple, ('cert', 'key') pair.
        :return: Nothing, modifies field in place
        """
        self.cert = cert

    def set_host(self, host):
        """
        Setter for host parameter

        :param host: address of HTTP service
        :return: Nothing, modifies field in place
        """
        self.host = host

    def get(self, path, headers=None, params=None, **kwargs):
        """
        Sends a GET request to host/path.

        :param path: String, Resource path on server
        :param params: Dictionary of parameters to be added to URL
        :param headers: Dictionary of HTTP headers to be sent with the request,
        overwrites default headers if there is overlap
        :param kwargs: Other arguments used in the requests.request call
        valid parameters in kwargs are the optional parameters of Requests.Request
        http://docs.python-requests.org/en/master/api/
        :return: requests.Response
        :raises: RequestException
        """

        if headers is not None:
            merger = jsonmerge.Merger(SCHEMA)
            kwargs["headers"] = merger.merge(self.defaultHeaders, headers)
        else:
            kwargs["headers"] = self.defaultHeaders

        if self.cert is not None:
            kwargs["cert"] = self.cert

        if params is None:
            params = {}

        url = combine_urls(self.host, path)

        self.logger.debug(
            "Trying to send HTTP GET to {0}{1}".format(url,
                                                       "?" + urllib.urlencode(
                                                           params,
                                                           doseq=True) if params else ''))
        try:
            resp = requests.get(url, params, **kwargs)
            self._log_response(resp)
        except requests.RequestException as es:
            self._log_exception(es)
            raise
        return resp

    def post(self, path, data=None, json=None, headers=None, **kwargs):
        """
        Sends a POST request to host/path.

        :param path: String, resource path on server
        :param data: Dictionary, bytes or file-like object to send in the body of the request
        :param json: JSON formatted data to send in the body of the request
        :param headers: Dictionary of HTTP headers to be sent with the request,
        overwrites default headers if there is overlap
        :param kwargs: Other arguments used in the requests.request call
        valid parameters in kwargs are the optional parameters of Requests.Request
        http://docs.python-requests.org/en/master/api/
        :return: requests.Response
        :raises: RequestException
        """

        if headers is not None:
            merger = jsonmerge.Merger(SCHEMA)
            kwargs["headers"] = merger.merge(self.defaultHeaders, headers)
        else:
            kwargs["headers"] = self.defaultHeaders

        url = combine_urls(self.host, path)

        if self.cert is not None:
            kwargs["cert"] = self.cert
        self.logger.debug("Trying to send HTTP POST to {}".format(url))
        try:
            resp = requests.post(url, data, json, **kwargs)
            self._log_response(resp)
        except requests.RequestException as es:
            self._log_exception(es)
            raise

        return resp

    def put(self, path, data=None, headers=None, **kwargs):
        """
        Sends a PUT request to host/path.

        :param path: String, resource path on server
        :param data: Dictionary, bytes or file-like object to send in the body of the request
        :param headers: Dictionary of HTTP headers to be sent with the request,
        overwrites default headers if there is overlap
        :param kwargs: Other arguments used in the requests.request call
        valid parameters in kwargs are the optional parameters of Requests.
        Request http://docs.python-requests.org/en/master/api/
        :return: requests.Response
        :raises: RequestException
        """

        if headers is not None:
            merger = jsonmerge.Merger(SCHEMA)
            kwargs["headers"] = merger.merge(self.defaultHeaders, headers)
        else:
            kwargs["headers"] = self.defaultHeaders

        url = combine_urls(self.host, path)

        if self.cert is not None:
            kwargs["cert"] = self.cert
        self.logger.debug("Trying to send HTTP PUT to {}".format(url))
        try:
            resp = requests.put(url, data, **kwargs)
            self._log_response(resp)
        except requests.RequestException as es:
            self._log_exception(es)
            raise
        return resp

    def delete(self, path, headers=None, **kwargs):
        """
        Sends a DELETE request to host/path.

        :param path: String, resource path on server
        :param headers: Dictionary of HTTP headers to be sent with the request,
        overwrites default headers if there is overlap
        :param kwargs: Other arguments used in the requests.request call
        valid parameters in kwargs are the optional parameters of Requests.Request
        http://docs.python-requests.org/en/master/api/
        :return: requests.Response
        :raises: RequestException
        """

        if headers is not None:
            merger = jsonmerge.Merger(SCHEMA)
            kwargs["headers"] = merger.merge(self.defaultHeaders, headers)
        else:
            kwargs["headers"] = self.defaultHeaders

        url = combine_urls(self.host, path)

        if self.cert is not None:
            kwargs["cert"] = self.cert
        self.logger.debug("Trying to send HTTP DELETE to {}".format(url))
        try:
            resp = requests.delete(url, **kwargs)
            self._log_response(resp)
        except requests.RequestException as es:
            self._log_exception(es)
            raise

        return resp

    def patch(self, path, data=None, headers=None, **kwargs):
        """
        Sends a PATCH request to host/path.

        :param path: String, resource path on server
        :param data: Data as a dictionary, bytes, or file-like object to
        send in the body of the request.
        :param headers: Dictionary of HTTP headers to be sent with the request,
        overwrites default headers if there is overlap
        :param kwargs: Other arguments used in the requests.request call
        valid parameters in kwargs are the optional parameters of Requests.Request
        http://docs.python-requests.org/en/master/api/
        :return: requests.Response
        :raises: RequestException
        """

        if headers is not None:
            merger = jsonmerge.Merger(SCHEMA)
            kwargs["headers"] = merger.merge(self.defaultHeaders, headers)
        else:
            kwargs["headers"] = self.defaultHeaders

        url = combine_urls(self.host, path)

        if self.cert is not None:
            kwargs["cert"] = self.cert
        self.logger.debug("Trying to send HTTP PATCH to {}".format(url))
        try:
            resp = requests.patch(url, data=data, **kwargs)
            self._log_response(resp)
        except requests.RequestException as es:
            self._log_exception(es)
            raise

        return resp

    # pylint: disable=len-as-condition
    def _log_response(self, resp):
        self.logger.debug("Request url: %s", resp.request.url)
        self.logger.debug("Request headers: %s", resp.request.headers)
        self.logger.debug("Server responded with %d", resp.status_code)
        self.logger.debug("Response headers: %s", resp.headers)
        if hasattr(resp, "content") and len(resp.content) > 0:
            try:
                json_content = json.loads(resp.content)
                self.logger.debug("Response content: {}".format(json_content))
            except ValueError:
                if isinstance(resp.content, binary_type):
                    try:
                        self.logger.debug("Response payload: {}".format(resp.content))
                    except UnicodeDecodeError:
                        self.logger.debug("Response payload: {}".format(repr(resp.content)))
                elif isinstance(resp.content, string_types):
                    self.logger.debug("Response payload: {}".format(resp.content.decode("utf-8")))
                else:
                    self.logger.debug("Unable to parse response payload")

    def _log_exception(self, exception):
        if hasattr(exception, "request") and exception.request:
            self.logger.debug("Request url:     {}".format(exception.request.url))
            self.logger.error("Request headers: {}".format(exception.request.headers))
            if hasattr(exception.request, "data"):
                if exception.request.data and len(exception.request.data) > 0:
                    self.logger.error("Request payload {}".format(exception.request.data))
        self.logger.error("Exception when performing request: {}".format(exception))
