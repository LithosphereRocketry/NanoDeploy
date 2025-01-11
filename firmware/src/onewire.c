#include "onewire.h"

#include <msp430.h>

#include "pins.h"

static enum owi_state {
    STATE_OWI_OFF,
    STATE_OWI_IDLE,
    STATE_OWI_PRE_RESET,
    STATE_OWI_RESET,
    STATE_OWI_READY,
    STATE_OWI_CMD
} owi_state = STATE_OWI_OFF;

static volatile uint8_t* volatile owi_buf;
static volatile uint8_t owi_len;

static volatile uint8_t owi_bitcount;

volatile uint8_t owi_cmd;

#define OWI_TA0_MODE (TASSEL_2 | ID_0)

void config_onewire() {
    flight_state = STATE_PROG;
    owi_state = STATE_OWI_IDLE;

    TA0CTL = OWI_TA0_MODE | MC_0; // Make timer stopped
    TA0CCTL1 = CCIE;
}

static inline void start_oneshot(uint16_t cycles) {
    TA0CCR1 = cycles;
    TAR = 0;
    TA0CTL = OWI_TA0_MODE | MC_2;
}

// void owi_receive(volatile uint8_t *buf, size_t len, uint8_t lpm_flags) {
//     owi_buf = (volatile uint8_t* volatile) buf;
//     owi_len = len;
//     owi_bitcount = 8;
// }

__attribute__((interrupt(TIMER0_A1_VECTOR))) 
static void isr_taiv() {
    TA0IV = 0; // manually clear TAIV flag
    TA0CTL = OWI_TA0_MODE | MC_0; // Stop timer

    switch(owi_state) {
        case STATE_OWI_PRE_RESET:
            // reset pulse is long enough
            owi_state = STATE_OWI_RESET;
            break;
        case STATE_OWI_RESET:
            // end presence pulse
            P1DIR &= ~P_OWI;
            // Prepare to read command
            owi_bitcount = 8;
            owi_state = STATE_OWI_CMD;
            break;
        case STATE_OWI_CMD:
            // Sample incoming data
            owi_cmd >>= 1;
            owi_cmd |= ((P1IN & P_OWI) ? (1 << 7) : 0);
            owi_bitcount --;
            if(owi_bitcount == 0) {
                NOP;
            }
            break;
        default:
            break;
    }
}

__attribute__((interrupt(PORT1_VECTOR)))
static void isr_port1() {
    switch(owi_state) {
        case STATE_OWI_OFF:
            config_onewire();
            // intentional fallthrough
        case STATE_OWI_IDLE:
            // Trigger CCR1 at 410 us (close enough to 480)
            start_oneshot(410*16);
            
            P1IES &= ~P_OWI; // trigger on positive edge
            owi_state = STATE_OWI_PRE_RESET;
            break;
        case STATE_OWI_PRE_RESET:
            // Reset pulse was too short, take it from the top
            owi_state = STATE_OWI_IDLE;
            P1IES |= P_OWI; // back to negative edge
            break;
        case STATE_OWI_RESET:
            // Successfully reset
            P1DIR |= P_OWI; // produce presence pulse
            P1IES |= P_OWI; // back to negative edge

            // Start timer for 70us presence pulse (min 60us)
            start_oneshot(70*16);
            break;
        // States that sample the input all do the same thing
        case STATE_OWI_CMD:
            // Sample at 15 us
            start_oneshot(15*16);
            break;
        default:
            break;
    }
    P1IFG &= ~P_OWI;
}
