#!/usr/bin/python3
import serial
import argparse
import typing
import time

from nano_owi_bridge import *

def select(port: serial.Serial, addr: bytes) -> None:
    cmd_write(port, 0x55, addr)

def deselect(port: serial.Serial):
    # Selecting two different devices should force all devices into idle
    select(port, bytes([0]*8))
    select(port, bytes([0xFF]*8)) # as a bonus, this is an invalid CRC

class DeviceID:
    DEVICE_CLASS = 0x49

    def __init__(self, hwver=0xFF, fwver=0xFFFF, id=0):
        self.hwver = hwver
        self.fwver = fwver
        self.id = id

    def from_bytes(data: bytes) -> typing.Any | None:
        if owi_crc(data) == 0 and data[0] == DeviceID.DEVICE_CLASS:
            return DeviceID(
                data[1],
                int.from_bytes(data[2:4], 'little'),
                int.from_bytes(data[4:7], 'little')
            )
        else:
            return None

    def __bytes__(self):
        without_crc = (bytes([DeviceID.DEVICE_CLASS, self.hwver])
                        + self.fwver.to_bytes(2, 'little')
                        + self.id.to_bytes(3, 'little'))
        return without_crc + bytes([owi_crc(without_crc)])

    def __str__(self):
        return f"<hw:{self.hwver} fw:{self.fwver} sn:{self.id}>"

def main():
    parser = argparse.ArgumentParser(
        description="Configuration tool for NanoDeploy altimeter."
    )
    parser.add_argument("port", help="Serial port to search for device on")
    args = parser.parse_args()

    with serial.Serial(args.port, 115200) as port:
        owi_id = cmd_scan(port)
        if owi_id is None:
            print("No device detected")
        else:
            dev_id = DeviceID.from_bytes(owi_id)
            if dev_id is None:
                print(f"Device {owi_id} is corrupted or not a NanoDeploy")
                print("Attempt to reflash with default config?")
            else:
                print(f"NanoDeploy detected: {dev_id}")

            cmd_write(port, 0x7A, b'') # Request barometer conversion
            time.sleep(10)
            buf = cmd_read(port, 0xB0, 64)
            print("pres:", int.from_bytes(buf[0:4], 'little'))
            print("alt:", int.from_bytes(buf[4:6], 'little'))
            print("temp:", int.from_bytes(buf[6:8], 'little'))
            # deselect(port)

if __name__ == "__main__":
    main()