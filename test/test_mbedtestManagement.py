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
from os.path import join, abspath, dirname
import subprocess
import mock

from mbed_test.mbedtestManagement import ExitCodes
from mbed_test.mbedtestManagement import mbedtestManager
from mbed_test import Result
#Add mbedtest/test to path, to allow importing testbase files
testpath = dirname(abspath(__file__))
sys.path.append(testpath)


class MockObject:
    def __init__(self, version="0.5.0"):
        self.version = version


class TestVerify(unittest.TestCase):
    def setUp(self):
        global silent_on
        silent_on = True
        self.ctm = mbedtestManager()

        #variables for testing getLocalTestcases, parseLocalTestcases, parseLocalTest, loadClass, printListTestcases

        self.testdir = join(testpath, 'testbase')

        self.files = [
            ('testbase.dummy', 'testbase', abspath(join(self.testdir,'dummy.py'))),
            ('testbase.level0', 'testbase', abspath(join(self.testdir,'level0.py'))),
            ('testbase.lv1.level1', join('testbase','lv1'), abspath(join(self.testdir,'lv1','level1.py'))),
            ('testbase.lv1.lv2.level2', join('testbase','lv1','lv2'), abspath(join(self.testdir,'lv1','lv2','level2.py'))),
            ('testbase.lv1.lv2.lv3.level3', join('testbase','lv1','lv2','lv3'), abspath(join(self.testdir,'lv1','lv2','lv3','level3.py'))),
            ('testbase.dummy_multiples', 'testbase', abspath(join(self.testdir,'dummy_multiples.py')))
        ]

        #absolute path varies and should not be tested
        self.comparisonCases = [\
        {'tc_name': 'dummy',
        'tc_status': 'unknown',
        'tc_comp': ["None"],
        'tc_type': 'functional',
        'tc_path': 'testbase.dummy.Testcase',
        'tc_group': 'testbase',
        'tc_subtype': '',
        'tc_fail': ''}, \
        {'tc_status': 'released',
        'tc_name': 'rootdirtest',
        'tc_type': 'installation',
        'tc_subtype': '',
        'tc_path': 'testbase.level0.Testcase',
        'tc_group': 'testbase',
        'tc_comp':["None"],
        'tc_fail':''},\
        {'tc_status': 'development',
        'tc_name': 'subdirtest',
        'tc_type': 'compatibility',
        'tc_subtype': '',
        'tc_path': 'testbase.lv1.level1.Testcase',
        'tc_group': join('testbase','lv1'),
        'tc_comp':["None"],
        'tc_fail':''},\
        {'tc_status': 'maintenance',
        'tc_name': 'subsubdirtest',
        'tc_type': 'smoke',
        'tc_subtype': '',
        'tc_path': 'testbase.lv1.lv2.level2.Testcase',
        'tc_group': join('testbase','lv1','lv2'),
        'tc_comp':["None"],
        'tc_fail':''},\
        {'tc_status': 'broken',
        'tc_name': 'subsubsubdirtest',
        'tc_type': 'regression',
        'tc_subtype': '',
        'tc_path': 'testbase.lv1.lv2.lv3.level3.Testcase',
        'tc_group': join('testbase','lv1','lv2','lv3'),
        'tc_comp':["None"],
        'tc_fail':''},
        {'tc_name': 'first_dummy_test',
        'tc_status': 'unknown',
        'tc_comp': ["None"],
        'tc_type': 'functional',
        'tc_path': 'testbase.dummy_multiples.FirstTest',
        'tc_group': 'testbase',
        'tc_subtype': '',
        'tc_fail': ''},
        {'tc_name': 'second_dummy_test',
        'tc_status': 'unknown',
        'tc_comp': ["None"],
        'tc_type': 'functional',
        'tc_path': 'testbase.dummy_multiples.SecondTest',
        'tc_group': 'testbase',
        'tc_subtype': '',
        'tc_fail': ''}
        ]

        self.comparisonCase = {'tc_status': 'released', 'tc_file': join(self.testdir,'level0.py'), 'tc_name': 'rootdirtest', 'tc_type': 'installation', 'tc_subtype': '', 'tc_path': 'testbase.level0.Testcase', 'tc_group': 'testbase', 'tc_fail':'', 'tc_comp':["None"]}

        self.comparisonCaseMultiples = [
            {
                'tc_name': 'first_dummy_test',
                'tc_status': 'unknown',
                'tc_comp': ["None"],
                'tc_type': 'functional',
                'tc_path': 'testbase.dummy_multiples.FirstTest',
                'tc_group': 'testbase',
                'tc_subtype': '',
                'tc_fail': '',
                'tc_file': join(self.testdir,'dummy_multiples.py')
            },
            {
                'tc_name': 'second_dummy_test',
                'tc_status': 'unknown',
                'tc_comp': ["None"],
                'tc_type': 'functional',
                'tc_path': 'testbase.dummy_multiples.SecondTest',
                'tc_group': 'testbase',
                'tc_subtype': '',
                'tc_fail': '',
                'tc_file': join(self.testdir,'dummy_multiples.py')
            },
        ]

        #variables for testing createFilter
        self.intFilter = 1
        self.dictFilter = {'tc_group': 'testbase', 'tc_status':'released', 'tc_type':'compatibility'}
        self.dictFilter2 = {'tc_group': 'testbase/lv1', 'tc_status':'released', 'tc_type':'compatibility'}
        self.dictFilter3 = {'tc_status':'maintenance'}
        self.listFilterOut = [0,1,2,3]
        self.listFilterIn = [1,2,3,4]
        self.listFilter2 = [0,1]
        self.wildFilter = 'all'

        self.intString = str(self.intFilter)
        self.dictString = str(self.dictFilter2)
        self.listString = str(self.listFilterIn)
        self.stringString = 'rootdirtest'#wrong way would be 'level0.py', at the moment anyway.

        #variables for testing run()
        self.args_print = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='all', tc_cfg=None, tcdir=self.testdir, testtype=False, type=None,
            subtype=None, valgrind=False, valgrind_tool=None, verbose=False)
        self.args_noprint = argparse.Namespace(
            available=False, version=False, bin=None, binary=False, channel=None,
            clean=False, cloud=False, component=False, device='*', gdb=None,
            gdbs=None, gdbs_port=2345, group=False, iface=None, kill_putty=False, list=True,
            listsuites=False, log='./log', my_duts=None, nobuf=None, pause_when_external_dut=False,
            putty=False, reset=False, silent=True, skip_case=False, skip_rampdown=False, skip_rampup=False,
            status=False, suite=False, tc='all', tc_cfg=None, tcdir=self.testdir, testtype=False, type=None,
            subtype=None, valgrind=False, valgrind_tool=None, verbose=False)

        del sys.argv[1:]

    def tearDown(self):
        #Delete generated log files
        self.args_print.clean = True
        self.ctm.run(self.args_print)


    def test_getLocalTestcases_Success(self):
        #relativepath = join(testpath, '../../mbed-test/test/testbase')
        #weird_path = join(testpath, '../test/../../mbed-test/test/testbase')
        #Test that the right form of testcase list is returned
        files =  self.ctm.getLocalTestcases(self.testdir)
        for x in self.files:
            self.assertIn(x,files)
        #files =  self.ctm.getLocalTestcases(relativepath)
        #for x in self.files:
        #    self.assertIn(x,files)
        #files =  self.ctm.getLocalTestcases(weird_path)
        #for x in self.files:
        #    self.assertIn(x,files)

    def test_getLocalTestcases_Fail(self):
        #Not testing excessively large path tree, such as walking every directory in /
        faulty_path =  join(testpath, './foobar')
        proper_path =  join(testpath, './log')  #not expected to have any python files
        files = self.ctm.getLocalTestcases(faulty_path)
        self.assertEqual(files, [])
        files = self.ctm.getLocalTestcases(proper_path)
        self.assertEqual(files, [])

    def test_parseLocalTest_Success(self):
        #Test that the right dictionary is returned
        toparse = self.files[1]
        parsed = self.ctm.parseLocalTest(toparse[0],toparse[1],toparse[2], False)
        self.assertEqual(self.comparisonCase, parsed[0])
        for i in ['tc_name', 'tc_group', 'tc_status', 'tc_type', 'tc_file', 'tc_fail', 'tc_comp']:
            self.assertTrue(i in parsed[0].keys())

        # test with multiple tests cases embedded inside a syngle python file
        toparse = self.files[5]
        parsed = self.ctm.parseLocalTest(toparse[0],toparse[1],toparse[2], False)
        self.assertEqual(self.comparisonCaseMultiples, parsed)


    def test_parseLocalTest_Fail(self):
        #modulename not a string
        success = None
        try:
            self.ctm.parseLocalTest(5,'testbase','./testbase/level0.py', False)
        except TypeError:
            success = True
        self.assertTrue(success == True)

        #modulename is an empty string
        success = None
        try:
            self.ctm.parseLocalTest('','testbase','./testbase/level0.py', False)
        except ValueError:
            success = True
        self.assertTrue(success == True)

        #missing module
        missing_module_tcs = self.ctm.parseLocalTest('testbase.level1.Testcase','testbase','./testbase/level0.py', False)
        self.assertTrue(isinstance(missing_module_tcs, list))
        self.assertTrue('Invalid TC' in missing_module_tcs[0]['tc_fail'])
        # Not parseLocalTest's business to verify that getLocalTestcases produces correctly formatted tuples.
        # The second forms the group specifier, so if that's incorrect information while the first item is
        # correct then something has seriously broken getLocalTestcases.

        #TODO: Some way of testing uninitializable testcase.
        #TODO: Add test for json config file
        #TODO: Add test for in-file configuration dictionary(once that gets implemented)

    def test_parseLocalTestcases_Success(self):
        #Test that the right list of dictionaries is returned
        #The list is ordered, therefore the comparison happens in order. The dictionaries aren't, and the comparison happens by key:value.
        paths = ['./testbase']#, '../../mbed-test/test/testbase', '../test/../../mbed-test/test/testbase']
        for path in paths:
            gotCases = self.ctm.getLocalTestcases(join(testpath, path))
            parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
            for case in parsedCases:
                del case['tc_file']
            for case in parsedCases:
                keys = case.keys()
                self.assertIn('tc_name', keys)
                self.assertIn('tc_status', keys)
                self.assertIn('tc_comp', keys)
                self.assertIn('tc_type', keys)
                self.assertIn('tc_path', keys)
                self.assertIn('tc_group', keys)
            self.assertEqual(
                sorted(self.comparisonCases, key=lambda tc: tc['tc_name']),
                sorted(parsedCases, key=lambda tc: tc['tc_name'])
            )

    def test_parseLocalTestcases_Fail(self):
        #misshapen list
        files = list(self.files)
        files[0] = 5
        fetchedCases = self.ctm.parseLocalTestcases(files, False)
        #skips case 1 because module not specified
        #checking file path comparisons is pointless
        for case in fetchedCases:
            del case['tc_file']
        self.assertEqual(fetchedCases, self.comparisonCases[1:])
        #integer, string, dict
        self.assertEqual(self.ctm.parseLocalTestcases(5, False), [])
        self.assertEqual(self.ctm.parseLocalTestcases('rutabaga', False), [])
        self.assertEqual(self.ctm.parseLocalTestcases({'ruta': 'baga'}, False), [])

    def test_createFilter_Success(self):
        #Test that the right kind of filter is returned based on input object
        filt = self.ctm.createFilter('asdf')

        self.assertEqual(filt['tc_name'], 'asdf')
        for key in filt.keys():
            if key != 'tc_name':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter('all')
        self.assertEqual(filt['tc_name'], 'all')

        filt = self.ctm.createFilter('[1,2,3]')
        self.assertTrue(isinstance(filt['tc_list'], list))
        self.assertEqual(filt['tc_list'], [0, 1, 2])
        self.assertTrue(len(filt['tc_list']) == 3)
        for key in filt.keys():
            if key != 'tc_list':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter('1,2,3')
        self.assertTrue(isinstance(filt['tc_list'], list))
        self.assertEqual(filt['tc_list'], [0, 1, 2])
        self.assertTrue(len(filt['tc_list']) == 3)
        for key in filt.keys():
            if key != 'tc_list':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter('1')
        self.assertTrue(isinstance(filt['tc_list'], list))
        self.assertEqual(filt['tc_list'], [0])
        self.assertTrue(len(filt['tc_list']) == 1)
        for key in filt.keys():
            if key != 'tc_list':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter(status='broken')
        self.assertTrue(isinstance(filt, dict))
        self.assertEqual(filt['tc_status'], 'broken')
        for key in filt.keys():
            if key != 'tc_status':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter(group='testbase')
        self.assertTrue(isinstance(filt, dict))
        self.assertEqual(filt['tc_group'], 'testbase')
        for key in filt.keys():
            if key != 'tc_group':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter(testtype='installation')
        self.assertTrue(isinstance(filt, dict))
        self.assertEqual(filt['tc_type'], 'installation')
        for key in filt.keys():
            if key != 'tc_type':
                self.assertFalse(filt[key])

        filt = self.ctm.createFilter()
        self.assertEqual(filt, -1)

        filt = self.ctm.createFilter(['a'])
        self.assertTrue(isinstance(filt, dict))
        self.assertTrue(isinstance(filt['tc_list'], list))
        self.assertTrue(len(filt['tc_list']) == 1)

        filt = self.ctm.createFilter(tc=False, status='asdf', group='fdsa', testtype='foobar', subtype=False, component='foo')
        self.assertEqual({'tc_list': False, 'tc_name': False, 'tc_status': 'asdf', 'tc_group': 'fdsa', 'tc_type': 'foobar', 'tc_subtype':False, 'tc_comp':['foo']}, filt)

        #string with weird symbols?
        #self.assertTrue(self.ctm.createFilter('asdf‰@£$‰{‚3'))
        #Succeeds, but will return escaped characters. Add utf-8 support?

    def test_createFilter_Fail(self):
        #negative integer
        filt = self.ctm.createFilter(status = 5)
        self.assertTrue(filt == -1)

        filt = self.ctm.createFilter(group = 5)
        self.assertTrue(filt == -1)

        filt = self.ctm.createFilter(testtype = 5)
        self.assertTrue(filt == -1)

        filt = self.ctm.createFilter(tc = -5)
        self.assertTrue(filt == -1)

        filt = self.ctm.createFilter({'foo':5})
        self.assertTrue(filt == -1)

        filt = self.ctm.createFilter({'tc_status':5})
        filt = self.ctm.createFilter({'tc_status':5})
        self.assertTrue(filt == -1)

        filt = self.ctm.createFilter(tc={'tc_status':'a'},status='broken')
        self.assertTrue(filt['tc_status'] == 'broken')

        filt = self.ctm.createFilter([])
        self.assertTrue(filt == -1)

        #string with bad encoding?
        #add test when encoding decision made

    def test_filterTestcases_Success(self):
        gotCases = self.ctm.getLocalTestcases(self.testdir)
        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)

        filt = self.ctm.createFilter('rootdirtest')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 1)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter('all')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == len(parsedCases))

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter('[1,2]')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 2)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter('1')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 1)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter(status='broken')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 1)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter(group='lv3')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 1)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter(group='testbase')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == len(self.comparisonCases))

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter(group=join('testbase','lv1'))
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 3)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter(testtype='installation')
        filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 1)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter()
        with self.assertRaises(SystemExit) as cm:
            filtered = self.ctm.filterTestcases(parsedCases, filt)
        self.assertEqual(cm.exception.code, 0)

        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        filt = self.ctm.createFilter(False, 'released', 'testbase', 'installation')
        self.assertTrue(isinstance(filtered, list))
        self.assertTrue(len(filtered) == 1)

        cases = self.ctm.filterTestcases(parsedCases, {'tc_list':['rootdirtest', 2]})
        self.assertTrue(len(cases) == 2)


    def test_filterTestcases_Fail(self):
        gotCases = self.ctm.getLocalTestcases(self.testdir)
        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(parsedCases, [])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(parsedCases, {'tc_fail':4})
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(parsedCases, {})
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(parsedCases, {'tc_list': False, 'tc_name': False, 'tc_status': False, 'tc_group': False, 'tc_type': False})
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(5, {'tc_list':[]})
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases([], {'tc_list':[]})
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(parsedCases, {'tc_list':[99999999]})
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            cases = self.ctm.filterTestcases(parsedCases, {'tc_list':[-5]})
        self.assertEqual(cm.exception.code, 0)

        cases = self.ctm.filterTestcases(parsedCases,{'tc_group':'rutabaga'})
        self.assertTrue(len(cases)==0)

    @mock.patch("mbed_test.mbedtestManagement.pkg_resources.require", return_value=[MockObject()])
    def test_runTest_Success(self, mock_pkg):
        #Test running a single test
        result = self.ctm.runTest(self.comparisonCase['tc_path'])
        self.assertTrue(result != None)
        result = self.ctm.runTest(self.comparisonCase['tc_path'], defaultConf={"name": "testname", "requirements": {"duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        self.assertTrue(result != None)


        #Commented out due to CI.
        self.ctm.args.check_version = True
        compat = {"framework": {"name": "mbedtest", "version": "0.5.0"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'], defaultConf={"name": "testname", "compatible": compat, "requirements": {
            "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        self.assertEquals(result.getVerdict(), "pass")

        compat = {"framework": {"name": "mbedtest", "version": ">0.3.2"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        self.assertEquals(result.getVerdict(), "pass")

        #Better way to do a check?
        #TDOO: The below doesn't work. Why?
        #print result  #gives that is instance of Result.Result
        #print isinstance(result, Result.Result)    #False, apparently
        #self.assertTrue(isinstance(result, Result.Result))

    @mock.patch("mbed_test.mbedtestManagement.pkg_resources.require", return_value=[MockObject()])
    def test_runTest_Fail(self, mock_pkg):
        #Missing module
        with self.assertRaises(ImportError) as cm:
            self.ctm.runTest('testbase.level1.Testcase')
        #Modulename not a string
        with self.assertRaises(TypeError) as cm:
            self.ctm.runTest(5)

        self.ctm.args.check_version = True
        non_compat = {"framework": {"name": "mbedtest", "version": "0.3.2"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": non_compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        verdict = result.getVerdict()
        self.assertEquals("skip", verdict)


        non_compat = {"framework": {"name": "mbedtest", "version": "<0.3.2"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": non_compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        verdict = result.getVerdict()
        self.assertEquals("skip", verdict)


        non_compat = {"framework": {"name": "mbedtest", "version": ">0.5.0"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": non_compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        verdict = result.getVerdict()
        self.assertEquals("skip", verdict)

        mock_pkg.return_value = [MockObject(version="1.0.0")]
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": non_compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        verdict = result.getVerdict()
        self.assertEquals("skip", verdict)

        non_compat = {"framework": {"name": "mbedtest", "version": "0.5.0"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": non_compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        verdict = result.getVerdict()
        self.assertEquals("skip", verdict)

        non_compat = {"framework": {"name": "mbedtest", "version": ">=0.5.0"}}
        result = self.ctm.runTest(self.comparisonCase['tc_path'],
                                  defaultConf={"name": "testname", "compatible": non_compat, "requirements": {
                                      "duts": {"*": {"count": 0}, 1: {"nick": "None"}}}})
        verdict = result.getVerdict()
        self.assertEquals("skip", verdict)


        #silent
        #    does not really need automated testing, as it only controls printing.
        #if testbenchname(), skip() or skipreason() don't exist, it will have been caught by other tests
        #they are methods in bench.py, which is inherited by every testcase, and which should be tested separately.


    def test_runTestcases_Success(self):
        #Run set of dummy tests
        results = self.ctm.runTestcases(self.comparisonCases)
        self.assertTrue(isinstance(results, list))
        self.assertEqual(len(results), len(self.comparisonCases))

    def test_runTestcases_Fail(self):
        path = join(testpath, './testbase')
        gotCases = self.ctm.getLocalTestcases(path)
        parsedCases = self.ctm.parseLocalTestcases(gotCases, False)
        #faulty testcase list
        cases = list(parsedCases)
        cases[1] = 5
        results = self.ctm.runTestcases(cases)
        self.assertEqual(len(results), len(cases)-1)
        #not iterable
        results = self.ctm.runTestcases(5)
        self.assertTrue(results == [])
        #list member dictionary does not have 'tc_path' key
        cases = list(parsedCases)
        del cases[1]['tc_path']
        results = self.ctm.runTestcases(cases)
        self.assertTrue(len(results) == len(cases)-1)

    def test_runPrint(self):
        #Test printing testcases from base method
        self.assertTrue(self.ctm.run(self.args_print) == 0)

    def test_runNoPrint(self):
        #Test running testcases from base method
        self.assertTrue(self.ctm.run(self.args_noprint) == 0)

    def test_runClean(self):
        clean = self.args_noprint
        clean.clean = True
        self.assertTrue(self.ctm.run(clean) == 0)


    def test_run_returnCodes(self):
        retcode = subprocess.call("python mbedtest.py --tc test_run_retcodes_fail --tcdir test --type process -s",
                                  shell = True)
        self.assertEquals(retcode, ExitCodes.EXIT_FAIL)
        retcode = subprocess.call("python mbedtest.py --tc test_run_retcodes_success --tcdir test --type process -s",
                                  shell = True)
        self.assertEquals(retcode, ExitCodes.EXIT_SUCCESS)

        retcode = subprocess.call("python mbedtest.py --tc test_run_retcodes_notfound --tcdir test --type process -s",
                                  shell = True)
        self.assertEquals(retcode, ExitCodes.EXIT_ERROR)

