#!/usr/bin/env python
"""
Simple POD x3 control utility, written to test pod functionality.
Warning: this code may remove your warranty, erase firmware, eat your dog and so on. Use at your own risk.
libusb and python bindings are required.
This code is released under GPL v2. Have fun.

NOTE:
	before using, look at the end of the file and uncomment functon calls you want to use

USAGE:
	Turn on pod
	remove line6usb kernel module, using rmmod or (better) delete it or disable it.
	wait few seconds
	look at the end of this file and comment/uncomment function calls you want to test
	type python pypodx3.py in console
	it sometimes doesn't work for the first time, works for the second and then doesn't work until pod is turned off and on again.
	
	You can get interactive console: comment pod.close() call and run it using python -i pypodx3.py
	then you can control pod object

"""

import sys, time, math, array, struct, string
import usb
import struct
import threading

def formathex(buffer):
    """ return buffer content as hex formatted bytes """
    buf2 = []
    if buffer is None or len(buffer) == 0:
        return ""
    for item in buffer:
        buf2.append("%02X"%(item))
    return string.join(buf2," ")

class DeviceDescriptor(object) :
    def __init__(self, vendor_id, product_id, interface_id) :
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.interface_id = interface_id

    def getDevice(self):
        """
        Return the device corresponding to the device descriptor if it is
        available on a USB bus.  Otherwise, return None.  Note that the
        returned device has yet to be claimed or opened.
        """
        buses = usb.busses()
        for bus in buses :
            for device in bus.devices :
                if device.idVendor == self.vendor_id :
                    if device.idProduct == self.product_id :
                        return device
        print "no device"
	sys.exit(1)

