#ifndef COMMANDS_H
#define COMMANDS_H

enum device_command {
    DEV_CMD_READ = 0xB0,
    DEV_CMD_MEASURE = 0x7A
};

// Call when a new command comes in
void owi_command();

// Call when a transfer completes
void owi_transfer();

#endif