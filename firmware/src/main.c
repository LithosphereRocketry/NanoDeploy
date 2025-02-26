#include <stdint.h>
#include <string.h>
#include <msp430.h>
#include <iomacros.h>

#include "usi_i2c.h"
#include "common.h"
#include "hwconfig.h"
#include "tick.h"
#include "commands.h"
#include "flight_logic.h"
#include "gzp6816d.h"

int main(void) {
    config_clock();
    config_io();

    __eint();

    i2c_init(USIDIV_4, USISSEL_2); // SMCLK/16 = 1MHz Fast+

    gzp_request_read(GZP_OSR_PRES_8X, GZP_OSR_TEMP_4X);

    __dint();
    config_tick();
    __eint();

    while(1) {
        __bis_SR_register(SLEEP_BITS); // Enter LPM0 sleep
        // When we are woken:
        do {
            if(wakeup & WAKE_OWI_CMD) {
                owi_command();
                wakeup &= ~WAKE_OWI_CMD;
            } else if(wakeup & WAKE_OWI_XFER) {
                owi_transfer();
                wakeup &= ~WAKE_OWI_XFER;
            } else if(wakeup & WAKE_TICK) { // Main run loop
                flight_step();
                wakeup &= ~WAKE_TICK;
            }
        } while(wakeup);
    }
}
