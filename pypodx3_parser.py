#!/usr/bin/env python
"""
This code tries to describe + parse + generate the configuration of POD X3.
It is to be used either from pypodx3.py or standalone, if you have USB logs in
the right format (CSV from USBlyzer):

21:45:10.482,out,01:01:01,14 00 01 00 04 00 0A 40 01 03 00 20 00 00 00 00 06 00 00 00 00 00 00 00

"""

import sys, time, math, array, struct, string
import usb.util, usb.core
import struct
import threading
import signal
import struct

def pdir(port):
    if port == None:
        return ''
    if port == 0x01:
        return '<'
    else:
        return '>'

def formathex(port, data):
    if len(data) > 32:
        cont = "..."
    else:
        cont = ""
    return "%s[%04d] %s%s" % (pdir(port), len(data), " ".join("{:02x}".format(c) for c in data[:32]), cont)

def printcmd(port, name, data = None):
    print(pdir(port) + " %s: %s" % (name, data))

class EffectDump:
    def __init__(self, port, data):
        cmdData = data[7:]
        
        which = cmdData[0]
        binData = ''.join(map(chr, cmdData[1:]))
        if which != 1:
            print("ERROR: Unexpected value 'which': %d" % (which))
            return

        printcmd(port, "EffectDump", formathex(None, cmdData[1:]))

class ConfigCmd:
    def __init__(self, port, data):
        cmdData = data[7:]
        
        which = cmdData[0]
        if which == 0x21:
            # Looks like some kind of ping. When sent either way, the opposite
            # side returns INT 0 / a|0 -> 0|0 (perhaps even INT 0 / a|b -> c|d)
            a,b,c,d = cmdData[1:5]
            printcmd(port, "ConfigCmd ", "%d|%d -> %d|%d" % (a,b,c,d))
        elif which == 0x03:
            # also some kind of ping with response INT 0 / 3|0 -> 0|0
            if cmdData[1:5] != [0, 0, 0, 0]:
                printcmd(port, "ConfigCmd ", "ERROR: Unexpected non-zero's")
            printcmd(port, "ConfigCmd ", "%d|%d %d %d" % tuple(cmdData[1:5]))
        elif which == 0x00:
            # request EffectDump
            # TODO: perhaps i == -1 -> current?
            i = struct.unpack("<i", ''.join(map(chr, cmdData[1:5])))[0]
            printcmd(port, "ConfigCmd ", "Request EffectDump(%d)" % (i))
        elif which == 0x04:
            # set effect config-like thing
            i = struct.unpack("<i", ''.join(map(chr, cmdData[1:5])))[0]
            effectConfig = cmdData[5:]
            printcmd(port, "ConfigCmd ", "Send EffectDump(%d, %s)" % (i, formathex(None, effectConfig)))
        else:
            printcmd(port, "ConfigCmd ", (formathex(None, data)))

class PacketParser:
    '''
    Estimated format:
    
    u8 pkt_type;
    union {
        u8 data[256];
        struct {
            /* pkt_types 01/02/04/05/06 */
            /* input from POD:
             * usually 01: 04 0A 03 01|02 40 00 01 [...]
             * usually 04: 00 0A 03 01|02 40 00 01 [...]
             *                   ^        ^
             *                   40       30 ... output
             */
            u8 unkn1; // mostly 0 (except for pkt_type == 1/2)
            u8 unkn2; // always 0x0a
            u8 src;
            u8 flag1; // mostly 0 for incoming, 1 for out; but also 2/3...
            u8 dst;
            u8 unkn3; // mostly 0
            u8 subdata_len;
            u8 data[];
        } contents_1 ;
        struct {
            /* pkt_type 03 */
            /* 10 00 01 00 03 00 02 01 04 89|2E 40 00 00 00 00 FF 00 00 00 02 */
        } contents_2;
    } packet;
    '''
    
    def __init__(self):
        self.__types = {
            0x01: self.effectDump,
            0x02: self.configCmd,
            0x04: self.intParameter1,
            0x05: self.intParameter2,
            0x06: self.floatParameter
        }
        
    def __call__(self, port, data):
        if not self.checkDirection(port, data):
            return
        if not self.checkLength(port, data):
            return
        if not self.checkConst(port, data):
            return
        
        if data[0] in self.__types:
            self.__types[data[0]](port, data)
        else:
            print("ERROR: unknown packet type in %s" % (formathex(port, data)))

    def checkDirection(self, port, data):
        # looks like bytes 3,5 indicate the direction
        bad = False
        if port == 0x01:
            if ((data[3], data[5]) != (0x03, 0x40)):
                bad = True
        elif port == 0x81:
            if ((data[3], data[5]) != (0x40, 0x03)):
                bad = True
        if bad:
            print("ERROR: Unexpected direction: %s" % formathex(port, data))
        return not bad

    def checkLength(self, port, data):
        # bytes 7,8 look like they could contain length; TODO
        return True

    def checkConst(self, port, data):
        if data[2] != 0x0a:
            print("@2 != 0x0a: %s" % formathex(port, data))
            return False
        if data[6] != 0:
            print("@6 != 0: %s" % formathex(port, data))
            return False
        if not data[0] in [1, 2]:
            if data[1] != 0x00:
                print("@1 != 0: %s" % formathex(port, data))
                return False
        return True
    
    def effectDump(self, port, data):
        fc = EffectDump(port, data)
    
    def configCmd(self, port, data):
        se = ConfigCmd(port, data)
    
    def intParameter1(self, port, data):
        flag1 = data[4]
        cmdData = data[7:]
        
        which = cmdData[0]
        binData = ''.join(map(chr, cmdData[1:]))
        if len(binData) != 12:
            print("ERROR: Unexpected length %d" % (len(binData)))
            return False
        ints = struct.unpack("<IHHHH", binData)
        print(pdir(port) + " INT %d / %d|%d -> %d|%d" % ints)

    def intParameter2(self, port, data):
        flag1 = data[4]
        cmdData = data[7:]
        
        which = cmdData[0]
        binData = ''.join(map(chr, cmdData[1:]))
        if len(binData) != 16:
            print("ERROR: Unexpected length %d" % (len(binData)))
            return False
        ints = struct.unpack("<IIII", binData)
        print(pdir(port) + " INT %d / %d / %d -> %d" % ints)

    def floatParameter(self, port, data):
        flag1 = data[4]
        cmdData = data[7:]
        binData = ''.join(map(chr, cmdData[1:]))
        if len(binData) != 20:
            print("ERROR: Unexpected length %d" % (len(binData)))
            return False
        vals = struct.unpack("<IHHHHHHf", binData)
        if vals[0] != 0:
            print("ERROR: Unexpected value 0 (!= 0): %d" % vals[0])
            return False
        print(pdir(port) + " FLT %d|%d / %d|%d | %d -> %f " % tuple(list(vals[1:6]) + [vals[7]]))

