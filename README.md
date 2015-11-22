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
You'll need python + pyusb for it.

Read/write command format seem to be (almost) the same.



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

The detailed format is "decrypted" to a great degree, will be described more
closely later (or on request, whichever comes first :-) ) - but it's pretty
straight-forward in the end, no cypher/checksums seem to be involved.


Audio transfer
==============

Isochronous data has S24_3LE format, input is 8 channels / output 2 channels. Fortunately it's out-of-box compatible with ALSA.

While the control doesn't seem to be required, audio doesn't seem to work unless the host is listening for URBs (even if none arrive). Because of that, the linux driver has to provide isochronous audio and bulk handling code... Pity, I was hoping userspace will handle the bulk handling entirely.
