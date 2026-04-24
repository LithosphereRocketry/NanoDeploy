import time
import typing
import configparser
from nano_owi_bridge import *

mem_size = 16*1024
mem_per_packet = 8

# Returns (pressure (Pa), altitude (m), temperature (unconverted))
def poll_sensors(port: serial.Serial) -> tuple[int, int, int]:
    cmd_write(port, 0x7A, b'') # Request barometer conversion
    time.sleep(0.25)
    buf = cmd_read(port, 0xB0, 64)
    print(buf)
    return (int.from_bytes(buf[0:4], 'little'),
            int.from_bytes(buf[4:6], 'little'),
            int.from_bytes(buf[6:8], 'little'))

def read_config(port: serial.Serial) -> bytes:
    cmd_write(port, 0x70, b'')
    time.sleep(0.001)
    return cmd_read(port, 0xB0, 64)

def write_config(port: serial.Serial, buffer: bytes):
    cmd_write(port, 0xBF, buffer)
    cmd_write(port, 0x80, b'')

state_names = {
    1: "ready",
    3: "boost",
    4: "coast",
    5: "descent",
    6: "main"
}

csv_header = "time,baro_altitude,state,batt_voltage,cont_drogue,current_drogue,cont_main,current_main,raw\n"

def packet_to_csv(data: bytes):
    if data[4] not in state_names:
        state='unknown'
    else:
        state = state_names[data[4]]
    time = int.from_bytes(data[0:2], 'little') / 40
    altitude = int.from_bytes(data[2:4], 'little', signed=True)
    battery = data[5] * 3.3 * 2 / 255
    cont_drogue = 1 if data[6] == 0xFF else 0
    curr_drogue = data[6] * 3.3 / 1023 / 0.05 if cont_drogue == 1 else 0
    cont_main = 1 if data[7] == 0xFF else 0
    curr_main = data[7] * 3.3 / 1023 / 0.05 if cont_main == 1 else 0
    return f"{time},{altitude},{state},{battery},{cont_drogue},{curr_drogue},{cont_main},{curr_main},{data.hex()}\n"

