# NanoDeploy

## Firmware

Firmware for NanoDeploy is located in the `firmware` directory. Most day-to-day
operations are handled by that folder's Makefile.

### Build environment setup

The setup process for TI's MSP430 toolchain is pretty miserable on modern Linux.
See firmware/install-notes.md for details.

### Uploading

Run `make run` to upload the code to an attached MSP430 development board.

### Debugging

Run `make gdb` to upload the code to the attached dev board and start a GDB
server session. From a separate terminal, then run `msp430-gdb`. (The included
.gdbinit file should take care of all the necessary setup.)