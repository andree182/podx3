podx3
=====

Linux kernel now contains support for some Line6 PODs, but not X3, and
apparently also not for settings manipulation.

This code is partly based on what was already done in
http://sourceforge.net/p/line6linux/ (esp. the x3 branch). Some userspace
stuff+docs will be dumped here - linux driver modifications will hopefully be
kept in linux kernel eventually :-)



pypodx3.py
==========

This tool can be used to dump the commands used to configure the pod.
You'll need python + pyusb for it. Just execute it and you should, ideally,
start seeing decoded incoming stuff from the POD  (i.e. you need to turn knobs
etc.). Ctrl+C terminates it.

Read/write command format seem to be (almost) the same, for the future
reference - except for some direction flags/addresses. Some messages may be
uni-directional though (to-be-researched).

If it doesn't work, make sure line6usb driver is not loaded, and/or that you
have sufficient permissions (sudo).


Sample output:

%<------------------------------------------------------------------------------
no kernel driver attached
set configuration...
-- init (expecting 20 10 04)
resp: 20 10 04
-- INIT F000...F080
87 FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
BF FF FF FF FF FF 1F FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
FF FF FF FF FF FF FF FF
POD Serial: 1620786
< INT 0 / 5|5 -> 0|0
< INT 0 / 5|5 -> 1|0
< FLT 0|3 / 1|0 | 5 -> 0.516129 
< FLT 0|3 / 1|0 | 5 -> 0.512219 
< FLT 0|3 / 1|0 | 5 -> 0.508309 
< FLT 0|3 / 1|0 | 5 -> 0.504399 
< FLT 0|3 / 1|0 | 5 -> 0.502444 
< FLT 0|3 / 1|0 | 5 -> 0.498534 
< FLT 0|3 / 1|0 | 5 -> 0.496579 
< FLT 0|3 / 1|0 | 5 -> 0.492669 
< FLT 0|3 / 1|0 | 5 -> 0.490714 
< FLT 0|3 / 1|0 | 5 -> 0.487781 
< FLT 0|3 / 1|0 | 5 -> 0.485826 
< FLT 0|3 / 1|0 | 5 -> 0.481916 
< FLT 0|3 / 1|0 | 5 -> 0.479961 
< FLT 0|3 / 1|0 | 5 -> 0.477028 
< FLT 0|3 / 1|0 | 5 -> 0.473118 
< FLT 0|3 / 1|0 | 5 -> 0.469208 
< FLT 0|3 / 1|0 | 5 -> 0.465298 
< FLT 0|3 / 1|0 | 5 -> 0.461388 
< FLT 0|3 / 1|0 | 5 -> 0.457478 
< FLT 0|3 / 1|0 | 5 -> 0.455523 
< FLT 0|3 / 1|0 | 5 -> 0.451613 
< FLT 0|3 / 1|0 | 5 -> 0.449658 
< FLT 0|3 / 1|0 | 5 -> 0.448680 
< FLT 0|3 / 1|0 | 5 -> 0.452590 
< FLT 0|3 / 1|0 | 5 -> 0.456501 
< FLT 0|3 / 1|0 | 5 -> 0.461388 
< FLT 0|3 / 1|0 | 5 -> 0.467253 
< FLT 0|3 / 1|0 | 5 -> 0.473118 
< FLT 0|3 / 1|0 | 5 -> 0.478983 
< FLT 0|3 / 1|0 | 5 -> 0.484848 
< FLT 0|3 / 1|0 | 5 -> 0.489736 
< FLT 0|3 / 1|0 | 5 -> 0.494624 
< FLT 0|3 / 1|0 | 5 -> 0.496579 
< FLT 0|3 / 1|0 | 5 -> 0.497556 
< FLT 0|3 / 1|0 | 5 -> 0.500489 
< FLT 0|3 / 1|0 | 5 -> 0.501466 
< FLT 0|3 / 1|0 | 5 -> 0.502444 
ERROR: Unexpected value 'which': 35
< EffectDump: [4096] 36 30 27 73 20 52 26 42 20 20 20 20 20 20 20 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00...
< INT 0 / 0|3 -> 0|0
< INT 0 / 3|3 -> 0|0
< INT 0 / 1|3 -> 0|0
< INT 0 / 0|3 -> 1|0
< INT 0 / 3|3 -> 1|0
< INT 0 / 1|3 -> 1|0
< INT 0 / 3|2 -> 1|0
< INT 0 / 3|2 -> 0|0
< INT 0 / 3|5 -> 1|0
< INT 0 / 3|5 -> 0|0
%<------------------------------------------------------------------------------



POD bulk message format
=======================

Apparently, pod bulk messages consist of header and body.


Header
------
At least the incoming messages may not be complete. The header byte-format is:
ContentsLength ?? Flags ??

Flags is 0x01 for first packet, 0x04 for followup packets (to be appended to
previous buffer).


Contents
--------
Standard floats are used, e.g.

06 00 0A 03 00 40 00 15 00 00 00 00 00 00 03 00 01 00 00 00 05 00 10 3F DD 74 53 3F

for setting "Tone volume".

The detailed format is "decrypted" to a great degree, and is currently
documented by code in the module pypodx3_parser.py.


Audio transfer
==============

Isochronous data has S24_3LE format, input is 8 channels / output 2 channels.
Fortunately it's out-of-box compatible with ALSA.

While the control doesn't seem to be required, audio doesn't seem to work unless
the host is listening for URBs (even if none arrive). Because of that, the linux
driver has to provide isochronous audio and bulk handling code... Pity, I was
hoping userspace will handle the bulk handling entirely.
