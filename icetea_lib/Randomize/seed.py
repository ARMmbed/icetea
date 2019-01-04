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

import uuid
from datetime import datetime
import json


class Seed(object):
    """
    Base Seed implementation.
    """
    def __init__(self, value, seed_id=None, date=None):
        self.__seed_value = value
        self.__seed_id = seed_id if seed_id else str(uuid.uuid4())
        self.__date = date if date else datetime.utcnow().isoformat()

    def __repr__(self):
        return str(self.__seed_value)

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __cmp__(self, other):
        return cmp(self.value, other)

    @property
    def value(self):
        """
        get __seed_value.

        :return: __seed_value
        """
        return self.__seed_value

    @property
    def seed_id(self):
        """
        get __seed_id.

        :return: __seed_id
        """
        return self.__seed_id

    @property
    def date(self):
        """
        Return date.

        :return: __date
        """
        return self.__date

    def store(self, filename):
        """
        Store seed in json format into a file

        :param filename: File name to save
        :return: Nothing
        """
        with open(filename, 'w') as file_handle:
            seed_dict = {"seed_id": self.seed_id, "seed_value": self.value, "date": self.date}
            json.dump(seed_dict, file_handle)

    @staticmethod
    def load(filename):
        """
        Load seed from a file.

        :param filename: Source file name
        :return: dict
        """
        with open(filename, 'r') as file_handle:
            return json.load(file_handle)


class SeedInteger(Seed):
    """
    Integer seed implementation.
    """
    def __iadd__(self, other):
        return SeedInteger(self.value + other)

    @staticmethod
    def load(filename):
        """
        Load seed from a file.

        :param filename: Source file name
        :return: SeedInteger
        """
        json_obj = Seed.load(filename)
        return SeedInteger(json_obj["seed_value"], json_obj["seed_id"], json_obj["date"])


class SeedString(Seed):
    """
    String seed implementation
    """
    def __getitem__(self, index):
        """
        Return character at index.

        :param index: index of character.
        :return: str
        """
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return str(self.value)

    def __iter__(self):
        for elem in self.value:
            yield elem

    @staticmethod
    def load(filename):
        json_obj = Seed.load(filename)
        return SeedString(json_obj["seed_value"], json_obj["seed_id"], json_obj["date"])


class SeedStringArray(Seed):
    """
    SeedStringArray implementation.
    """
    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        for elem in self.value:
            yield elem

    def store(self, filename):
        with open(filename, 'w') as file_handle:
            seed_dict = {"seed_id": self.seed_id, "seed_value": self.value, "date": self.date}
            json.dump(seed_dict, file_handle, default=lambda array_elem: array_elem.value)

    @staticmethod
    def load(filename):
        json_obj = Seed.load(filename)
        return SeedStringArray(json_obj["seed_value"], json_obj["seed_id"], json_obj["date"])
