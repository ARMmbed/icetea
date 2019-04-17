#!/usr/bin/env python
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
# pylint: disable=unused-argument
import mock


def create(*args, **kwargs):
    """
    Create a Mock object that imitates a valid Cloud module.

    :param args: Not used
    :param kwargs: Not used
    :return: mock.MagicMock
    """
    attrs = {"client.get_suite.return_value": True, "get_campaign_id.side_effect": [True, KeyError],
             "get_campaigns.return_value": True, "update_testcase.return_value": True,
             "upload_results.side_effect": [True, False]}
    mock_module = mock.MagicMock()
    mock_module.configure_mock(**attrs)
    return mock_module