class PacketCompleter(threading.Thread):
    '''
    struct usb_line6_podhd_message {
        u8 packet_data_len;
        u8 unkn1;
    #define PODHD_MSG_FLAG_FIRST (0x01)
    #define PODHD_MSG_FLAG_FOLLOWUP (0x04)
        u8 flags;
        u8 unkn2;

        u8 packet_data[];
    } __attribute__((packed));
    '''
    MAX_DELAY = 0.1

    def __init__(self, parser):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.curData = []
        self.lastTime = None
        self.stop = False
        self.lastPort = None
        self.parser = parser

    def run(self):
        while not self.stop:
            self.lock.acquire()
            if self.curData == []:
                self.lock.release()
                time.sleep(0.1)
                continue

            if self.lastTime + PacketCompleter.MAX_DELAY < time.time():
                self.packetComplete(self.lastPort)

            self.lock.release()

    def appendData(self, data, port = 0x01):
        ## looks like [len ?? flag ??] + [len * bytes...]
        ## flag ==0x01: first packet
        ## flag ==0x04: continuation of previous?
        self.lock.acquire()
        if data[2] == 0x01:
            if self.curData != []:
                self.packetComplete(self.lastPort)
                self.curData = []
        elif data[2] == 0x04:
            if (self.curData == []) or (self.lastPort != None and port != self.lastPort):
                print("ERROR: Continued data, but no previous packet stored")
                data = data[:4] # discard the frame
                port = self.lastPort

        # print "++ ", formathex(data)
        self.curData += data[4:]
        self.lastTime = time.time()
        self.lastPort = port
        self.lock.release()

    def packetComplete(self, port):
        data = self.curData
        self.curData = []
        self.lastTime = None

        self.parser(port, data)

p = 0x01
def myparse(pc, s):
    global p
    s = s.strip()

    if len(s) == 0:
        return
    if s.startswith('#'):
        if s.find('OUT') != -1:
            p = 0x81
        elif s.find('IN') != -1:
            p = 0x01
        return

    if s.find(',') == -1:
        # raw hex data
        d = s.split(' ')
    else:
        if s.startswith("URB"):
            return
        else:
            if s.find(',01:01:') != -1:
                d = s.split(',')[-1].split(' ')
                if d[0].find(':') != -1:
                    return
                if s.find('out,01:01:01') == -1:
                    p = 0x01
                else:
                    p = 0x81
            else:
                return

    # b = ''.join(map(lambda x: chr(int(x, 16)), d))
    b = map(lambda x: int(x, 16), d)
    pc.appendData(b, p)

if __name__ == "__main__":
    run = True
    def signal_handler(signal, frame):
        global run
        run = False
    signal.signal(signal.SIGINT, signal_handler)

    pc = PacketCompleter(PacketParser())

    while run:
        l = sys.stdin.readline()
        if l == "":
            break
        myparse(pc, l)
