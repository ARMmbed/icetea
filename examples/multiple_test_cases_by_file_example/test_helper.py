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

def test_case(TestCaseBase, **kwargs):
    """
    Decorator which allow definition of test cases as simple functions.
    It takes two parameters:
        * TestCaseBase: this is the base class that will be used to create
        the test case. It is exected that this base class implement __init__,
        rampUp and rampDown
        * kwargs: Dictionnary of arguments that will be passed as initialization
        parameters of the test case
    """

    def wrap(case_function):
        kwargs['name'] = name = kwargs.get('name', case_function.__name__)
        class_name = "class_" + name
        case_function.func_globals[class_name] = type(
            class_name,
            (TestCaseBase,object), {
                '__init__': lambda self:
                    TestCaseBase.__init__(self, **kwargs),
                'IS_TEST': True,
                'case': case_function
            }
        )
        return case_function
    return wrap
