#include "tick.h"

#include <msp430.h>
#include <pins.h>

#include "common.h"
#include "onewire.h"

void config_tick() {
    TA0CCR0 = 2000; // 16MHz/2000 = 8KHz
    TA0CCTL0 = CCIE; // CC0 interrupt is a little easier than TA interrupt
                     // since it self-resets and isn't shared
    // SMCLK, no divider, up mode
    TA0CTL = TASSEL_2 | ID_0 | MC_1;
}

volatile uint8_t tone_pitch = 0xFF;
volatile uint16_t perfcount = 0;
volatile uint16_t elapsed = 0;

__attribute__((interrupt(TIMER0_A0_VECTOR))) 
static void isr_ta0(void) {
    static uint16_t tick_counter = 0;
    perfcount ++;

    if(tick_counter == 0) {
        elapsed ++;
        wakeup |= WAKE_TICK;
        __bic_SR_register_on_exit(SLEEP_BITS);
        tick_counter = 199; // 40 Hz
    } else {
        tick_counter--;
    }

    static uint8_t tone_counter = 0;
    uint8_t p = tone_pitch; // avoid multiple volatile accesses
    if(p != 0xFF) { // 0xFF = buzzer off
        if(tone_counter == 0) {
            P2OUT ^= P_BUZZER;
            tone_counter = (p >> 1) + ((P2OUT & P_BUZZER) ? (p & 1) : 0);
        } else {
            tone_counter--;
        }
    }
}
