#include <stdint.h>
#include <msp430.h>

#include "hwconfig.h"
#include "pins.h"
#include "flashcfg.h"

union {
    uint8_t flashbuf[64];
} buffers;

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

    P1OUT = P_LED;
    while(1) {
        for(i = 1000000; i > 0; i--) {}
        P1OUT ^= blink;
    }
}