class POD():
    VENDOR_ID     = 0x0E41   #: Vendor Id
    PRODUCT_ID    = 0x414A   #: Product Id for POD X3 bean
    INTERFACE_ID  = 1        #: The interface we use to talk to the device
    #BULK_IN_EP   = 0x86     #: Endpoint for Bulk reads
    #BULK_OUT_EP  = 0x01     #: Endpoint for Bulk writes
    PACKET_LENGTH = 0x40     #: 64 bytes
    device_descriptor = DeviceDescriptor(VENDOR_ID, PRODUCT_ID, INTERFACE_ID)

    def __init__(self,) :
      # The actual device (PyUSB object)
      self.device = self.device_descriptor.getDevice()
      # Handle that is used to communicate with device. Setup in L{open}
      self.handle = None
   
    def open(self) :
        #self.device = self.device_descriptor.getDevice()
        if not self.device:
            print >> sys.stderr, "POD isn't plugged in"
        try:
            self.handle = self.device.open()
            #self.handle.detachKernelDriver(0)
            #self.handle.detachKernelDriver(1)
            #self.handle.detachKernelDriver(2)
        except usb.USBError, err:
            print >> sys.stderr, "err:",err
    
    def getConf(self):
        """ return device selected configuration """
        reqType = 0x80
        resp = self.handle.controlMsg(reqType, usb.REQ_GET_CONFIGURATION, 1, value=0x0000, index=0x00)
        if len(resp) > 0:
            print "configuration:", resp
        return resp[0]
    
    def getIf(self):
        """ return device selected interface """
        reqType = 0x80
        resp = self.handle.controlMsg(reqType, usb.REQ_GET_CONFIGURATION, 1, value=0x0000, index=0x00)
        if len(resp) > 0:
            print "configuration:", resp
        return resp[0]
    
    def setguitarmic(self):
        """ set guitar/mic mode """
        try:
            print "g/m:start bulk write"
            buf = [0x18, 0x00, 0x01, 0x00, 0x05, 0x00, 0x0A, 0x40, 0x01, 0x03, 0x00, 0x16, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x16, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]
            sent = self.handle.bulkWrite(0x01,buf)
            print "past write", sent
        except Exception, e:
            print "exception in bulkWrite:"
            print e

    def readData(self, dataLen, addr):
        resp = self.handle.controlMsg(0x40, 0x67, 0, value=(dataLen << 8) | 0x21, index=addr)
        print "resp (ACK)", formathex(resp)
        resp = self.handle.controlMsg(0xC0, 0x67, 1, value=0x12, index=0x00)
        print "resp (x12)", formathex(resp)
        resp = self.handle.controlMsg(0xC0, 0x67, dataLen, value=0x13, index=0x00)
        print "resp (x13)", formathex(resp)
        return resp

    def init(self):
        """ pod initialization - trying to do the same things the original driver does during X3 startup """
        print "set configuration..."
        print self.handle.setConfiguration(1)
        print "---init (20 10 04...)"
        resp = self.handle.controlMsg(0xC0, 0x67, 3, value=0x11, index=0x00)
        print "resp:", formathex(resp)
        
        print("-- INIT F000...F080")
        #a sequence i don;t understand yet
        bytes = [0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70, 0x78, 0x80]
        for item in bytes:
            # This looks exactly like $linuxdrv/driver.c/line6_read_data()
            self.readData(8, 0xF000 | item)
            resp = self.handle.controlMsg(0x40, 0x67, 0, value=0x0201, index=0x02)
            print "resp (x201)", formathex(resp)

        print "wake up"
        resp = self.handle.controlMsg(0x00, usb.REQ_SET_FEATURE, 0, value=0x01, index=0x00)
        print "resp", formathex(resp)
        print "claim interface 0x1"
        self.handle.claimInterface(1)

        #data = [0x0C, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02, 0x40, 0x02, 0xF0, 0x01, 0x00, 0x00, 0x00, 0x00, 0xFF]
        data = [0x0C, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02, 0x40, 0x02, 0xEE, 0x01, 0x00, 0x00, 0x00, 0x00, 0xFF]
        print "write 0x10 bytes to ep 0x01"
        resp = self.handle.bulkWrite(0x01, data)
        print "resp", resp
        
        print "read 0x40 bytes from ep0x81"
        # looks like [len ?? flag ??] + len * bytes
        # flag ==0x01: first packet
        # flag ==0x04: continuation of previous?
        resp = self.handle.bulkRead(0x1, 0x40)
        print "resp", formathex(resp)

    def close(self):  
        """ Release device interface """
        try:
            #self.handle.reset()
            self.handle.releaseInterface()
        except Exception, err:
            print >> sys.stderr, err 

    def setparam(self, paramnum, value_percent):
        """
        set channel parameter value
        most , if not all, values are in range 0x00 00 00 00 - 0x3f 80 00 00
        """
        buf = [0x1C, 0x00, 0x01, 0x00, 0x06, 0x00, 0x0A, 0x40, 0x01, 0x03, 0x00, 0x15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x05, 0x00, 0x10, 0x3F, 0x00, 0x00, 0x00, 0x00]
        maxval = 0x3f800000
        val = (maxval/100) * value_percent
        try:
            #help(self.handle.bulkWrite)
            buf[0x18] = paramnum
            paramval = struct.pack('i', val)
            buf[0x1c] = ord(paramval[0])
            buf[0x1d] = ord(paramval[1])
            buf[0x1e] = ord(paramval[2])
            buf[0x1f] = ord(paramval[3])
            print 'val=',paramval, 'paramnum=', paramnum
            print formathex(buf)
            print "start bulk write"
            sent = self.handle.bulkWrite(1,buf,100)
            print "past write", sent
            #sent = self.handle.bulkWrite(0x01,buf,100)
            #print "past write2", sent
            #this message can be see in usb dumps everythime after changing param value,
            #however it appears only once after cranking param up and down constantly
            resp = self.handle.controlMsg(0xc0, 0x67, 0x03, value=0x11, index=0x00)
            print "resp", resp
        except Exception, e:
            print "exception in bulkWrite:",e

    def get_serial_number2(self):
        d = self.readData(4, 0x80d0)
        print "POD Serial: %d" % (struct.unpack('<I', ''.join([chr(i) for i in d])))

class PacketCompleter(threading.Thread):
    MAX_DELAY = 0.1

    def __init__(self):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.curData = []
        self.lastTime = None

    def run(self):
        while True:
            self.lock.acquire()
            if self.curData == []:
                self.lock.release()
                time.sleep(0.1)
                continue

            if self.lastTime + PacketCompleter.MAX_DELAY < time.time():
                self.packetComplete()

            self.lock.release()

    def appendData(self, data):
        self.lock.acquire()
        if data[2] == 0x01:
            if self.curData != []:
                self.packetComplete()
                self.curData = []
        elif data[2] == 0x04:
            if self.curData == []:
                print("ERROR: Continuing data, but no previous packet stored?!")

        # print "++ ", formathex(data)
        self.curData += data[4:]
        self.lastTime = time.time()
        self.lock.release()

    def packetComplete(self):
        data = self.curData
        self.curData = []
        self.lastTime = None

        print formathex(data)

pod = POD()
pod.open()
pod.init()
pod.get_serial_number2()
pc = PacketCompleter()
pc.start()

while True:
    try:
        resp = pod.handle.bulkRead(0x1, 0x40)
        pc.appendData(resp)
    except:
        pass

#pod.setparam(5, 10)
#pod.setguitarmic()
pod.close()
