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

Deprecated decorator
"""

import inspect
import traceback
import warnings
import functools


def deprecated(message=""):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used first time and filter is set for show DeprecationWarning.
    """
    def decorator_wrapper(func):
        """
        Generate decorator wrapper function
        :param func: function to be decorated
        :return: wrapper
        """
        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            """
            Wrapper which recognize deprecated line from source code
            :param args: args for actual function
            :param kwargs: kwargs for actual functions
            :return: something that actual function might returns
            """
            current_call_source = '|'.join(traceback.format_stack(inspect.currentframe()))
            if current_call_source not in function_wrapper.last_call_source:
                warnings.warn("Function {} is now deprecated! {}".format(func.__name__, message),
                              category=DeprecationWarning, stacklevel=2)
                function_wrapper.last_call_source.add(current_call_source)

            return func(*args, **kwargs)

        function_wrapper.last_call_source = set()

        return function_wrapper
    return decorator_wrapper


# Print deprecated messages always. This might causes side effect
# where deprecation warnings from another dependencies are also printed but
# maybe it's not bad thing eventually.
warnings.simplefilter('always', DeprecationWarning)  # turn off filter
