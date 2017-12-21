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
from icetea_lib.Searcher import verifyMessage
from icetea_lib.Searcher import Invert

class TestVerify(unittest.TestCase):
    def test_default(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli',
            'strange bird']
        self.assertTrue(verifyMessage(lines, ['oopeli', 'huhheli']))
        self.assertFalse(verifyMessage(lines, ['oopeli', 'huhhelis']))
        self.assertFalse(verifyMessage(lines, ['oopeli', 'huhhe li']))
        self.assertFalse(verifyMessage(lines, [False]))
        self.assertTrue(verifyMessage(lines, ['strange bird']))

    def test_invert(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli' ]
        self.assertTrue(verifyMessage(lines, ['oopeli', Invert('uups')]))
        self.assertFalse(verifyMessage(lines, ['oopeli', Invert('huhheli')]))
        self.assertFalse(verifyMessage(lines, ['oopeli', Invert('huhheli')]))

    def test_regex(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli' ]
        self.assertTrue(verifyMessage(lines, ['^aa', '^be', '^oopeli']))
        self.assertFalse(verifyMessage(lines, ['^aa', '^opeli']))

    def test_string(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(verifyMessage(lines, "aapeli"))
        self.assertTrue(verifyMessage(lines, "oop"))
        self.assertFalse(verifyMessage(lines, "ai"))

    def test_set(self):
        lines = [
            'aapeli',
            'beeveli',
            'oopeli',
            'huhheli']
        self.assertTrue(verifyMessage(lines, {"aapeli"}))
        self.assertTrue(verifyMessage(lines, {"oop"}))
        self.assertFalse(verifyMessage(lines, {"ai"}))
        self.assertFalse(verifyMessage(lines, {1}))

    def test_false_type(self):
        with self.assertRaises(TypeError):
            verifyMessage([], 1)