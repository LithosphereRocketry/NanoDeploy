import enum
import serial

class Tag(enum.Enum):
    READ = 0
    WRITE = 1
    SCAN = 2
    ALARM = 3
    RESET = 4
    RSSC = 5

# Utility functions for using OWI bridge interface (see firmware/OWI_bridge)

def cmd_read(port: serial.Serial, cmd: int, length: int) -> bytes:
    port.write(bytes([Tag.READ.value, length, cmd]))
    return port.read(length)

def cmd_write(port: serial.Serial, cmd: int, data: bytes) -> None:
    port.write(bytes([Tag.WRITE.value, len(data), cmd]) + data)

def cmd_scan(port: serial.Serial, alarm: bool = False) -> bytes | None:
    if alarm:
        port.write(bytes([Tag.ALARM.value, 0, 0]))
    else:
        port.write(bytes([Tag.SCAN.value, 0, 0]))
    if port.read(1)[0] != 0:
        return port.read(8)
    else:
        return None
    
def cmd_reset(port: serial.Serial) -> bool:
    port.write(bytes([Tag.RESET.value, 0, 0]))
    return port.read(1)[0] != 0

def cmd_reset_scan(port: serial.Serial) -> None:
    port.write(bytes([Tag.RSSC.value, 0, 0]))

def owi_crc(data: bytes) -> int:
    # Adapted from the PJRC OneWire library
    crc = 0
    for b in data:
        for _ in range(8):
            mix = (crc ^ b) & 1
            crc >>= 1
            if mix:
                crc ^= 0x8C
            b >>= 1
    return crc