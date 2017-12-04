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

import time
import pyshark
from threading import Thread
from threading import Lock
import sys
import re
from datetime import datetime
from icedtea_lib.TestStepError import TestStepError
import icedtea_lib.LogManager as LogManager


class NwPacket:

    @staticmethod
    def verify(packet, expectedValues):
        lines = packet.packetStr.splitlines()
        field_values = dict() # field keys assumed to be unique accross layers
        for layer_key, layer_value in expectedValues.items():
            # support for legacy JSON interface
            if re.match("^.+\..+", layer_key):
                layer_key, field_key = layer_key.split('.')
                layer_value = { field_key : layer_value }
            layer_found = False
            for line in lines:
                if layer_found == False:
                    m = re.search("^Layer "+layer_key+":", line)
                    if m == None:
                        continue
                    layer_found = True
                for field_key, field_value in layer_value.items():
                    if field_key in field_values and field_values[field_key] == True:
                        continue
                    else:
                        field_values[field_key] = False
                    # Whole row match (key starts with '*')
                    if field_key.startswith("*"):
                        m = re.search("(\t)" + field_value, line)
                        if m != None:
                            field_values[field_key] = True
                        continue
                    m = re.search("(\t|(, )|= )"+field_key+":[\s]{0,}([^,]*)[,]{0,1}", line)
                    if m == None:
                        continue
                    if re.search(field_value, m.group(3)):
                        field_values[field_key] = True
                    else:
                        continue
            if layer_found == False:
                return False
            for field_key, field_value in field_values.items():
                if field_value == False:
                    return False
        return True

    def __init__(self, packet, mark=None):
        self.__marks = []
        self.timestamp = datetime.now()
        self.packetStr = str(packet)
        self.appendMark(mark)

    def isMark(self, mark ):
        return mark in self.__marks

    def appendMark(self, mark ):
        if mark:
            self.__marks.append( mark )

    def __str__(self):
        return str(self.packet)

    def getMarks(self):
        return ','.join(self.__marks)

class NwPacketManager:

    def __init__(self):
        self.__packets = []
        self.__marks = []
        self.__lock = Lock()
        self.setMarkForHead('start')
        self.logger = LogManager.get_bench_logger("bench", "WS")

    def setMarkForHead(self, mark):
        if self.hasPackets():
            #set mark
            self.__packets[-1].appendMark( mark )
            return

        self.__lock.acquire()
        self.__marks.append( mark )
        self.__lock.release()

    def push(self, packet, mark = None):
        packet = NwPacket(packet)

        self.__lock.acquire()
        while len(self.__marks)>0:
                packet.appendMark( self.__marks.pop() )
        self.__lock.release()

        self.__packets.append( packet  )
        #print("Got packet, count now: %i" % len(self))

    def count(self):
        return len(self.__packets)

    def getPackets(self):
        return self.__packets

    def lastPacketIndex(self):
        return len(self.__packets)-1

    def hasPackets(self):
        return len(self.__packets) > 0

    def __getitem__(self, index):
        return self.__packets[index].packet

    ''' print packet to console between markers.
    By default it prints all packets from beginning to end.
    usage example:
    self.wshark.setMark("S1")
    self.delay(10)
    self.wshark.setMark("S2")
    self.wshark.printPackets("S1", "S2")
    '''
    def printPackets(self, startMarker='start', endMarker=None):
        if not self.hasPackets():
            raise ValueError("Not packets available")

        startIndex = self.findIndexByMark(startMarker)
        endIndex = self.lastPacketIndex() if endMarker == None else self.findIndexByMark(endMarker)
        for n in range(startIndex, endIndex):
            print(self[n])

    # verify packet(s) that it contains valid contents
    # Usage example:
    #   verifyPackets( [{"WPAN": {"Command Identifier": "Beacon Request"}}] )
    #     OR  verifyPackets( [{"WPAN.Command Identifier": "Beacon Request"}] )
    # raise TestStepError exception if packet(s) not contains expected content
    def verifyPackets(self, expectedPackets, startMarker='start', endMarker=None ):

        if not self.hasPackets():
            raise ValueError("Not packets available")

        startIndex = self.findIndexByMark(startMarker)
        endIndex = self.lastPacketIndex() if endMarker == None else self.findIndexByMark(endMarker)

        ok, expectedThatNotFound, packet = self.__verifyPackets(expectedPackets, startIndex, endIndex)
        if not ok:
            # @todo print why packet didn't match to expected
            raise TestStepError("Packet not found: " + str(expectedThatNotFound))

        self.logger.debug("verifyPackets success")

    # Count number of packets that match the given specifications (packet fields)
    # Usage example:
    #   countPackets( {"IPV6":{"Destination":"fe80::166e:a00:0:2"}} )
    def countPackets(self, expectedPacket, startMarker='start', endMarker=None):

        if not self.hasPackets():
            raise ValueError("Not packets available")

        startIndex = self.findIndexByMark(startMarker)
        endIndex = self.lastPacketIndex() if endMarker == None else self.findIndexByMark(endMarker)

        count = self.__countPackets(expectedPacket, startIndex, endIndex)
        return count

    def findIndexByMark(self, mark):
        index = 0
        for pck in self.__packets:
            if pck.isMark(mark):
                return index
            index += 1
        return None

    def FindNext(self, expectedPacket, begIndex, toIndex):
        for index in range(begIndex, toIndex+1):
            ok = NwPacket.verify( self.__packets[index], expectedPacket )
            if ok:
                return True, index, self.__packets[index]
        raise LookupError("Not found")

    def __verifyPackets(self, expectedPackets, startIndex, endIndex):
        position = startIndex
        for expectedContent in expectedPackets:
            try:
                ok, position, match = self.FindNext(expectedContent, position, endIndex)
                if ok == False:
                    return False, expectedContent, match
                position = position + 1
            except LookupError as msg:
                #Not found
                #print("Not Found: %s" % msg)
                return False, expectedContent, None
        return True, None, None

    def __countPackets(self, expectedContent, startIndex, endIndex):
        position = startIndex
        count = 0
        ok = True
        try:
            while ok == True:
                ok, position, match = self.FindNext(expectedContent, position, endIndex)
                if ok == True:
                    count = count + 1
                position = position + 1
        except LookupError as msg:
            return count
        return count

