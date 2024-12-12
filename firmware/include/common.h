#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>

extern volatile enum wake_reason {
    WAKE_TICK = 1<<0
} wakeup;

extern union buffer_structure {
    uint8_t flashbuf[64];
} buffers;

#endif