#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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
import sys
import argparse
import os
import json

#Adds mbedtest/ to path, to allow importing using mbed_test.module form
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(libpath)
from mbed_test.mbedtestManagement import mbedtestManager
from mbed_test import Result

class TestVerify(unittest.TestCase):
    def setUp(self):
        self.ctm = mbedtestManager()

        #variables for testing getLocalTestcases, parseLocalTestcases, parseLocalTest, loadClass, printListTestcases

        self.testpath = os.path.abspath(os.path.dirname(__file__))
        sys.path.append(self.testpath)
        self.testdir = os.path.join(self.testpath, 'testbase')
        #variables for testing run()

        self.args_suite = argparse.Namespace(available=False, version=False, bin=None, binary=False, branch='master', buildDate='', buildUrl='', campaign='', clean=False, cloud=False, commitId='', component=False, device='*', gdb=None, gdbs=None, gdbs_port=2345, vgdb=None, gitUrl='', group=False, iface=None, kill_putty=False, list=False, listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False, putty=False, reset=False, silent=False, skip_case=False, skip_rampdown=False, skip_rampup=False, status=False, subtype=False, suite='dummy_suite.json', suitedir=os.path.join(self.testpath, 'suites'), tc=False, tc_cfg=None, tcdir=os.path.join(self.testpath, 'testbase'), testtype=False, type=None, use_sniffer=False, valgrind=False, valgrind_text=False, valgrind_console=False, valgrind_tool=None, valgrind_track_origins=False, verbose=False)
        del sys.argv[1:]


    def tearDown(self):
        #Delete generated log files
        self.ctm.cleanLogs()

    def test_getSuites(self):
        #suitedir = os.join(testpath, 'suites') #mbed-test/test/suites
        suitedir = self.testpath
        suitelist = self.ctm.getSuites(os.path.join(self.testpath, 'suites'))
        #Assert is list
        self.assertTrue(isinstance(suitelist, list))
        #Assert is len 1
        self.assertEqual(len(suitelist), 1)

        #Assert handles not string
        suitelist = self.ctm.getSuites(5)
        self.assertEqual(suitelist, [])

        #Assert handles faulty path
        suitelist = self.ctm.getSuites('./rutabaga')
        self.assertEqual(suitelist, [])

    def test_runSuite(self):
        
        with open(os.path.join(self.testpath,'./suites/dummy_suite.json')) as file:
            suite = json.load(file)
        results = self.ctm.runSuite(suite, tcdir=self.testdir)
        self.assertTrue(isinstance(results, list))
        self.assertEqual(len(results), 3)

        results = self.ctm.runSuite(suite, tcdir="examples")
        self.assertTrue(isinstance(results, list))
        self.assertEqual(len(results), 2)

        bad_suite = {"testcases": [{"iteration": 1,"retryCount": 0,}]}
        results = self.ctm.runSuite(bad_suite, tcdir=self.testdir)
        self.assertEqual(results, [])

        bad_suite = {"testcases": [{"name":"rutabaga","iteration": 1,"retryCount": 0,}]}
        tc = [str(x['name']) for x in bad_suite['testcases']]
        filt = self.ctm.createFilter(tc)
        results = self.ctm.runSuite(bad_suite, tcdir=self.testdir)
        self.assertEqual(results, [])
        #testcase that times out?
        #failing testcase?

        self.assertEqual(self.ctm.run(self.args_suite), 0)
