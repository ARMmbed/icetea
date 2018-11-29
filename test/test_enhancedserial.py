# pylint: disable=missing-docstring

import unittest
import mock

from serial import SerialException, SerialTimeoutException

from icetea_lib.enhancedserial import EnhancedSerial


class EnhancedSerialTests(unittest.TestCase):

    def test_peek(self):
        ens = EnhancedSerial()
        self.assertEqual(ens.peek(), "")
        ens.buf = "test"
        self.assertEqual(ens.peek(), "test")

    def test_readline(self):
        with mock.patch.object(EnhancedSerial, "read") as mock_read:
            ens = EnhancedSerial()
            mock_read.side_effect = ["test\n".encode("utf-8"), "test".encode("utf-8"),
                                     SerialTimeoutException, SerialException, ValueError]
            self.assertEqual(ens.readline(), "test\n")
            self.assertIsNone(ens.readline(timeout=0))
            self.assertIsNone(ens.readline(timeout=0))
            self.assertIsNone(ens.readline(timeout=0))
            self.assertIsNone(ens.readline(timeout=0))
