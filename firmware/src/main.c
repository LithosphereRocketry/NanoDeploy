#include <stdint.h>
#include <string.h>
#include <msp430.h>
#include <iomacros.h>

#include "usi_i2c.h"

#include "common.h"
#include "hwconfig.h"
#include "pins.h"
#include "flashcfg.h"
#include "tick.h"
#include "gzp6816d.h"
#include "eeprom_24c.h"
#include "atmosphere.h"

uint16_t tmp;
volatile uint32_t base_pres;
volatile uint32_t pres;
volatile uint16_t alt;

static uint8_t err;

int main(void) {
    config_clock();
    config_io();

    // fcfg_read(/*buffers.*/flashbuf);

    // Ensure state of flashbuf isn't UB
    memset(/*buffers.*/flashbuf, 0, 64);

    __eint();

    P1OUT = P_LED;

    i2c_init(USIDIV_4, USISSEL_2); // SMCLK/16 = 1MHz Fast+

    eep_read(0x7, 0x1200,  /*buffers.*/flashbuf, 64);
    err = 0;
    uint8_t blink = 0;
    for(unsigned i = 0; i < 64; i++) {
        if(/*buffers.*/flashbuf[i] != (uint8_t) (i ^ ~i<<2)) {
            err = 1;
            break;
        } // primitive hash function thing
    }
    
    if(err) {
        for(unsigned i = 0; i < 64; i++) {
            /*buffers.*/flashbuf[i] = i ^ ~i<<2;
        }
        eep_write_page(0x7, 0x1200, /*buffers.*/flashbuf, 64);
        blink = P_LED;
    }

    P1OUT = P_LED;

    gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);

    __dint();
    config_tick();
    __eint();

    while(1) {
        __bis_SR_register(LPM0_bits); // Enter LPM0 sleep
        // When we are woken:
        if(wakeup & WAKE_TICK) { // Main run loop
            // gzp_get_raw_data(&pres, &tmp);
            // gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);

            // uint32_t pressure = gzp_pressure_pa(pres);
            // volatile uint32_t altitude = atm_pressure_alt(pressure, 101325);
            switch(tone_pitch) {
                // case 0xFF: tone_pitch = 0; break;
                // case 0: tone_pitch = 1; break;
                // default: tone_pitch = 0xFF; break;
            }
            // P1OUT ^= P_PYRO_DROGUE | P_LED;
            // P2OUT ^= P_PYRO_MAIN;
            P1OUT ^= blink;
            wakeup &= ~WAKE_TICK;
        }
    }
}
