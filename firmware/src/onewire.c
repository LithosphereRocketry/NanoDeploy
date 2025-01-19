#include "onewire.h"

#include <msp430.h>

#include "pins.h"

#define CYCLES_US 16 // 16MHz timer clock

#define RESET_TIME (400 * CYCLES_US)
#define PPULSE_DELAY (15 * CYCLES_US)
#define PPULSE_TIME (120 * CYCLES_US)
#define SAMPLE_TIME (15 * CYCLES_US)
#define TRANSMIT_TIME (40 * CYCLES_US)

static enum owi_state {
    // Idle and startup/reset
    STATE_OWI_OFF,
    STATE_OWI_IDLE,
    STATE_OWI_RESET,
    STATE_OWI_PPULSE,
    STATE_OWI_CMD,
    STATE_OWI_SEARCH,
    STATE_OWI_SEARCH_CMPL,
    STATE_OWI_SEARCH_SEL,
    STATE_OWI_SEND,
    STATE_OWI_RECV
} owi_state = STATE_OWI_OFF;

static volatile uint8_t* volatile owi_buf;
static volatile size_t owi_len;
static volatile uint8_t owi_byte;

static volatile uint8_t owi_bitcount;

volatile uint8_t owi_cmd;

#define OWI_TA0_MODE (TASSEL_2 | ID_0 | TAIE)

static inline void start_timer() {
    TA0R = 0;
    TA0CTL = OWI_TA0_MODE | MC_2;
}

static inline void stop_timer() {
    TA0CTL = OWI_TA0_MODE | MC_0;
}

void config_onewire() {
    // Just to be paranoid, make sure we don't get interrupted while configuring
    // the state machine
    __dint();
    flight_state = STATE_PROG;
    owi_state = STATE_OWI_IDLE;

    TA0CTL = OWI_TA0_MODE | MC_0; // Make timer stopped
    // Don't enable CC interrupts yet, we'll enable that per-state-transition as
    // not all need it
    // Set up reset watchdog
    TA0CCR2 = RESET_TIME;
    __eint();
}

void owi_select() {
    owi_state = STATE_OWI_CMD;
    owi_bitcount = 8;
}

void owi_search(const uint8_t *rom) {
    // This part of the state machine should never write to the buffer, so
    // it should be safe to cast away const here
    // Just to be paranoid, make sure we don't get interrupted while configuring
    // the state machine
    __dint();
    owi_buf = (volatile uint8_t*) rom;
    // Preload the first byte to save time in precise interrupts
    owi_bitcount = 8;
    owi_byte = *rom;
    owi_len = 8;
    // Make sure we don't have any issues with preexisting timer interrupts
    TA0CCTL1 = 0;
    owi_state = STATE_OWI_SEARCH;
    __eint();
}

void owi_receive(volatile uint8_t* buf, size_t len) {
    __dint();
    owi_buf = buf;
    owi_bitcount = 8;
    owi_len = len;
    // Make sure we don't have any issues with preexisting timer interrupts
    TA0CCTL1 = 0;
    owi_state = STATE_OWI_RECV;
    __eint();
}

void owi_send(const uint8_t* buf, size_t len) {
    // This part of the state machine should never write to the buffer, so
    // it should be safe to cast away const here
    // Just to be paranoid, make sure we don't get interrupted while configuring
    // the state machine
    __dint();
    owi_buf = (volatile uint8_t*) buf;
    // Preload the first byte to save time in precise interrupts
    owi_bitcount = 8;
    owi_byte = *buf;
    owi_len = len;
    // Make sure we don't have any issues with preexisting timer interrupts
    TA0CCTL1 = 0;
    owi_state = STATE_OWI_SEND;
    __eint();
}

