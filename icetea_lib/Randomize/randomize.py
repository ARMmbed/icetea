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

Randomize class for generating randomized content.
"""

import random
import string
from inspect import isfunction

from icetea_lib.Randomize.seed import SeedInteger, SeedString, SeedStringArray


class Randomize(object):
    """
    Randomize class, collection of static methods for generating randomized content.
    """
    @staticmethod
    def random_integer(max_value, min_value=0):
        """
        :param max_value: Maximum value, int
        :param min_value: Minimum value, int, default is 0
        :return: SeedInteger
        """
        return SeedInteger(random.randint(min_value, max_value))

    @staticmethod
    def random_list_elem(str_list):
        """
        :param str_list: a pre-defined string list
        :return: SeedString()
        """
        if isinstance(str_list, list):
            for elem in str_list:
                if not isinstance(elem, str):
                    raise TypeError("list element can only be string")
            return SeedString(random.choice(str_list))
        return None

    @staticmethod
    def random_string(max_len=1, min_len=1, chars=string.ascii_letters, **kwargs):
        """
        :param max_len: max value of len(string)
        :param min_len: min value of len(string)
        :param chars: can be sting, list of strings or function pointer.
        Randomly choose one if given a list of strings
        :param kwargs: keyword arguments for chars if it's function pointer
        :return: SeedString()
        """
        if isinstance(chars, list):
            # assume each element is a str
            chars = ''.join(chars)

        if isinstance(chars, str):
            return SeedString(
                ''.join(random.choice(chars) for _ in range(random.randint(min_len, max_len))))
        elif isfunction(chars):
            # this function is assumed to return/generate one character each time it is called
            return SeedString(
                ''.join(chars(**kwargs) for _ in range(random.randint(min_len, max_len))))
        else:
            raise ValueError("chars should be string, list, or function pointer")

    @staticmethod
    def random_array_elem(str_array):
        """
        :param str_array:a pre-defined string array
        :return: SeedStringArray()
        """
        return SeedStringArray([str(Randomize.random_list_elem(str_array))])

    @staticmethod
    def random_string_array(max_len=1, min_len=1,
                            elem_max_len=1, elem_min_len=1,
                            strings=string.ascii_letters, **kwargs):
        """
        :param max_len: max value of len(array)
        :param min_len: min value of len(array)
        :param elem_max_len: max value of len(array[index])
        :param elem_min_len: min value of len(array[index])
        :param strings: allowed string characters in each element of array,
        or predefined list of strings, or function pointer
        :param **kwargs: keyworded arguments for strings if it's a function pointer
        :return: SeedStringArray
        """
        string_array = list()
        for _ in range(random.randint(min_len, max_len)):
            string_array.append(Randomize.random_string(max_len=elem_max_len, min_len=elem_min_len,
                                                        chars=strings, **kwargs).value)

        return SeedStringArray(string_array)
