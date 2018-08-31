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

import os
import sys
from distutils.core import setup
from setuptools import find_packages

DESCRIPTION = "Icetea - test framework"
OWNER_NAMES = 'Jussi Vatjus-Anttila'
OWNER_EMAILS = 'jussi.vatjus-anttila@arm.com'

INSTALL_REQUIRES = [
          "prettytable",
          "requests",
          "yattag",
          "pyserial>2.5",
          "jsonmerge",
          "mbed-ls>=1.5.1,==1.*",
          "semver",
          "mbed-flasher==0.9.*",
          "six"
      ]
if sys.version_info.major == "3":
    INSTALL_REQUIRES.append("pyshark")
else:
    INSTALL_REQUIRES.append("pyshark-legacy")


# Utility function to cat in a file (used for the README)
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='icetea',
      version='1.0.1',
      description=DESCRIPTION,
      long_description=read('README.md'),
      author=OWNER_NAMES,
      author_email=OWNER_EMAILS,
      maintainer=OWNER_NAMES,
      maintainer_email=OWNER_EMAILS,
      url='https://github.com/ARMmbed/icetea.git',
      packages=find_packages(include=["icetea_lib.*", "icetea_lib"]),
      data_files=[('icetea_lib', ['icetea_lib/tc_schema.json'])],
      include_package_data=True,
      license="(R) ARM",
      tests_require=["coverage", "netifaces", "mock"],
      extras_require={
          "colors": ["coloredlogs"]
      },
      test_suite='test',
      entry_points={
          "console_scripts": [
              "icetea=icetea_lib:icetea_main"
          ]
      },
      install_requires=INSTALL_REQUIRES
    )
