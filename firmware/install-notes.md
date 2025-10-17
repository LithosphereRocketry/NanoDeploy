# MSP430 Toolchain Setup Notes

(Note: This guide is exclusively for Linux. Windows and Mac users are on their
own.)

TI's distribution of the MSP430 GCC compiler _sucks_. It does function once it's
set up, but that setup process is truly miserable. This may go some way to
explaining why Ubuntu by-default ships the absolutely ancient GCC 4.4 for this
platofrm. This is what I needed to do to get it working.

A huge thanks to dragonmux of the 1bitsquared discord for help in setting this
up, without whom this experience would probably have caused me to give up
embedded development forever.

## Install the compiler itself

Download and extract the standalone compiler archive from TI. I set the
destination to `/opt/msp430-gcc` so future steps will assume that's the install
location - if you prefer a different location, you'll need to amend the paths
given to match.

Here is a `tar` one-liner that should put everything in the right place,
provided you make sure the folder above exists:

```sh
sudo tar --strip-components=1 -xjf msp430-gcc-9.3.1.11_linux64.tar.bz2 -C /opt/msp430-gcc/
```

Don't be tempted by the siren song of the installer - it _only_ accomplishes
extracting the contents of the archive with a pretty GUI. None of the following
additional steps will be helped by the installer.

The tools won't be on your path by default, so either symlink the tools you need
to a location that is (`~/.local/bin` is what I typically use) or add
`/opt/msp430-gcc/bin` to your path.

## Install the support libraries

The compiler distribution doesn't ship with the support libraries required to
use the chips' hardware without hard-coding addresses. (As I said above, this is
inexplicably **not** fixed by the packaged installer. The "incl. support files"
on the website is a bold-faced lie.) 

Download the support files from the same page on the website, then extract them
to `/opt/msp430-gcc/msp430-elf/include/` (notably, not the base MSP430 include
directory, but the one inside msp430-elf.) Here's a one-liner for that as well:

```sh
sudo unzip -j msp430-gcc-support-files-1.212.zip msp430-gcc-support-files/include/* -d /opt/msp430-gcc/msp430-elf/include/
```

However, this is TI, and nothing can be easy - the support libraries are also
mispackaged, with everything dumped in `include`. We need to move the linker
scripts to the `lib` folder instead:

```sh
sudo mv /opt/msp430-gcc/msp430-elf/include/*.ld /opt/msp430-gcc/msp430-elf/lib/
```

## Installing libmsp430

Of course, we aren't done. Nothing we've done so far has provided the actual
drivers and support tools for the MSP430 debugger.

TI doesn't seem to ship the actual debugger on Linux, so you need a way to get
your hands on the `mspdebug` CLI utility. At least on Ubuntu 22.04, the version
that your package manager installs doesn't work - you have to build from source.
What else is new. The good news is that with the addition of a few dependencies 
(libreadline-dev and libusb-dev, for me) the dlbeer/mspdebug repository's `make`
and `make install` work pretty painlessly.

You will still be missing the `libmsp430.so` support library. TI does ship a
built copy of this library, but it doesn't work. Thanks, TI. So we have to build
it.

First we need to clone a copy of `hidapi`. TI's guide links to a very old
version because they haven't updated their toolchain in decades - I found it
easier to use a modern one from libusb. Build it as normal - no need to install
it.

Then we need to download and extract TI's MSPDS bundle, ignoring the binaries
and using only the source code. Make sure you get the one titled
`MSPDS-OPEN-SOURCE - MSP Debug Stack Open Source Package` - the more prominently
displayed one does not work, despite seeming almost identical.

Once you've extracted the MSPDS package, from the hidapi build from before, copy
`hidapi/hidapi.h` to `ThirdParty/include/hidapi.h` and `build/libusb/hid.o` to
`ThirdParty/lib64/hid-libusb.o`. Then just `make`. TI has one last annoyance to
provide us - `make install` puts the result in /usr/local/lib, which on my
system isn't on the link path, so just manually move it to /usr/lib.\

Now, at long last, you should be able to run `make gdb` in one terminal and
`msp430-elf-gdb` in another and start debugging code. Phew.