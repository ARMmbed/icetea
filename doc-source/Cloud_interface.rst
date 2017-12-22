###############
Cloud interface
###############

Icetea contains a wrapper for separate cloud storage clients to
enable the use of several different backends for test results.
Icetea will try to use
`opentmi-client <https://github.com/OpenTMI/opentmi-client-python>`_ by default.

*****
Usage
*****

To enable the cloud storage functionality, run Icetea with the -w flag.
This will enable several different functionalities such as storing
the test results into a cloud database using a client.
To change the client module, run Icetea with the --cm option
and provide the installed python module as the value for that option.
The module must be a valid python module and it must be
installed into the system so that the python module
loader is able to find it.

************
Requirements
************

To be compatible with Icetea the cloud client
must implement some requirements:
* The module must contain a create method which returns
an instance of the client.
    * Prototype of the function should look like this:
    * create(host, port, result_converter, testcase_converter, args)
    * The converters are optional but can be used to convert
      the Icetea result and testcase objects into formats
      supported by the backend.
* The client must contain the following methods:
    * get_suite(suite, options='')
      returns suite information as a dictionary object.
    * get_campaign_id(campaignName)
    * get_campaigns()
    * get_campaign_names(), returns list of campaign/suite names.
    * update_testcase(metadata)
    * send_result(result)
      returns new result entry as a dictionary or None.

An example client module is available at
`sample_cloud.py <../examples/sample_cloud.py>`_.