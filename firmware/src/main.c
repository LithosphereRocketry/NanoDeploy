#include <stdint.h>
#include <msp430.h>
#include <iomacros.h>

#include "common.h"
#include "hwconfig.h"
#include "pins.h"
#include "flashcfg.h"
#include "tick.h"

int main(void) {
    config_clock();
    config_io();

    fcfg_read(buffers.flashbuf);

    uint8_t err = 0;
    uint8_t blink = 0;
    uint32_t i;
    for(i = 0; i < 64; i++) {
        if(buffers.flashbuf[i] != (uint8_t) (i ^ ~i<<2)) {
            err = 1;
            break;
        } // primitive hash function thing
    }
    
    if(err) {
        int32_t i;
        for(i = 0; i < 64; i++) {
            buffers.flashbuf[i] = i ^ ~i<<2;
        }
        fcfg_write(buffers.flashbuf);
        blink = P_LED;
    }

    config_tick();
    __eint();

    P1OUT = P_LED;
    while(1) {
        __bis_SR_register(LPM0_bits); // Enter LPM0 sleep
        // When we are woken:
        if(wakeup & WAKE_TICK) { // Main run loop
            switch(tone_pitch) {
                // case 0xFF: tone_pitch = 0; break;
                // case 0: tone_pitch = 1; break;
                // default: tone_pitch = 0xFF; break;
            }
            wakeup &= ~WAKE_TICK;
        }
    }
}
