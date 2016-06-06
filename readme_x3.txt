written by:  Maciej "Fiedzia" Dziardziel (maciejdziardziel@wp.pl)

=================================================================
POD X3 protocol information
=================================================================

Below are the pieces of information that i gathered so far.
There is still much to discover, i am only able get pod serial number and
(sometimes) set pod channel parameter. All info is related to POD X3 bean.

Basic pod information are in files:

  lsusb_x3       - X3 lsusb output
  lsusb_x3live   X3 live lsusb output

=================================================================
pypodx3.py
=================================================================

To make experimenting easier, i wrote simple python script to interact with pod,
see pypodx3.py in this directory. This will require libusb and python libusb bindings
(install libusb and python-usb in ubuntu). Once i will understand X3 protocol,
functionality of this script will be added to kernel module.
Unfortunately stable libusb doesn't support isochronous transfers, so it will have
to be implemented either using unstable version (but there is no ready to install python module for it)
or only in kernel module.

=================================================================
Obtaining serial number
=================================================================
To see how to get serial number i tunred on pod, then started monitoring usb then
i turned Line6 monkey on.

Monkey keeps sending series of control messages, amoung them are:

control:(bmrequesttype=0xc0, brequest= 0x67, length=4, value=0x0013, index=0x00)
which returns 4 bytes serial number (see get_serial_number method pypod.x3).

Monkey alse sends following control messages, which meaning is unknown for me.
I believe they contain firmware version, as monkey is displaying it.

control:(bmrequesttype=0xc0,brequest= 0x67, length=3, value=0x11, index=0)
which return 3 bytes: 0x20 0x10 0x00

control:(bmrequesttype=0x40,brequest= 0x67, length=0, value=0x11, index=0)

control:(bmrequesttype=0x40, brequest=0x67, length=0, value=0x0421, index=0x80d0)

control:(bmrequesttype=0xc0, brequest=0x67, length=1, value=0x0012, index=0x00)
which returns 1 byte: 0x04

=================================================================
POD X3 initialization
=================================================================
File usb_pod_start.html contains dump of messages that are send right after connecting pod
to the computer. Look also at start method in pypodx3.py - i tried to reply them all in the same form and order.

I looks that at the end of initialization pod sends bulk read reaquest to ep0x81 (0x40 bytes)
and listens to pod events - pressing pod buttons or changing its parameters generates events
that are read that way.

=================================================================
POD channel parameters
=================================================================
Setting channel param (general like volume or  treble and amp specific
like drive or presence) is done with bulk messages.
The message looks like that:

write 0x20 bytes to ep 0x01 (volume min)
1C 00 01 00 06 00 0A 40 01 03 00 15 01 00 00 00 00 00 03 00 01 00 00 00 05 00 10 3F 00 00 00 00
(the same, volume max)
1C 00 01 00 06 00 0A 40 01 03 00 15 01 00 00 00 00 00 03 00 01 00 00 00 05 00 10 3F 00 00 80 3F
(the same, volume near middle)
1C 00 01 00 06 00 0A 40 01 03 00 15 01 00 00 00 00 00 03 00 01 00 00 00 05 00 10 3F 48 B6 08 3F

looking at different parameters and their values, it seems that data above contains:
  parameter number at bytes 0x18-0x14
  parameter value at last 4 bytes, mostrly in range from 0x00 00 00 00 to 0x3F 80 00 00,
  but that depends on amp simulated

see method setparampypodx3.py and usb_volume.html for sniffer log


File usb_pod_param_change.html contains messages received when i started pressing buttons
and rotating knobs on the device (turning amp/stomp/verb/delay on/off and settingdrive/bass/middle etc.).