class Wireshark(NwPacketManager):

    __iface = 'Sniffer'
    __captureThreadFile = None

    fileLoggingCapture = None
    liveCapture = None

    def __init__(self):
        NwPacketManager.__init__(self)
        self.logger = LogManager.get_bench_logger("bench", "WS")

    def setMark(self, mark):
        self.setMarkForHead(mark)

    # Start live network capturing to a file
    def startCapture(self, iface, file, tshark_arguments = None):
        self.__iface = iface
        if file:
            # first capture data to a file
            self.logger.debug('Start wireshark capturing to a file: %s', file)
            kwargs = dict(iface=self.__iface, file=file)
            if isinstance(tshark_arguments, dict):
                for key in tshark_arguments.keys():
                    kwargs[key] = tshark_arguments[key]
            self.__captureThreadFile = Thread(target=self.__sniffToFile, kwargs=kwargs)
            self.__captureThreadFile.setName("NW file capture")
            self.__captureThreadFile.start()

        # capture live data to a python side..
        kwargs = dict(iface=self.__iface)
        if isinstance(tshark_arguments, dict):
            for key in tshark_arguments.keys():
                    kwargs[key] = tshark_arguments[key]
        self.__captureThreadLive = Thread(target=self.__liveCapture, kwargs=kwargs)
        self.__captureThreadLive.setName("NW live capture")
        self.__captureThreadLive.start()

    # Load captured packets from a file
    def loadCapture(self, file):
        self.logger.debug('Loading capture file: %s', file)
        capture = pyshark.FileCapture(input_file=file)
        if capture == None:
            raise ValueError('Loading capture file FAILED.')
        for packet in capture:
            self.push(packet)
        self.logger.debug('Done loading capture file.')

    # Stop live network data logging
    def stopCapture(self):
        if self.fileLoggingCapture:
            self.fileLoggingCapture.close()
            self.__captureThreadFile.join( timeout = 5 )
        self.liveLoggingCapture.close()
        self.__captureThreadLive.join( timeout = 5 )
        return self.count()

    # Get captured packets
    def getCaptures(self):
        return self.getPackets()

    #Once pyshark supports it, add preference overriding arguments
    def __liveCapture(self, iface, decode_as=None):
        self.logger.debug("Sniffing if: '%s' -> live" % (iface))
        self.liveLoggingCapture = pyshark.LiveCapture( interface=iface, decode_as=decode_as)
        for packet in self.liveLoggingCapture.sniff_continuously():
            self.push(packet)
        self.logger.debug("live sniffing ends")

    #Once pyshark supports it, add preference overriding arguments
    def __sniffToFile(self, iface, file, decode_as=None):
        self.logger.debug("Sniffing if: '%s' -> file: %s" % (iface, file))
        self.fileLoggingCapture = pyshark.LiveCapture(interface=iface, output_file=file, decode_as=decode_as)
        ret = self.fileLoggingCapture.sniff()
        self.logger.debug("file sniffing ends")
