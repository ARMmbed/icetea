import unittest
from subprocess import Popen, PIPE
import os


class TestRegression(unittest.TestCase):
    def test_regression_tests(self):
        icetea_verbose = '-vv'
        icetea_bin = "icetea"
        this_file_path = os.path.dirname(os.path.realpath(__file__))
        tc_name_list = ["test_async", "test_cli_init", "test_close_open", "test_cmdline", "test_multi_dut",
                        "test_cmd_resp", "test_serial_port"]
        test_result = []
        # start spawn tests
        for tc in tc_name_list:
            parameters = [icetea_bin, "--tcdir", this_file_path, "--tc", tc, "--failure_return_value", icetea_verbose]
            if tc == "test_cli_init":
                parameters.append("--reset")
            proc = Popen(parameters, stdout=PIPE)
            proc.communicate()

            test_result.append((tc, proc.returncode))

        raise_exception = False
        for tc, result in test_result:
            if result != 0:
                raise_exception = True
                print(tc + " failed with retCode: " + str(result))

        if raise_exception:
            raise Exception("Regression tests have failure")


if __name__ == '__main__':
    unittest.main()
