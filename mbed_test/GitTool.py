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

import os
from os.path import abspath, relpath, dirname
import subprocess
import re


def get_path(filename):
    path = abspath(filename) if os.path.isdir(filename) else dirname(abspath(filename))
    return path


def get_git_root(path):
    path = get_path(path)
    return __run_git(["rev-parse", "--show-toplevel"], path)[0]


def get_git_file_path(filename):
    git_root = get_git_root(filename)
    return relpath(filename, git_root).replace("\\", "/") if git_root else ''



def get_commit_id(path):
    path = get_path(path)
    return __run_git(["rev-parse", "HEAD"], path)[0]


def get_remote_url(path, remote="origin"):
    path = get_path(path)
    cmd = ["config", "--get", "remote.%s.url" % remote]
    return __run_git(cmd, path)[0]


def is_git_root_dirty(path):
    path = get_path(path)
    cmd = ["diff-index", "--quiet", "HEAD"]
    return __run_git(cmd, path)[1] != 0


def get_current_branch(path):
    path = get_path(path)
    exe = ["rev-parse", "--abbrev-ref", "HEAD"]
    return __run_git(exe, path)[0]


def get_git_info(git_folder, verbose=False):
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
    except Exception as err:
        print("GitTool exception:")
        print(err)
        return {}

    if isinstance(git_info['url'], str):
        match = re.search("github\.com:(.*)\/(.*)", git_info['url'])
        if match:
            git_info["scm"] = "github.com"
            git_info["scm_path"] = match.group(2)
            git_info["scm_group"] = match.group(1)
            git_info["scm_link"] = "https://github.com/%s/%s" % (git_info["scm_group"], git_info["scm_path"].replace(".git", ""))
            git_info["scm_link"] += "/tree/%s/%s" % (git_info['commitid'], git_info["git_path"])

    if verbose:
        print("all git_info:")
        print(git_info)
        #print(json.dumps(git_info, sort_keys=True, indent=4))
        #print("....")

    return git_info


def __get_git_bin():
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
        p = subprocess.Popen(exe,
                             cwd=path,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        # print("Cmd ('%s') fails: %s" % (' '.join(exe), err.message))
        return None, None
    except ValueError as err:
        # print("Cmd ('%s') fails: %s" % (' '.join(exe), err.message))
        return None, None
    except OSError as err:
        # print("Cmd ('%s') fails: %s" % (' '.join(exe), err.message))
        return None, None

    out, err = p.communicate()
    if err:
        print("Cmd ('%s') fails: %s" % (' '.join(exe), err))
        return None, p.returncode
    else:
        return out.strip(), p.returncode
