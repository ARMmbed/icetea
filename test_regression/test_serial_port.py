from icetea_lib.bench import Bench
from icetea_lib.Searcher import verify_message


'''
Regression test: test dut serial port and write data

Code parts under test:
    DutSerial:
        print_info()
        writeline()
        dut.comport
        dut.traces 
'''


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(self,
                       name="test_serial_port",
                       title="regression test for dut serial data communication",
                       status="development",
                       purpose="Verify dut serial",
                       component=["cmdline"],
                       type="regression",
                       requirements={
                           "duts": {
                               '*': {
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

        # print dut information
        dut.print_info()

        # get dut serial port
        self.logger.info("DUT serial port is %s" % dut.comport)

        # write data to dut
        dut.writeline(data="echo 'This is a testing line write to dut'")

        # wait 1 second
        self.delay(1)

        # verify message from trace
        verify_message(dut.traces, 'This is a testing line write to dut')
