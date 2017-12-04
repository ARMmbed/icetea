# Plugin framework
IcedTea implements a plugin framework that allows users to
develop their own features for select parts of the test framework.

This plugin framework is meant to replace the previous extension and
extapps. The framework is still heavily under development and should
be considered an alpha-level feature at this point in time.

## Enabling plugins
IcedTea comes stock with a set of default plugins, which are
located in icedtea_lib/Plugin/plugins. These plugins are always
automatically enabled. These default plugins are defined
in icedtea_lib/Plugin/plugins/default_plugins.py

To enable custom plugins, you can place them in
a location of your choosing (must contain an __init__.py) and tell
IcedTea the path to a file, which contains the required import
statements and a dictionary with name plugins_to_load,
which maps the names of the custom plugins to the imported classes.

An example of the file performing the plugin imports is below:

```
from Asserts import AssertPlugin
from default_parsers import DefaultParsers
from FileApi import FileApiPlugin
from HttpApi import HttpApiPlugin

plugins_to_load={
    "AssertPlugin": AssertPlugin,
    "default_parsers": DefaultParsers,
    "FileApi": FileApiPlugin,
    "HttpApi": HttpApiPlugin
}
```

This file defaults to icedtea_lib/Plugin/plugins/plugins_to_load.py and
can be set by giving IcedTea the path
with the plugin_path cli argument.

## Plugin types
Currently the plugin framework support two broad types of plugins,
both of which are described in more detail below. These types are
global (or run level) plugins and test case level plugins.

Both of these types are further split into sub types.

Currently the test case level plugins support three types of plugins:
* Parsers for implementing custom response parsers.
* Bench extension for implementing new features that attach user defined
functionality to the test bench so they can be accessed from test cases.
* External services, which can be started by IcedTea for use during
test runs.

Each plugin can implement one or several of these types.

The global plugin type currently supports just one type of plugin, which
is the allocator.

The difference between these two types of plugins is in their scope.
Test case level plugins are meant to provide new functionality and tools
to the test case, and they are loaded individually for each test case.
Global plugins are meant to provide new functionality for the entire
run and they are loaded exactly once during the run,
at the very beginning. These plugins could implement things like
reporters, resource management and logging. Of these, only resource
management via allocators is implemented at present.

## PluginBase
PluginBase is the base module for all plugins used by IcedTea.
It contains the classes used to define the plugin types.
The two classes contained in PluginBase module are PluginBase, which is
the base class for test case level plugins, and RunPluginBase, which is
the base class for global plugins. The PluginBase class is shown below
as an example, since the RunPluginBase is very similar to PluginBase.

```
class PluginBase(object):
    def __init__(self):
        pass

    def get_bench_api(self):
        return None

    def get_parsers(self):
        return None

    def get_external_services(self):
        return None

    def init(self, bench=None):
        return None

    # regexp search with one value to return
    @staticmethod
    def find_one(line, lookup):
        m = re.search(lookup, line)
        if m:
            if m.group(1):
                return m.group(1)
        return False

    # regex search with multiple values to return
    @staticmethod
    def find_multiple(line, lookup):
        m = re.search(lookup, line)
        if m:
            ret = []
            for i in range(1, len(m.groups()) + 1):
                ret.append(m.group(i))
            if ret:
                return ret
        return False
```

## Implementing custom plugins
Note that all test case level plugins can actually contain several
plugin types. The implementation does not restrict a single plugin to a
single type. To add more types, just implement the required functions as
described below.

### Response parsers
Response parsers are meant for implementing custom response parsers
for IcedTea. The parsers that are registered to Bench are
called every time a line is received from a DUT and they should return a
dictionary of desired information from the matched line. Examples
can be found from
[default parsers](../icedtea_lib/Plugin/plugins/default_parsers.py)

#### Implementing a data parser
To implement a data parser, you need to create a class,
that inherits from the PluginBase class.
A response parser type plugin needs to implement the _get_parsers_
method, which should return a dictionary of type
{parser name: callable}. Parser names need to be unique.

The callable mapped to the parser name should take one argument,
the line received from the DUT as a string.

To help with implementation, the PluginBase base class contains two
static methods, which can be used in custom parsers.
These functions are find_one(line, lookup) and find_multiple(line,
lookup). These functions can be used to find either a single match
to regular expression lookup from line or a list of matches found
from line. Both functions return False if no matches are found.

### Bench extensions
Bench extensions are meant for implementing new add-ons to the
test bench, similarly to how the old extension feature worked.
They are registered to bench during plugin registration at the
start of a test case and are accessible in test cases through the
test case self property using the name you defined for the feature
in the plugin. These extensions are also provided with
access to the bench object so they are able to utilize all bench APIs.

#### Implementing a bench extension
To implement a bench extension you need to create a class
that inherits the PluginBase class. Then you need to
implement the _get_bench_api_ method, which returns a dictionary that
maps the new functions, classes and other attributes
your plugin implements to unique names.
These names are added to the test bench object using setattr() function.
They are not allowed to overwrite existing attributes.

The PluginBenchExtension can also contain an optional init(bench=None)
method, which can be used to initialize any classes and variables your
plugin might need to function and to store the bench reference should
your plugin need some of the bench APIs.

### External Services
During test bench initialization, IcedTea can look for and start
external services you application or your tests might require.
These services are started before the test case itself starts, during
the test bench setup phase. A reference to the instance of the extapp
is added to the Bench object with the service name
as the attribute name.

#### Implementing an external service
To implement an external service type plugin,
you need to create a class, that inherits the PluginBase class.
The class should contain a method called _get_external_services_, which
should return a dictionary of format {service name: Class}. The value
is a class reference to a class that implements the actual service and
it needs to contain methods _start_ and _stop_.
These methods take no arguments and they are called before the test
to start the service and after the test to stop it.
Both of these methods should raise a PluginException
if they fail for any reason.
The class __init__ method needs to take one positional argument,
which is the string name of the service,
as well as two keyword arguments (conf: dict and bench: Bench).
The init function also needs to save the service name from arguments
into attribute name.

### Allocator
Allocators are utilities used by the IcedTea ResourceProvider class
to allocate resources needed by the test bench. These resources are
usually devices or processes being tested (DUT:s). The plugin framework
provides a way to implement custom allocators so that developers can
utilize their own resource management solutions.

#### Implementing an allocator
Allocators are implemented as global plugins, which means that only one
allocator can be used during a run. The used allocator can be selected
from the IcedTea cli using parameter --allocator.
The actual allocator plugin implementation requires two parts:
The plugin and the allocator.

The plugin is implemented in a manner similar to the other types. First
create a class that inherits the RunPluginBase class. This class must
implement the _get_allocators_ function, that returns a dictionary
mapping allocator names to their classes. These names are the ones
that are searched through when selecting the allocator to use based on
the --allocator cli parameter.

The actual allocator class needs to inherit the
[BaseAllocator](../icedtea_lib/ResourceProvider/Allocators/BaseAllocator.py)
class and implement at least the allocate-function defined there.

## Examples
Examples of different types of plugins can be found as generic examples
in the examples-folder in the repository root. More detailed examples
can be seen in the default plugins implemented in
icedtea_lib/Plugin/plugins.
