######################
Command Line Interface
######################

Communication between a test case and the Device Under Test (DUT)
takes place via the Command Line Interface.

The library used currently on the device side is
`cli library <https://github.com/ARMmbed/mbed-client-cli>`_
(`yotta <yotta.mbed.com>`_ package). It contains the functionality for:

* Shell input characters.
* Displaying data.
  * Handling of [VT100](https://en.wikipedia.org/wiki/VT100).
* Command execution.
* Basic command parsing functions.

The cli library **does not**:

* encapsulate command parameters
* verify allowed parameters