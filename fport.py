#!/usr/bin/env python3
import struct
import array
import bitstruct

FRAME_HEAD = 0x7e
ESCAPE_CHAR = 0x7D
ESCAPE_XOR_VALUE = 0x20
FRAME_TYPE_CONTROL = 0x00
FRAME_TYPE_DOWNLINK = 0x01
FRAME_TYPE_UPLINK = 0x81
PRIM_NULL = 0x00
PRIM_DATA = 0x10
PRIM_READ = 0x30
PRIM_WRITE = 0x31
PRIM_RESPONSE = 0x32

FRAME_INDEX_LEN = 0
FRAME_INDEX_TYPE = 1
FRAME_INDEX_CRC = -1


class FportMessage(object):
    implementations = {0: 'FportMessageControl', 1: 'FportMessageDownlink'}

    def __init__(self, message):
        pass

    @staticmethod
    def build_message(frame):
        if frame.valid:
            typename = FportMessage.implementations[frame.type]
            t = globals()[typename]
            return t(frame)
        else:
            print("Invalid Frame!", frame)
            return None


class FportMessageControl(FportMessage):
    format=bitstruct.compile('u11u11u11u11u11u11u11u11u11u11u11u11u11u11u11u11u4u1u1u1u1<')
    def __init__(self, message):
        # S.Bus like structure:
        # 16 * 11bit channels:
        # 0  [ ch1.7 ch1.6 ch1.5 ch1.4 ch1.3 ch1.2 ch1.1 ch1.0]
        # 1  [ ch2.4 ch2.3 ch2.2 ch2.1 ch2.0 ch1.10 ch1.9 ch1.8]
        # 2  [ ch3.1 ch2.0 ch2.10 ch2.9 ch2.8 ch2.7 ch2.6 ch2.5]
        # ...
        # 21 [ ch16.10 ch16.9 ch16.8 ch16.7 ch16.6 ch16.5 ch16.4  ch16.3]
        # 22 flag byte [0 0 0 0 failsafe frame_lost ch18 ch17]
        print(message.frame)
        data = t.format.unpack(message.frame)
        self.axis = data[0:16]
        self.switches = data[16:18]
        self.frame_lost = data[18]
        self.failsafe = data[19]
        pass

    def __str__(self):
        return "Control - ax:{}, sw:{}, frame Lost/FS: {}/{}".format(self.axis, self.switches, self.frame_lost, self.failsafe)


class FportMessageDownlink(FportMessage):
    def __init__(self, message):
        self.prim = message.frame[0]
        self.app_id_l = message.frame[1]
        self.app_id_h = message.frame[2]
        self.data = message.frame[3:7]
        pass

    def __str__(self):
        return "Downlink - Prim:{}, AppId:{}/{}, data:{}".format(
               self.prim, self.app_id_l, self.app_id_h, self.data)


class FportFrame(object):
    def __init__ (self, packet):
        self.len = 0
        self.type = FRAME_TYPE_CONTROL
        self.frame = array.array('B')
        self.crc = 0
        self.valid = False
        self.unpack(packet)

    @staticmethod
    def decode(packet):
        p2 = packet[:]
        index = 0
        # handle any escaped character
        to_fix = []
        while True:
            try:
                index = packet.index(ESCAPE_CHAR)
            except ValueError:
                return packet
            del packet[index]
            to_fix.append(index)
        for i in to_fix:
            packet[i] = packet[i] + ESCAPE_XOR_VALUE

    def unpack(self, packet):
        # remove header and trailer
        packet.remove(FRAME_HEAD)
        packet.remove(FRAME_HEAD)

        self.len = packet[FRAME_INDEX_LEN]
        if self.len > (len(packet) - 2):
            self.valid = False
            return
        self.type = packet[FRAME_INDEX_TYPE]
        self.crc = packet[FRAME_INDEX_CRC]
        self.frame = packet[FRAME_INDEX_TYPE + 1: FRAME_INDEX_CRC]
        self.frame = self.decode(self.frame)
        self.valid = self.check_crc(packet)

    def __str__(self):
        return "Message: Len:{}, Type:{}, CRC:{}, VALID:{}, Data:{}".format(
               self.len, self.type, self.crc, self.valid, self.frame)

    def check_crc(self, packet):
        crc = sum(packet) % 0xFF
        return crc == 0


class FportParser(object):
    def __init__(self, message_handler):
        self.buffer = array.array('B')
        self.packet = array.array('B')
        self.message_handler = message_handler

    def on_message(self, packet):
        message = FportMessage.build_message(packet)
        if self.message_handler:
            self.message_handler(message)
        else:
            print('No handler set, received:', message)

    def parse(self, data):
        self.buffer.frombytes(data)

        while len(self.buffer) > 0:
            is_packet_started = len(self.packet) > 0
            try:
                index = self.buffer.index(FRAME_HEAD)
            except ValueError:
                if is_packet_started:
                    self.packet.frombytes(self.buffer[:])
                del self.buffer[:]
                break
            index = index + 1

            if is_packet_started:
                # looking for a trailer symbol
                self.packet.frombytes(self.buffer[:index])
                if len(self.packet) > 2:
                    #try:
                    message = FportFrame(self.packet)
                    self.on_message(message)
                    #except:
                    #    print("failure", self.packet)
                else:
                    # Empty packet, the trailer is actually a lead for the next packet
                    index = index - 1
                del self.packet[:]
            else:
                self.packet.append(FRAME_HEAD)
            del self.buffer[:index]
