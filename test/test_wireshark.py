"""
Copyright 2017 ARM Limited
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
# pylint: disable=missing-docstring,invalid-name,anomalous-backslash-in-string

import sys
import unittest
from icetea_lib.wireshark import NwPacket
from icetea_lib.wireshark import NwPacketManager
from icetea_lib.TestStepError import TestStepError
sys.path.append('.')

if sys.version_info[0] == 2:  # Python2
    import mock
else:                         # Python3
    from unittest import mock  # pylint: disable=no-name-in-module



class TestVerify(unittest.TestCase):

    def test_packetparser(self):
        string = open('test/data/BeaconRequest.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(NwPacket.verify(  # Successful
            packet,
            {"WPAN": {
                "Command Identifier": "Beacon Request",
                "Destination Addressing Mode": "Short/16-bit",
                "Destination PAN": "0xffff",
                "Frame Version": "0"
            }}
        ))
        self.assertFalse(NwPacket.verify(  # Unsuccessful
            packet,
            {"WPAN": {
                "Command Identifier": "Bacon Request",
                "Destination Addressing Moda": "Short/16-bit",
                "Destination PAN": "0xffff"
            }}
        ))

    def test_packetparser6lowpan(self):
        string = open('test/data/6lowpanping.txt', 'r').read()
        p = NwPacket(string)
        self.assertTrue(NwPacket.verify(  # Successful
            p,
            {"6LOWPAN": {
                "Destination": "fe80::166e:a00:0:2",
                "Source address compression": "Stateless",
                "Context identifier extension": "False"
            }, "ICMPV6":{
                "Response To": "17"
            }}
        ))

    def test_packetparser6lowpan2(self):
        string = open('test/data/6lowpanping2.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(NwPacket.verify(  # Successful
            packet,
            {"6LOWPAN": {
                "Destination": "fe80::166e:a00:0:2",
                "Source address compression": "Stateless",
                "Context identifier extension": "False"
            }, "UDP": {
                "Source Port": "65534"
            }, "IPV6": {
                "Source": "fe80::ff:fe00:0"
            }}
        ))

    def test_packetparser6lowpan3(self):
        string = open('test/data/6lowpanudp.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(
            NwPacket.verify(
                packet,
                {
                    "6LOWPAN": {
                        "Destination": "fd00:db8::ff:fe00:face"
                    },
                    "IPV6": {
                        "RPLInstanceID": "0x82"
                    },
                    "UDP": {
                        "Destination Port": "7"
                    }
                }
            )
        )

    def test_packetparserfullrow(self):
        string = open('test/data/rpl_dio.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(NwPacket.verify(
            packet,
            {
                "IPV6": {
                    "Source": "fe80::ff:fe00:face",
                    "Destination": "ff02::1a"
                },
                "ICMPV6": {
                    "Code": "1",
                    "*1": "ICMPv6 RPL Option \(Routing Information fd00:db8::/64\)",
                    "*2": "ICMPv6 RPL Option \(Prefix Information fd00:db8::ff:fe00:face/64\)",
                    "*3": "ICMPv6 RPL Option \(Routing Information ::/0\)"
                }
            }
        ))

    def test_packetparserlegacy(self):
        string = open('test/data/BeaconRequest.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(NwPacket.verify(
            packet,
            {
                "WPAN.Command Identifier": "Beacon Request",
                "WPAN.Destination Addressing Mode": "Short/16-bit",
                "WPAN.Destination PAN": "0xffff",
                "WPAN.Frame Version": "0"
            }
        ))
        self.assertFalse(NwPacket.verify(  # Unsuccessful
            packet,
            {
                "WPAN.Command Identifier": "Bacon Request",
                "WPAN.Destination Addressing Moda": "Short/16-bit",
                "WPAN.Destination PAN": "0xffff"
            }
        ))

    def test_packetparsermultilayer(self):
        string = open('test/data/BeaconRequest.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(NwPacket.verify(  # Successful
            packet,
            {"WPAN": {
                "Destination PAN": "0xffff"
            }, "IP": {
                "Protocol": "UDP"
            }}
        ))
        self.assertFalse(NwPacket.verify(  # Unsuccessful
            packet,
            {"WPAN": {
                "Destination PAN": "0xffff"
            }, "IP": {
                "Protocol": "XXX"
            }}
        ))

    def test_packetparserregexvalue(self):
        string = open('test/data/BeaconRequest.txt', 'r').read()
        packet = NwPacket(string)
        self.assertTrue(NwPacket.verify(
            packet,
            {"WPAN":{
                "Destination PAN": "0xfff[abcdef]"
            }, "IP":{
                "Protocol": "KGB|UDP|VH1"
            }}
        ))

    @mock.patch('icetea_lib.LogManager.get_bench_logger')
    def test_packetmangager_happyday(self, loggerpatch):
        loggerpatch.return_value = mock.MagicMock()
        p1 = open('test/data/BeaconRequest.txt', 'r').read()
        p2 = open('test/data/BeaconRequest2.txt', 'r').read()
        manager = NwPacketManager()
        manager.push(p1)
        manager.push(p2)
        self.assertTrue(manager.verifyPackets([{
            "WPAN":{
                "Command Identifier": "Beacon Request",
                "Destination PAN": "0xffff",
                "Sequence Number": "79"
            }
        }]) is None)

    @mock.patch('icetea_lib.LogManager.get_bench_logger')
    def test_packetmangager_sadday(self, loggerpatch):
        loggerpatch.return_value = mock.MagicMock()
        p1 = open('test/data/BeaconRequest.txt', 'r').read()
        p2 = open('test/data/BeaconRequest2.txt', 'r').read()
        manager = NwPacketManager()
        manager.push(p1)
        manager.push(p2)
        with self.assertRaises(TestStepError):
            self.assertTrue(manager.verifyPackets([{
                "WPAN": {
                    "Command Identifiers": "Bacon Request",
                    "Destination PAN": "0xffff"
                }
            }]) is None)
        with self.assertRaises(TestStepError):
            self.assertTrue(manager.verifyPackets([{
                "WPAN": {
                    "Command Identifier": "Beacon Request",
                    "Destination PAN": "0xffff",
                    "Sequence Number": "80"
                }
            }]) is None)

    @mock.patch('icetea_lib.LogManager.get_bench_logger')
    def test_packetcounter6lowpan(self, loggerpatch):
        loggerpatch.return_value = mock.MagicMock()
        p1 = open('test/data/BeaconRequest2.txt', 'r').read()
        p2 = open('test/data/6lowpanping.txt', 'r').read()
        p3 = open('test/data/BeaconRequest.txt', 'r').read()
        p4 = open('test/data/6lowpanping2.txt', 'r').read()
        manager = NwPacketManager()
        manager.push(p1)
        manager.push(p2)
        manager.push(p3)
        manager.push(p4)
        self.assertTrue(manager.countPackets({
            "WPAN": {
                "Extended Source": "14:6e:0a:00:00:00:00:01",
            },
            "IPV6": {
                "Destination": "fe80::166e:a00:0:2"
            }
        }) == 2)

    '''
    # these test needs sniffer HW and valid configurations.
    def test_liveCapture(self):

        wshark = Wireshark()
        wshark.startCapture('wireshark.pcap')
        time.sleep(5)
        wshark.setMark('marker#1')
        time.sleep(1)
        wshark.setMark('marker#2')
        self.assertIsInstance( wshark.stopCapture(), int )

        self.assertEqual( wshark.findIndexByMark('start'), 0 )
        self.assertEqual( wshark.findIndexByMark('unknown'), None )

        self.assertGreaterEqual( wshark.findIndexByMark('marker#1'), wshark.findIndexByMark('marker#2') )

    def test_wireshark(self):
        capture = pyshark.LiveCapture(interface='Sniffer')
        print('Start Live capturing')
        capture.sniff(timeout=10)
        for packet in capture.sniff_continuously(packet_count=50):
            print 'Just arrived:', packetl
        print("Stop Live Capturing")
        print( capture )
        for packet in capture:
            print(packet)
        import netifaces
        print( netifaces.inter() )
        print( capture.interfaces )

        self.assertTrue(True)
        with self.assertRaises(LookupError):
            self.assertTrue(raise LookupError())
    '''  # pylint: disable=pointless-string-statement


if __name__ == '__main__':
    unittest.main()
