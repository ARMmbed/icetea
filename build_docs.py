#!/usr/bin/env python

import os
import sys
from subprocess import check_call, CalledProcessError


def build_docs(location="doc-source", target=None, library="icetea_lib"):
    """
    Build documentation for Mbed-clitest. Start by autogenerating module documentation
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

    target = "doc{}html".format(os.sep) if target is None else target
    cmd_ar = ["sphinx-build", "-b", "html", location, target]
    try:
        print("Building html documentation.")
        retcode = check_call(cmd_ar)
    except CalledProcessError as error:
        print("Documentation build failed. Return code: {}".format(error.returncode))
        return 3
    print("Documentation built.")
    return 0


if __name__ == "__main__":
    sys.exit(build_docs())