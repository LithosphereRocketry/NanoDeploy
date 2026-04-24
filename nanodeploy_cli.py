#!/usr/bin/python3
import typing
import serial
import serial.serialutil
import argparse
import tqdm

import nano_owi_bridge as owi
from nanodeploy import *

def getval(msg: str, func: typing.Callable, default: typing.Any = None, onfail: None | str = None) -> typing.Any:
    if onfail is None:
        onfail = f"Input must be of type {func.__name__}"
    if default is not None:
        msg += f" ({default})"
    while True:
        try:
            instr = input(msg)
            if instr == "" and default is not None:
                return default
            return func(instr)
        except ValueError:
            print(onfail)

def cmd_help(*_: list[str]):
    print("NanoDeploy CLI interface commands:")
    for name, (help, _) in commands.items():
        print(f"{name}\t{help}")

def cmd_quit(*_: list[str]):
    exit(0)

def cmd_list(*_: list[str]):
    ensure_cfg()
    print(config)

def cmd_port(*args: str):
    global port
    if len(args) < 1:
        print("Not enough arguments to port command")
        return
    try:
        port = serial.Serial(args[0], 115200)
        print(f"Using port {args[0]}")
    except serial.SerialException:
        print(f"Couldn't open port {args[0]}")
            
def write_default(dev_id: DeviceID, name: str):
    default_config = Config(dev_id, name)
    write_config(port, bytes(default_config))

def prompt_id(prev: typing.Optional[DeviceID] = None) -> DeviceID:
    if prev is not None:
        hwver = getval("Hardware revision?", int, prev.hwver)
        fwver = getval("Firmware revision?", int, prev.hwver)
        id = getval("ID number?", int, prev.id)
    else:
        hwver = getval("Hardware revision?", int)
        fwver = getval("Firmware revision?", int)
        id = getval("ID number?", int)
    return DeviceID(hwver, fwver, id)

def cmd_dump(*args: str):
    if len(args) < 1:
        print("Not enough arguments to dump command")
        return
    cmd_read()
    if port is None:
        return
    print("Downloading flight data...")
    with open(args[0], "w") as f:
        f.write(read_data(port, tqdm.tqdm))
    print(f"Wrote data to {args[0]}")

def cmd_read(*_: list[str]):
    global config
    if port is None:
        print("Please select a port first")
        return
    owi.cmd_reset_scan(port)
    owi_id = owi.cmd_scan(port)
    if owi_id is None:
        print("No device found")
        return
    dev_id = DeviceID.from_bytes(owi_id)
    if dev_id is None:
        print(f"Device {owi_id} is corrupted or not a NanoDeploy")
        print("Attempt to reflash with default config?")
        inp = input("(Y/n)").lower()
        if inp not in ["", "y", "yes"]:
            return
        hwver = getval("Hardware revision?", int)
        fwver = getval("Firmware revision?", int)
        id = getval("ID number?", int)
        name = getval("Name?", str)
        write_default(DeviceID(hwver, fwver, id), name)
    new_config = Config.from_bytes(read_config(port))
    if new_config is None:
        if dev_id is not None:
            print(f"Device {owi_id} is a NanoDeploy but its configuration is invalid")
            print("Attempt to reflash with default config?")
            inp = input("(Y/n)").lower()
            if inp not in ["", "y", "yes"]:
                return
            name = getval("Name?", str)
            write_default(dev_id, name)
            new_config = Config.from_bytes(read_config(port))
    if new_config is None:
        print("Failed to write default config!")
        return
    config = new_config
    print("Read configuration data from device")

def cmd_write(*_: list[str]):
    if port is None:
        print("Please select a serial port")
        return
    if config is None:
        print("Please load a configuration first")
        return
    owi.cmd_reset_scan(port)
    owi_id = owi.cmd_scan(port)
    if owi_id is None:
        print("No device found")
        return
    write_config(port, bytes(config))
    print("Saved configuration to device")

def ensure_cfg() -> bool:
    global config
    if config is None and port is not None:
        print("No config loaded, pulling from device")
        cmd_read()
    if config is None:
        print("No config loaded, creating a default config")
        name = getval("Name?", str)
        config = Config(prompt_id(None), name)
        return True
    return False

def cmd_set_id(*_: list[str]):
    if not ensure_cfg():
        config.id = prompt_id(config.id)

def cmd_set_name(*_: list[str]):
    if not ensure_cfg():
        name = getval("Name?", str, config.name)
        config.name = name

def cmd_load(*args: list[str]):
    global port
    ensure_cfg()
    config.load_config(args[0])

def cmd_save(*args: list[str]):
    global port
    if len(args) < 1:
        print("Not enough arguments to save command")
        return
    if config is None:
        print("No config loaded")
    else:
        config.save_config(args[0])

def cmd_default(*_: list[str]):
    global config
    ensure_cfg()
    config = Config(config.id, config.name)
    print("Loaded default parameters")

commands: dict[str, tuple[str, typing.Callable[..., None]]] = {
    "help": ("Prints this help file", cmd_help),
    "quit": ("Exits CLI", cmd_quit),
    "list": ("Prints the currently loaded configuration", cmd_list),
    "port": ("Selects a serial port to search on", cmd_port),
    "dump": ("Downloads flight data to a CSV file", cmd_dump),
    "read": ("Reads configuration data from the device", cmd_read),
    "write": ("Writes configuration data to the device", cmd_write),
    "default": ("Resets the current config to default values", cmd_default),
    "setid": ("Sets a new OneWire id for the device", cmd_set_id),
    "setname": ("Sets a new name for the device", cmd_set_name),
    "load": ("Loads flight parameters from file", cmd_load),
    "save": ("Saves flight parameters to file", cmd_save)
}

port: typing.Optional[serial.Serial] = None
config: typing.Optional[Config] = None

def handle_cmd(inp: str):
    cmd, *args = inp.split()
    if cmd in commands:
        _, func = commands[cmd]
        try:
            func(*args)
        except KeyboardInterrupt:
            print()

def main():
    parser = argparse.ArgumentParser(
        description="Configuration tool for NanoDeploy altimeter."
    )
    parser.add_argument("port", nargs='?', default=None, help="Serial port to search for device on")
    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("-r", "--run-command", nargs="+", default=None, help="Run one or more commands rather than running interactively")
    run_group.add_argument("-R", "--run-file", default=None, help="Run one or more commands from a file rather than running interactively")
    args = parser.parse_args()
    if args.port is not None:
        cmd_port(args.port)
    if args.run_command is not None:
        for cmd in args.run_command:
            handle_cmd(cmd)
    elif args.run_file is not None:
        with open(args.run_file) as f:
            for line in f:
                handle_cmd(line)
    else:
        while True:
            try:
                handle_cmd(input("> "))
            except KeyboardInterrupt:
                print()
                cmd_quit()

if __name__ == "__main__":
    main()