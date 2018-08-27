## Developing Icetea
This document describes some information that is relevant for developers of Icetea.

### Documentation
HTML documentation for Icetea can be built using sphinx
(see Sphinx installation below).
The source for the documentation is located in
[doc-source](doc-source).

A build script for the documentation is included in [build_docs.py](build_docs.py) .
It's a simple python scripts that also
generates autodoc api documentation.
Run the script with:

`python build_docs.py`

#### Sphinx installation

* **Ubuntu linux**
    * `apt-get install python-sphinx`
* **Windows**
    * `pip install sphinx`
* **OS X**:
    * `sudo port install py27-sphinx`
    * `sudo port select --set python python27`
    * `sudo port select --set sphinx py27-sphinx`

#### Markdown documentation
The [doc](doc) folder contains a markdown copy of the rst documentation located in [doc-source](doc-source).
We try to keep both documentation formats
aligned so that they are identical, so please update
both if you make changes to the documentation.

### Running unit tests with *Icetea*
These instructions assume that you are using a linux system.
If you use Windows for development, note that tests using process duts
will be skipped.

The unit tests depend on a few extra python modules, described
in unit test dependencies below.

To build a test application for DUT and execute the test:

```
> make
> coverage run -m unittest discover -s test
```

To generate a coverage report (excluding plugins):

```
> coverage html --include "icetea_lib/*" --omit "icetea_lib/Plugin/plugins/*"
```

To run unit tests for plugins that ship with Icetea:

```
> coverage run -m unittest discover -s icetea_lib/Plugin/plugins/plugin_tests
```

To generate a coverage reports for plugin unit tests run:

```
> coverage html --include "icetea_lib/Plugin/plugins/*" --omit "icetea_lib/Plugin/plugins/plugin_tests/*"
```

#### Unit test dependencies

Unit tests depend on mock, coverage and netifaces.

```
> pip install mock
> pip install netifaces
> pip install coverage
```
