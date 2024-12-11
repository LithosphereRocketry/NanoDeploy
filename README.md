# NanoDeploy

## Firmware

Firmware for NanoDeploy is located in the `firmware` directory. Most day-to-day
operations are handled by that folder's Makefile.

### Build environment setup

* Install `gcc-msp430` and `gdb-msp430`.
* Install `mspdebug`. (The version on the apt repos didn't work for me, but building from source did)
* Find a way to acquire `libmsp430.so`. The easiest way is by using the one from
  a Code Composer Studio install. Alternatively, you can build it from source 
  available here: https://www.ti.com/tool/MSPDS#downloads - see below.

### Building libmsp430.so from source: a cavalcade of woes

This specifically applies to building on Linux, but I wouldn't be shocked if
similar problems exist on other platforms.

* TI's build setup is fairly atrocious. You have to manually copy object files
  (not .so or .a, .o) around as part of a normal install.
* The repo link for hidapi is no longer maintained. As of writing, use the
  libusb repo instead as it actually works.
* In newer versions of hidapi, hid-libusb.o is now hidapi/libusb/hid.o. Renaming
  the file to what TI expects seems to link fine.

### Uploading

Run `make run` to upload the code to an attached MSP430 development board.

### Debugging

Run `make gdb` to upload the code to the attached dev board and start a GDB
server session. From a separate terminal, then run `msp430-gdb`. (The included
.gdbinit file should take care of all the necessary setup.)