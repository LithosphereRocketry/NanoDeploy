#ifndef HWCONFIG_H
#define HWCONFIG_H


/*
Inline routines for setting up basic hardware functions.
*/

#include <msp430.h>

inline void config_clock() {
    DCOCTL = 0; // Clear control register to select lowest possible clock
    BCSCTL1 = CALBC1_16MHZ; // Load factory offsets for 16MHz clock
    // Leaving BCSCTL2 = default (0) gives us DCO clock with no divider
    // BCSCTL3 = default is fine since it mostly cares about external oscillators
    DCOCTL = CALDCO_16MHZ; // Switch DCO to 16MHz
}

#endif
