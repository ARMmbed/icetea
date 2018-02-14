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
from icetea_lib.Searcher import verify_message
from icetea_lib.Searcher import Invert

class TestVerify(unittest.TestCase):
    def test_default(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli',
            'strange bird']
        self.assertTrue(verify_message(lines, ['oopeli', 'huhheli']))
        self.assertFalse(verify_message(lines, ['oopeli', 'huhhelis']))
        self.assertFalse(verify_message(lines, ['oopeli', 'huhhe li']))
        self.assertFalse(verify_message(lines, [False]))
        self.assertTrue(verify_message(lines, ['strange bird']))

    def test_invert(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(verify_message(lines, ['oopeli', Invert('uups')]))
        self.assertFalse(verify_message(lines, ['oopeli', Invert('huhheli')]))
        self.assertFalse(verify_message(lines, ['oopeli', Invert('huhheli')]))

    def test_regex(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(verify_message(lines, ['^aa', '^be', '^oopeli']))
        self.assertFalse(verify_message(lines, ['^aa', '^opeli']))

    def test_string(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(verify_message(lines, "aapeli"))
        self.assertTrue(verify_message(lines, "oop"))
        self.assertFalse(verify_message(lines, "ai"))

    def test_set(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(verify_message(lines, {"aapeli"}))
        self.assertTrue(verify_message(lines, {"oop"}))
        self.assertFalse(verify_message(lines, {"ai"}))
        self.assertFalse(verify_message(lines, {1}))

    def test_false_type(self):
        with self.assertRaises(TypeError):
            verify_message([], 1)
