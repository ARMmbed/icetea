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

from icetea_lib.tools.tools import hex_escape_str, import_module, check_int
from icetea_lib.tools.tools import combine_urls, test_case, flush_queue, get_abs_path
from icetea_lib.tools.tools import generate_object_graphs_by_class, num, is_pid_running
from icetea_lib.tools.tools import get_fw_name, get_fw_version, get_number
from icetea_lib.tools.tools import recursive_dictionary_get, get_pkg_version
from icetea_lib.tools.tools import sha1_of_file, strip_escape, load_class
from icetea_lib.tools.tools import remove_empty_from_dict, Singleton
from icetea_lib.tools.tools import UNIXPLATFORM, IS_PYTHON3, set_or_delete, split_by_n
