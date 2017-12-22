##############
Run management
##############

**************
IceteaManager
**************

IceteaManager is the main entry point for test run execution.


.. autoclass:: icetea_lib.IceteaManager.IceteaManager
    :members:

*********
TestSuite
*********

Test suite is the container for a suite of test cases and the logic for running the suite.

.. automodule:: icetea_lib.TestSuite.TestSuite
    :members:

************
TestcaseList
************

TestcaseList is the primary container for a set of TestcaseContainers.

.. automodule:: icetea_lib.TestSuite.TestcaseList
    :members:

**************
TestcaseFilter
**************

.. automodule:: icetea_lib.TestSuite.TestcaseFilter
    :members:

################
Test case runner
################

*****************
TestcaseContainer
*****************

TestcaseContainer is a container for a single test case.

.. automodule:: icetea_lib.TestSuite.TestcaseContainer
    :members:

*****
Bench
*****

Bench is the main test runner. It is the parent class for test cases and contains the primary
test run logic.

.. autoclass:: icetea_lib.bench.Bench
    :members:

##########
Randomizer
##########

.. automodule:: icetea_lib.Randomize
    :members:

################
Plugin framework
################

************
Plugin types
************

.. automodule:: icetea_lib.Plugin.PluginBase
    :members:

*************
PluginManager
*************

.. automodule:: icetea_lib.Plugin.PluginManager
    :members:

###############
Event framework
###############

.. autoclass:: icetea_lib.Events.EventMatcher.EventMatcher
    :members:

********
Generics
********

.. automodule:: icetea_lib.Events.Generics
    :members:


###############################################
CliRequest, CliResponse and response parsing
###############################################

**********
CliRequest
**********

.. autoclass:: icetea_lib.CliRequest.CliRequest
    :members:

***********
CliResponse
***********

.. autoclass:: icetea_lib.CliResponse.CliResponse
    :members:

*****************
CliResponseParser
*****************

.. autoclass:: icetea_lib.CliResponseParser.ParserManager
    :members:

********
Searcher
********

.. automodule:: icetea_lib.Searcher
    :members:

###################
Resource management
###################

*****************
AllocationContext
*****************

.. automodule:: icetea_lib.AllocationContext
    :members:

****************
ResourceProvider
****************

.. automodule:: icetea_lib.ResourceProvider.ResourceProvider
    :members:

**************
ResourceConfig
**************

.. automodule:: icetea_lib.ResourceProvider.ResourceConfig
    :members:

*********************
ResourceRequirements
*********************

.. automodule:: icetea_lib.ResourceProvider.ResourceRequirements
    :members:

Exceptions
==========

.. autoclass:: icetea_lib.ResourceProvider.exceptions.ResourceInitError
    :members:

**********
Allocators
**********

.. automodule:: icetea_lib.ResourceProvider.Allocators.BaseAllocator
    :members:

Exceptions
==========

.. autoclass:: icetea_lib.ResourceProvider.Allocators.exceptions.AllocationError
    :members:

#######
Results
#######

******
Result
******

.. autoclass:: icetea_lib.Result.Result
    :members:

.. autoclass:: icetea_lib.ResultList.ResultList
    :members:

*****************
cloud integration
*****************

.. autoclass:: icetea_lib.cloud.Cloud
    :members:

##########
Exceptions
##########

.. automodule:: icetea_lib.TestStepError
    :members:

.. autoclass:: icetea_lib.TestStepError.TestStepTimeout
    :members:

.. autoclass:: icetea_lib.TestStepError.InconclusiveError
    :members:

#########
Reporting
#########

.. automodule:: icetea_lib.Reports.ReportBase
    :members:

.. automodule:: icetea_lib.Reports.ReportConsole
    :members:

.. automodule:: icetea_lib.Reports.ReportJunit
    :members:

.. automodule:: icetea_lib.Reports.ReportHtml
    :members:

###########################
Helpers and other internals
###########################


***************
Git integration
***************

.. automodule:: icetea_lib.GitTool
    :members:

**************
GenericProcess
**************

.. autoclass:: icetea_lib.GenericProcess.GenericProcess
    :members:

.. autoclass:: icetea_lib.GenericProcess.NonBlockingStreamReader
    :members:

.. autoclass:: icetea_lib.GenericProcess.StreamDescriptor
    :members:

**********
LogManager
**********

.. automodule:: icetea_lib.LogManager
    :members:

******
Timers
******

.. autoclass:: icetea_lib.timer.Timer
    :members:

.. autoclass:: icetea_lib.timer.Timeout
    :members:

***************
EnchancedSerial
***************

.. automodule:: icetea_lib.enhancedserial
    :members:

*********************
Wireshark integration
*********************

.. automodule:: icetea_lib.wireshark
    :members:

************************
Device connectors (DUTs)
************************

.. autoclass:: icetead_lib.DeviceConnectors.Dut.Dut
    :members:

.. autoclass:: icetea_lib.DeviceConnectors.DutConsole.DutConsole
    :members:

.. autoclass:: icetea_lib.DeviceConnectors.DutProcess.DutProcess
    :members:

.. autoclass:: icetea_lib.DeviceConnectors.DutSerial.DutSerial
    :members:

.. autoclass:: icetea_lib.DeviceConnectors.DutTcp.DutTcp
    :members:

Dut information
===============

.. automodule:: icetea_lib.DeviceConnectors.DutInformation
    :members:

*****************
Build information
*****************

.. automodule:: icetea_lib.build.build
    :members:
