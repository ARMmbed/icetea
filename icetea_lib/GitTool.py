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
from os.path import abspath, relpath, dirname
import subprocess
import re

from icetea_lib.tools.tools import IS_PYTHON3


def get_path(filename):
    """
    Get absolute path for filename.

    :param filename: file
    :return: path
    """
    path = abspath(filename) if os.path.isdir(filename) else dirname(abspath(filename))
    return path


def get_git_root(path):
    """
    Run git rev-parse --show-toplevel in path.

    :param path: path where to run git
    :return: str
    """
    path = get_path(path)
    return __run_git(["rev-parse", "--show-toplevel"], path)[0]


def get_git_file_path(filename):
    """
    Get relative path for filename in git root.

    :param filename: File name
    :return: relative path or None
    """
    git_root = get_git_root(filename)
    return relpath(filename, git_root).replace("\\", "/") if git_root else ''


def get_commit_id(path):
    """
    Run git rev-parse HEAD in path.

    :param path: Path where git is to be run.
    :return: str or None
    """
    path = get_path(path)
    return __run_git(["rev-parse", "HEAD"], path)[0]


def get_remote_url(path, remote="origin"):
    """
    Run git config --get remote.<remote>.url in path.

    :param path: Path where git is to be run
    :param remote: Remote name
    :return: str or None
    """
    path = get_path(path)
    cmd = ["config", "--get", "remote.%s.url" % remote]
    return __run_git(cmd, path)[0]


def is_git_root_dirty(path):
    """
    Run git diff-index --quiet HEAD in path.

    :param path: path where git is to be run
    :return: str or None.
    """
    path = get_path(path)
    cmd = ["diff-index", "--quiet", "HEAD"]
    return __run_git(cmd, path)[1] != 0


def get_current_branch(path):
    """
    Run git rev-parse --abbrev-ref HEAD in path.

    :param path: path where git is to be run
    :return: str or None.
    """
    path = get_path(path)
    exe = ["rev-parse", "--abbrev-ref", "HEAD"]
    return __run_git(exe, path)[0]


def get_git_info(git_folder, verbose=False):
    """
    Detect GIT information by folder.

    :param git_folder: Folder
    :param verbose: Verbosity, boolean, default is False
    :return: dict
    """
    if verbose:
        print("detect GIT info by folder: '%s'" % git_folder)
    try:
        git_info = {
            "commitid": get_commit_id(git_folder),
            "branch": get_current_branch(git_folder),
            "git_path": get_git_file_path(git_folder),
            "url": get_remote_url(git_folder),
            "scm": "unknown",
            "scm_group": "unknown",
            "scm_path": "unknown",
            "scm_link": ""
        }
        if is_git_root_dirty(git_folder):
            git_info['dirty'] = True
    except Exception as err:  # pylint: disable=broad-except
        print("GitTool exception:")
        print(err)
        return {}

    if isinstance(git_info['url'], str):
        match = re.search(r"github\.com:(.*)\/(.*)", git_info['url'])
        if match:
            git_info["scm"] = "github.com"
            git_info["scm_path"] = match.group(2)
            git_info["scm_group"] = match.group(1)
            scm_link_end = " %s/%s" % (git_info["scm_group"],
                                       git_info["scm_path"].replace(".git", ""))
            git_info["scm_link"] = "https://github.com/" + scm_link_end
            git_info["scm_link"] += "/tree/%s/%s" % (git_info['commitid'], git_info["git_path"])

    if verbose:
        print("all git_info:")
        print(git_info)

    return git_info


def __get_git_bin():
    """
    Get git binary location.

    :return: Check git location
    """
    git = 'git'
    alternatives = [
        '/usr/bin/git'
    ]
    for alt in alternatives:
        if os.path.exists(alt):
            git = alt
            break
    return git


def __run_git(cmd, path=None):
    """internal run git command
    :param cmd: git parameters as array
    :param path: path where command will be executed
    :return: tuple (<line>, <returncode>)
    """
    exe = [__get_git_bin()] + cmd
    try:
        proc = subprocess.Popen(exe, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return None, None
    except ValueError:
        return None, None
    except OSError:
        return None, None

    out, err = proc.communicate()
    if IS_PYTHON3:
        out = out.decode("utf-8")
    if err:
        print("Cmd ('%s') fails: %s" % (' '.join(exe), err))
        return None, proc.returncode
    return out.strip(), proc.returncode


if __name__ == "__main__":
    import sys
    import json
    FILE_NAME = sys.argv[1] if sys.argv.count > 1 else "./../setup.py"
    print(json.dumps(get_git_info(FILE_NAME), sort_keys=True, indent=4))
