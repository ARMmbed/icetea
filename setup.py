"""
Copyright 2017-2018 ARM Limited
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
from setuptools.command.install import install


DESCRIPTION = "Icetea - test framework"
OWNER_NAMES = "Joonas Nikula"
OWNER_EMAILS = "oulab.mbedcloudtesting.com@arm.com"
VERSION = "1.2.3-rc2"


def read(fname):
    """
    Utility function to cat in a file
    :param fname: filename
    :return: file content as a String
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


INSTALL_REQUIRES = [
    "prettytable<1.0",
    "requests",
    "yattag>=1.0",
    "pyserial>2.5",
    "jsonmerge>=1.4",
    "jsonschema<3.0.0",
    "mbed-ls>=1.5.1",
    "semver>=2.0",
    "mbed-flasher>=0.10.1,<0.11",
    "six>1.0"

]
TEST_REQUIRES = [
    "coverage>=4.0",
    "mock>=2.0",
    "sphinx>=1.0",
    "lxml",
    "pylint>=1.0",
    "astroid>=1.0"
]


class VerifyVersionCommand(install):
    """
    Custom command to verify that the git tag matches our version
    """
    description = "verify that the git tag matches our version"

    def run(self):
        is_ci = os.getenv("CIRCLECI")
        if is_ci:
            tag = os.getenv("CIRCLE_TAG")
            version = "v" + VERSION
            if tag != version:
                info = "Git tag: {0} does not match the"\
                       "version of this app: {1}".format(tag, version)
                sys.exit(info)
        # else: you are your own - please do not publish any releases without tag!


setup(name="icetea",
      version=VERSION,
      description=DESCRIPTION,
      long_description=read("README.md"),
      long_description_content_type='text/markdown',
      author=OWNER_NAMES,
      author_email=OWNER_EMAILS,
      maintainer=OWNER_NAMES,
      maintainer_email=OWNER_EMAILS,
      url="https://github.com/ARMmbed/icetea.git",
      packages=find_packages(include=["icetea_lib.*", "icetea_lib"]),
      data_files=[("icetea_lib", ["icetea_lib/tc_schema.json"])],
      include_package_data=True,
      keywords="armbed mbed-os mbed-cli ci framework testing automation",
      license="(R) ARM",
      tests_require=TEST_REQUIRES,
      test_suite="test",
      entry_points={
          "console_scripts": [
              "icetea=icetea_lib:icetea_main"
          ]
      },
      install_requires=INSTALL_REQUIRES,
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: OS Independent",
      ],
      cmdclass={
          "verify": VerifyVersionCommand,
      }
     )
