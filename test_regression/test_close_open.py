from icetea_lib.bench import Bench
from icetea_lib.DeviceConnectors.Dut import DutConnectionError
from icetea_lib.TestStepError import TestStepError


'''
Regression test: test open and close dut connection
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_close_open",
                       title="regression test for open and close dut connection",
                       status="development",
                       purpose="Verify dut connection",
                       component=["cmdline"],
                       type="regression",  # allowed values: installation, compatibility, smoke,
                       # regression, acceptance, alpha, beta, destructive, performance
                       requirements={
                           "duts": {
                               '*': {  # requirements for all nodes
                                    "count": 1,
                                    "type": "hardware",
                                    "allowed_platforms": ['K64F'],
                                    "application": {"bin": "examples/cliapp/mbed-os5/bin/mbed_cliapp_K64F.bin"}
                               }
                           }
                       }
                       )

    def case(self):
        # get dut
        dut = self.get_dut(1)

        # Close connection, since by default dut connection has opened already
        dut.close_connection()

        # wait a second and reopen connection
        self.delay(1)
        dut.open_connection()

        # verify connection opened successfully
        resp = self.command(1, "echo helloworld")
        resp.verify_message("helloworld", break_in_fail=True)

        # Check that exception is raised if we try to reopen connection
        try:
            dut.open_connection()
            # We should never get here, since previous line
            # should raise DutConnectionError exception
            raise TestStepError("Calling open_Connection twice didn't raise error as expected!")
        except DutConnectionError:
            pass
