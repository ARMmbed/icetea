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

import random
import unittest
import tempfile
from icetea_lib.Randomize.randomize import Randomize


class RandomizeTestcase(unittest.TestCase):
    def test_full_args(self):
        self.assertGreaterEqual(Randomize.random_integer(7, 3).value, 3)
        self.assertLessEqual(Randomize.random_integer(7, 3).value, 7)

        self.assertIn(Randomize.random_list_elem(['a', 'bb', 'cc']),
                      ['a', 'bb', 'cc'])

        self.assertGreaterEqual(len(Randomize.random_string(7, 3,
                                                            lambda x: random.choice(x), x='e34r')),
                                3)
        self.assertLessEqual(len(Randomize.random_string(7, 3,
                                                         lambda x: random.choice(x), x='e34r')),
                             7)
        self.assertIn(Randomize.random_string(chars=["aa", "bb", "ceedee"]).value,
                      ["a", "b", "c", "d", "e"])

        self.assertIn(Randomize.random_array_elem(['a', 'bb', 'cc']).value, [['a'], ['bb'], ['cc']])

        self.assertGreaterEqual(
            len(Randomize.random_string_array(9, 3, 7, 2, lambda x: random.choice(x), x='e34r')),
            3)
        self.assertLessEqual(
            len(Randomize.random_string_array(9, 3, 7, 2, lambda x: random.choice(x), x='e34r')),
            9)

    def test_chars_not_str(self):
        with self.assertRaises(ValueError):
            Randomize.random_string(7, 3, chars=6)

    def test_chars_not_list(self):
        with self.assertRaises(TypeError):
            Randomize.random_list_elem([6])

    def test_random_string_list_chars_not_str(self):
        with self.assertRaises(TypeError):
            Randomize.random_string(2, 1, chars=["a", "abc", 1])

    def test_random_integer_add(self):
        i = Randomize.random_integer(6)
        self.assertTrue(i + 6 == i.value + 6)
        self.assertTrue(6 + i == i.value + 6)

    def test_random_string_add(self):
        s = Randomize.random_string(5)
        v = s.value
        self.assertEqual(s + ' hello', v + ' hello')
        self.assertEqual('hello ' + s, 'hello ' + v)

    def test_random_string_array_add(self):
        a = Randomize.random_string_array(5, 3)
        v = a.value
        self.assertEqual(a + ['world'], v + ['world'])
        self.assertEqual(['world'] + a, ['world'] + v)

    def test_random_integer_iadd(self):
        i = Randomize.random_integer(6)
        v = i.value

        i += 6
        v += 6

        self.assertEqual(i, v)

    def test_random_integer_repr(self):
        i = Randomize.random_integer(6)
        self.assertEqual("%s" % i, str(i.value))

    def test_random_string_repr(self):
        s = Randomize.random_string(5)
        self.assertEqual("%s" % s, str(s.value))

    def test_random_string_array_repr(self):
        a = Randomize.random_string_array(5, 3)
        self.assertEqual("%s" % a, str(a.value))

    def test_random_string_iter(self):
        for elem in Randomize.random_string(7, 3):
            self.assertTrue(isinstance(elem, str))

    def test_random_string_array_iter(self):
        for elem in Randomize.random_string_array(7, 3):
            self.assertTrue(isinstance(elem, str))

    def test_random_string_get_item(self):
        s = Randomize.random_string(6)
        v = s.value
        self.assertEqual(s[0], v[0])

    def test_random_string_array_get_item(self):
        a = Randomize.random_string_array(6, 3)
        v = a.value
        self.assertEqual(a[0], v[0])

    def test_random_string_str(self):
        s_str = Randomize.random_string(6)
        self.assertEqual(str(s_str), s_str.value)

    def test_reproduce(self):
        seed = Randomize.random_integer(20, 3).value

        def user_func(seed):
            random.seed(seed)
            return random.randint(5,15), random.randint(15,25)

        r1, r2 = user_func(seed)
        r3, r4 = user_func(seed)

        self.assertEqual(r1, r3)
        self.assertEqual(r2, r4)

    def test_store_load(self):
        s_int = Randomize.random_integer(8, 4)
        s_str = Randomize.random_string(8, 4, lambda x: random.choice(x), x='e34r')
        s_str_a = Randomize.random_string_array(10, 6, 7, 4)

        f = tempfile.NamedTemporaryFile(delete=False)
        s_int.store(f.name)
        self.assertEqual(s_int.value, s_int.load(f.name).value)
        f.close()

        f = tempfile.NamedTemporaryFile(delete=False)
        s_str.store(f.name)
        self.assertEqual(s_str.value, s_str.load(f.name).value)
        f.close()

        f = tempfile.NamedTemporaryFile(delete=False)
        s_str_a.store(f.name)
        self.assertEqual(s_str_a.value, s_str_a.load(f.name).value)
        f.close()
