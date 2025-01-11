#ifndef COMMON_H
#define COMMON_H

#define NOP __asm__ __volatile__("nop");

#include <stddef.h>
#include <stdint.h>

extern volatile enum wake_reason {
    WAKE_TICK = 1<<0,
    WAKE_OWI = 1<<1
} wakeup;

extern enum state {
    STATE_READY = 0,
    STATE_PROG
} flight_state;

extern uint8_t databuf[64];
static const size_t dbuf_sz = sizeof(databuf);

#endif