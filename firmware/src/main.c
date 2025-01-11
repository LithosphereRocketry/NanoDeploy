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

    __eint();

    P1OUT = P_LED;

    i2c_init(USIDIV_4, USISSEL_2); // SMCLK/16 = 1MHz Fast+

    gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);

    __dint();
    config_tick();
    __eint();

    while(1) {
        __bis_SR_register(LPM0_bits); // Enter LPM0 sleep
        // When we are woken:
        if(wakeup & WAKE_TICK) { // Main run loop
            gzp_get_raw_data(&pres, &tmp);
            gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);

            perfcount = 0;
            uint32_t pressure = gzp_pressure_pa(pres);
            volatile uint32_t altitude = atm_pressure_alt(pressure, 101325);

            // P1OUT ^= blink;
            wakeup &= ~WAKE_TICK;
        }
    }
}