T = typing.TypeVar("T")
def read_data(port: serial.Serial, printer: typing.Callable[[T], T]=lambda x: x) -> str:
    csv = csv_header
    for i in printer(range(mem_size//64)):
        cmd_write(port, 0x7F, (i*64).to_bytes(2, 'little'))
        time.sleep(0.01)
        buf = cmd_read(port, 0xB0, 64)
        for i in range(64//mem_per_packet):
            pkt = buf[i*mem_per_packet:(i+1)*mem_per_packet]    
            line = packet_to_csv(pkt)
            if line is None:
                return csv
            else:
                csv += line
    return csv

class DeviceID:
    DEVICE_CLASS = 0x49

    def __init__(self, hwver=0xFF, fwver=0xFFFF, id=0):
        self.hwver = hwver
        self.fwver = fwver
        self.id = id

    @classmethod
    def from_bytes(cls, data: bytes) -> typing.Any | None:
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
        return f"<hw:{self.hwver} fw:{self.fwver} id:{self.id}>"

class Config:
    cfg_structure: dict[str, dict[str, tuple[typing.Callable[[str], typing.Any], str, str]]] = {
        "Device": {
            "base_pressure": (int, "base_pres", "Base pressure (Pa)")
        },
        "Liftoff": {
            "sample_rate": (float, "sample_rate_boost", "Boost sample rate (Hz)"),
            "detect_time": (float, "t_liftoff", "Liftoff detection time (s)"),
            "threshold": (float, "r_liftoff", "Liftoff threshold speed (m/s)")
        },
        "Burnout": {
            "sample_rate": (float, "sample_rate_coast", "Coast sample rate (Hz)"),
            "detect_time": (float, "t_burnout", "Coast detection time (s)")
        },
        "Drogue": {
            "sample_rate": (float, "sample_rate_drogue", "Drogue descent sample rate (Hz)"),
            "detect_time": (float, "t_apogee", "Drogue detection time (s)")
        },
        "Main": {
            "sample_rate": (float, "sample_rate_main", "Main descent sample rate (Hz)"),
            "detect_time": (float, "t_apogee", "Main detection time (s)")
        },
        "Landing": {
            "detect_time": (float, "t_land", "Landing detection time (s)"),
            "threshold": (float, "r_land", "Landing threshold speed (m/s)")
        }
    }

    def __init__(self, id: DeviceID, name: str):
        self.id: DeviceID = id
        self.name: str = name[:15]
        self.base_pres: int = 101325
        self.sample_rate_boost: float = 10
        self.sample_rate_coast: float = 10
        self.sample_rate_drogue: float = 1
        self.sample_rate_main: float = 1

        self.t_liftoff: float = 0.5
        self.t_burnout: float = 0.5
        self.t_apogee: float = 1
        self.t_main: float = 1
        self.t_land: float = 5
        self.r_liftoff: float = 10
        self.r_land: float = 1
    
    @classmethod
    def from_bytes(cls, data: bytes) -> typing.Self | None:
        if len(data) != 64 or owi_crc(data) != 0:
            return None
        id = DeviceID.from_bytes(data[0x00:0x08])
        if id is None:
            return None
        res = cls(id, data[0x30:0x3F].decode("ascii"))
        res.base_pres = int.from_bytes(data[0x1C:0x20], 'little')

        def scale_rate(n: int):
            if n == 0:
                return float("inf")
            return 40/data[n]

        res.sample_rate_boost = scale_rate(0x08)
        res.sample_rate_coast = scale_rate(0x09)
        res.sample_rate_drogue = scale_rate(0x0A)
        res.sample_rate_main = scale_rate(0x0B)

        res.t_liftoff = data[0x10] / 40
        res.t_burnout = data[0x11] / 40
        res.t_apogee = data[0x12] / 40
        res.t_main = data[0x13] / 40
        res.t_land = data[0x14] / 40

        res.r_liftoff = data[0x16]
        res.r_land = data[0x17]
        return res
    
    def __bytes__(self):
        data = [0]*64
        data[0x00:0x08] = bytes(self.id)
        data[0x08] = int(40 / self.sample_rate_boost)
        data[0x09] = int(40 / self.sample_rate_coast)
        data[0x0A] = int(40 / self.sample_rate_drogue)
        data[0x0B] = int(40 / self.sample_rate_main)

        data[0x10] = int(40*self.t_liftoff)
        data[0x11] = int(40*self.t_burnout)
        data[0x12] = int(40*self.t_apogee)
        data[0x13] = int(40*self.t_main)
        data[0x14] = int(40*self.t_land)

        data[0x16] = int(self.r_liftoff)
        data[0x17] = int(self.r_land)

        data[0x1C:0x20] = self.base_pres.to_bytes(4, 'little')
        name_bytes = self.name.encode("ascii")[:0xF]
        data[0x30:0x3F] = name_bytes + b'\x00'*(15-len(name_bytes))
        data[0x3F] = owi_crc(bytes(data[0x00:0x3F]))
        return bytes(data)
    
    def load_config(self, fpath: str):
        parser = configparser.ConfigParser()
        parser.read(fpath)
        for section_name, section in Config.cfg_structure.items():
            for entry_name, (xform, member, _) in section.items():
                setattr(self, member, xform(parser[section_name][entry_name]))

    def save_config(self, fpath: str):
        parser = configparser.ConfigParser()
        for section_name, section in Config.cfg_structure.items():
            parser.add_section(section_name)
            for entry_name, (_, member, _) in section.items():
                parser.set(section_name, entry_name, str(getattr(self, member)))
        with open(fpath, "w") as f:
            parser.write(f)

    def __str__(self):
        res = f"{self.name}\nOnewire id: {self.id}\n" 
        for grp in Config.cfg_structure.values():
            for _, member, docstr in grp.values():
                res += f"{docstr}: {getattr(self, member)}\n"
        return res
    
