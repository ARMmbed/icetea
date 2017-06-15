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

__author__ = 'jaakuk03'
import unittest
import sys
import os
import mbed_test.tools as tools

class TestClass():
    def __init__(self):
        self.test = True

class TestTools(unittest.TestCase):
    def test_loadClass_Success(self):
        sys.path.append(os.path.dirname(__file__))
        #Test that loadClass can import a class that is initializable
        module = tools.loadClass( "test_tools.TestClass" , verbose=False, silent=True)
        self.assertIsNotNone(module)
        moduleInstance = module()
        self.assertTrue( moduleInstance.test )
        del moduleInstance

    def test_loadClass_Fail(self):
        self.assertIsNone(tools.loadClass( 'testbase.level1.Testcase', verbose=False, silent=True))
        self.assertIsNone(tools.loadClass( '', verbose=False, silent=True))
        self.assertIsNone(tools.loadClass( 5 , verbose=False, silent=True))
        self.assertIsNone(tools.loadClass( [], verbose=False, silent=True))
        self.assertIsNone(tools.loadClass( {}, verbose=False, silent=True))

    def test_strintkey_to_intkey(self):
        suitedict = {
            "1": 1,
            "2": {"two": 2,
                  "3": 3
                 }
            }
        tools.strintkey_to_intkey(suitedict)
        # verify that integer strings are now integers
        self.assertTrue(1 in suitedict.keys())
        self.assertTrue(2 in suitedict.keys())
        self.assertTrue(3 in suitedict[2].keys())