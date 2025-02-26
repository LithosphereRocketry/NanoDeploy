#ifndef COMMANDS_H
#define COMMANDS_H

enum device_command {
    DEV_CMD_READ = 0xB0,
    DEV_CMD_WRITE = 0xBF,
    DEV_CMD_LOAD_CFG = 0x70,
    DEV_CMD_MEASURE = 0x7A,
    DEV_CMD_LOAD_DATA = 0x7F,
    DEV_CMD_SAVE_CFG = 0x80,
};

// Call when a new command comes in
void owi_command();

// Call when a transfer completes
void owi_transfer();

#endif