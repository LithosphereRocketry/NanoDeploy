#include "hwconfig.h"

#include <msp430.h>

#include "pins.h"

// Preserves config of WDT
// TODO: is it better to just predefine what the WDT config is?
void feed_watchdog() { WDTCTL = WDTPW | (WDTCTL & 0xFF) | WDTCNTCL; }

void config_clock() {
    WDTCTL = WDTPW | WDTHOLD; // Stop watchdog
    DCOCTL = 0; // Clear control register to select lowest possible clock
    BCSCTL1 = CALBC1_16MHZ; // Load factory offsets for 16MHz clock
    // Leaving BCSCTL2 = default (0) gives us DCO clock with no divider
    // BCSCTL3 = default is fine since it mostly cares about external oscillators
    DCOCTL = CALDCO_16MHZ; // Switch DCO to 16MHz
}

void config_io() {
    P1DIR = P_LED; // Enable output on LED pin

    P2DIR = P_BUZZER; // Enable output on buzzer
    P2SEL = 0; // Disable crystal driver on port2
}