static inline __attribute__((always_inline)) void timer_done() {

    uint8_t val;
    switch(owi_state) {
        case STATE_OWI_RESET:
            // Presence pulse start
            P1DIR |= P_OWI;
            // This should trigger a falling edge on P_OWI, restarting the timer
            // so set up the timer for the end of the presence pulse
            TA0CCTL1 = CCIE;
            TA0CCR1 = PPULSE_TIME;
            owi_state = STATE_OWI_PPULSE;
            break;
        case STATE_OWI_PPULSE:
            // Presence pulse end
            P1DIR &= ~P_OWI;
            TA0CCTL1 = 0;
            owi_state = STATE_OWI_CMD;
            owi_bitcount = 8; // preload bitcount
            break;
        case STATE_OWI_CMD:
            owi_byte >>= 1;
            if(P1IN & P_OWI) owi_byte |= 0x80;
            owi_bitcount --;
            if(owi_bitcount == 0) {
                owi_state = STATE_OWI_IDLE;
                owi_cmd = owi_byte;
                wakeup |= WAKE_OWI_CMD;
                __bic_SR_register_on_exit(SLEEP_BITS);   
            }
            break;
        case STATE_OWI_SEARCH:
            P1DIR &= ~P_OWI;
            owi_state = STATE_OWI_SEARCH_CMPL;
            break;
        case STATE_OWI_SEARCH_CMPL:
            P1DIR &= ~P_OWI;
            owi_state = STATE_OWI_SEARCH_SEL;
            break;
        case STATE_OWI_SEARCH_SEL:
            val = P1IN;
            if(((val & P_OWI) && (owi_byte & 0b1))
            || (!(val & P_OWI) && !(owi_byte & 0b1))) {
                // This is the correct bit, so stay in the search
                owi_bitcount --;
                if(owi_bitcount == 0) {
                    owi_len --;
                    if(owi_len == 0) {
                        // We have no more bytes of address, so we're done
                        // Listen for the next command
                        owi_state = STATE_OWI_CMD;
                    } else {
                        owi_buf ++;
                        owi_byte = *owi_buf;
                        owi_state = STATE_OWI_SEARCH;
                    }
                    // Regardless, we expect 8 bits of transfer
                    owi_bitcount = 8;
                } else {
                    owi_byte >>= 1;
                    owi_state = STATE_OWI_SEARCH;
                }
            } else {
                // Incorrect bit, drop out to idle
                owi_state = STATE_OWI_IDLE;
            }
            break;
        case STATE_OWI_SEND:
            P1DIR &= ~P_OWI;
            owi_bitcount --;
            if(owi_bitcount == 0) {
                owi_len --;
                if(owi_len == 0) {
                    owi_state = STATE_OWI_IDLE;
                    wakeup |= WAKE_OWI_XFER;
                    __bic_SR_register_on_exit(SLEEP_BITS);
                } else {
                    owi_buf ++;
                    owi_byte = *owi_buf;
                    owi_bitcount = 8;
                }
            } else {
                owi_byte >>= 1;
            }
            break;
        case STATE_OWI_RECV:
            owi_byte >>= 1;
            if(P1IN & P_OWI) owi_byte |= 0x80;
            owi_bitcount --;
            if(owi_bitcount == 0) {
                *owi_buf = owi_byte;
                owi_len --;
                if(owi_len == 0) {
                    owi_state = STATE_OWI_IDLE;
                    wakeup |= WAKE_OWI_XFER;
                    __bic_SR_register_on_exit(SLEEP_BITS);
                } else {
                    owi_buf ++;
                    owi_bitcount = 8;
                }
            }
            break;
        default:
            break;
    }
}

static inline __attribute__((always_inline)) void owi_rising() {
    switch(owi_state) {
        case STATE_OWI_RESET:
            // Prepare to send a presence pulse in the future
            // We keep the timer rolling from the descending edge for
            // consistency, so calculate what time we want based on current time
            TA0CCR1 = TA0R + PPULSE_DELAY;
            TA0CCTL1 = CCIE;
            break;
        default:
            break;
    }

    TA0CCTL2 = 0; // Switch off reset timer    
}

static inline __attribute__((always_inline)) void owi_falling() {
    if(flight_state != STATE_PROG) {
        config_onewire();
    }
    switch(owi_state) {
        case STATE_OWI_CMD:
        case STATE_OWI_RECV:
        case STATE_OWI_SEARCH_SEL:
            // Set timer for sample time
            TA0CCR1 = SAMPLE_TIME;
            TA0CCTL1 = CCIE;
            break;
        case STATE_OWI_SEND:
        case STATE_OWI_SEARCH:
            // If we have 0 in this bit position, send 0
            if(!(owi_byte & 1)) {
                P1DIR |= P_OWI;
            }
            TA0CCR1 = TRANSMIT_TIME;
            TA0CCTL1 = CCIE;
            break;
        case STATE_OWI_SEARCH_CMPL:
            // If we have 1 in this bit position, send 0
            if(owi_byte & 1) {
                P1DIR |= P_OWI;
            }
            TA0CCR1 = TRANSMIT_TIME;
            TA0CCTL1 = CCIE;
            break;
        default:
            break;
    }
    TA0CCTL2 = CCIE; // Enable reset timer
    start_timer();
}

__attribute__((interrupt(TIMER0_A1_VECTOR))) 
static void isr_taiv() {
    switch(TA0IV) {
        case TA0IV_TACCR1:
            TA0CCR1 = 0; // CCR1 flag received, switch it off
            timer_done();
            break;
        case TA0IV_TACCR2:
            // If we reach CCR2, that means the pulse is long enough to be a
            // reset
            TA0CCTL1 = 0; // turn off any existing oneshot
            owi_state = STATE_OWI_RESET;
            break;
        case TA0IV_TAIFG:
            // Make the timer effectively a one-shot by stopping it if it ever
            // wraps around
            stop_timer();
        default:
            break;
    }
}

__attribute__((interrupt(PORT1_VECTOR)))
static void isr_port1() {
    // Store which edge this was and immediately clear the interrupt to make
    // sure we don't miss anything on very quickly repeating pulses
    uint8_t p1val = P1IES;
    P1IES = P1IN;
    P1IFG &= ~P_OWI;

    // Now that we have time to breathe (and more interrupts can come in) handle
    // the actual work of the interrupt
    if(p1val & P_OWI) {
        owi_falling();
    } else {
        owi_rising();
    }

    return;
}
