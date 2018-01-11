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
from icetea_lib.CliResponse import CliResponse


class TestVerify(unittest.TestCase):

    def test_resps(self):
        response = CliResponse()
        response.lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(response.verify_message(['oopeli'], False))
        self.assertTrue(response.verify_message(['oopeli', 'huhheli'], False))
        self.assertFalse(response.verify_message(['huhheli', 'oopeli'], False))

        with self.assertRaises(LookupError):
            self.assertTrue(response.verify_message(['oop eli']))

    def test_traces(self):
        response = CliResponse()
        response.traces = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(response.verify_trace(['oopeli'], False))
        self.assertTrue(response.verify_trace(['oopeli', 'huhheli'], False))
        self.assertFalse(response.verify_trace(['huhheli', 'oopeli'], False))

        with self.assertRaises(LookupError):
            self.assertTrue(response.verify_trace(['oop eli']))

    def test_traces_deprecated(self):
        response = CliResponse()
        response.traces = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(response.verify_trace(['oopeli'], False))
        self.assertTrue(response.verify_trace(['oopeli', 'huhheli'], False))
        self.assertFalse(response.verify_trace(['huhheli', 'oopeli'], False))

        with self.assertRaises(LookupError):
            self.assertTrue(response.verify_trace(['oop eli']))
