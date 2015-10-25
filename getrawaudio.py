#!/usr/bin/env python
"""
Reads audio data from the device through isochronous transfer.

NOTE: Due to alignment or whatever, the data is not correct. Data size of
the input endpoint is 170B, but the the actual data size is 6 * (3*2*4),
the rest bytes are filled with zero.
"""

import usb.util
import time

ID_VENDOR = 0x0e41
ID_PRODUCT = 0x414a

d = usb.core.find(idVendor = ID_VENDOR, idProduct = ID_PRODUCT)
if d is None:
	raise ValueError("not connected")

d.set_interface_altsetting(0,1)

x = []

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

for i in range(0, 100):
	nx = d.read(0x86, 16384, 1000)
	print len(nx)

	if len(nx) == 0:
		time.sleep(0.001)
		continue

	raw = []
	for i in chunks(nx, 170):
		raw += i[:144]

	d.write(0x02, nx[:len(raw)/4])
	x += [raw]

f = file("test.raw", "w")
for i in x:
	f.write(''.join(map(chr,i)))
