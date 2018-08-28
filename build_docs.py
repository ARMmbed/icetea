#!/usr/bin/env python

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
from subprocess import check_call, CalledProcessError


def build_docs(location="doc-source", target=None, library="icetea_lib"):
    """
    Build documentation for Icetea. Start by autogenerating module documentation
    and finish by building html.

    :param location: Documentation source
    :param target: Documentation target path
    :param library: Library location for autodoc.
    :return: -1 if something fails. 0 if successfull.
    """
    cmd_ar = ["sphinx-apidoc", "-o", location, library]
    try:
        print("Generating api docs.")
        retcode = check_call(cmd_ar)
    except CalledProcessError as error:
        print("Documentation build failed. Return code: {}".format(error.returncode))
        return 3
    except OSError as error:
        print(error)
        print("Documentation build failed. Are you missing Sphinx? Please install sphinx using "
              "'pip install sphinx'.")
        return 3

    target = "doc{}html".format(os.sep) if target is None else target
    cmd_ar = ["sphinx-build", "-b", "html", location, target]
    try:
        print("Building html documentation.")
        retcode = check_call(cmd_ar)
    except CalledProcessError as error:
        print("Documentation build failed. Return code: {}".format(error.returncode))
        return 3
    except OSError as error:
        print(error)
        print("Documentation build failed. Are you missing Sphinx? Please install sphinx using "
              "'pip install sphinx'.")
        return 3
    print("Documentation built.")
    return 0


if __name__ == "__main__":
    sys.exit(build_docs())