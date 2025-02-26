#ifndef COMMON_H
#define COMMON_H

#define NOP __asm__ __volatile__("nop");

#define SLEEP_BITS LPM0_bits

#include <stddef.h>
#include <stdint.h>

extern volatile enum wake_reason {
    WAKE_TICK = 1<<0,
    WAKE_OWI_CMD = 1<<1,
    WAKE_OWI_XFER = 1<<2
} wakeup;

extern enum state {
    STATE_CALIB,
    STATE_READY,
    STATE_PROG,
    STATE_BOOST,
    STATE_COAST,
    STATE_DESCENT,
    STATE_MAIN,
    STATE_LANDED
} flight_state;

extern uint8_t databuf[64];
static const size_t dbuf_sz = sizeof(databuf);

#endif