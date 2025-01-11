#ifndef ONEWIRE_H
#define ONEWIRE_H

#include "common.h"

/**
 * Puts state machine in onewire mode, disabling flight logic. This will happen
 * automatically if the OWI pin is pulled low, or it can be done via this
 * function to prevent erroneous operation if the startup configuration of the
 * flight computer is wrong.
 */
void config_onewire();

/**
 * Command received by OneWire bus. If processor is woken with reason WAKE_OWI,
 * it should check here to see what command was requested.
 */
extern volatile uint8_t owi_cmd;

/**
 * Receive len bytes from the OWI bus into buf. On completion, clear processor
 * status flags lpm_flags and flag the wakeup reason as WAKE_OWI.
 */
// void owi_receive(volatile uint8_t* buf, size_t len, uint8_t lpm_flags);

/**
 * Send len bytes from buf to the OWI bus. On completion, clear processor status
 * flags lpm_flags and flag the wakeup reason as WAKE_OWI.
 */
// void owi_send(const uint8_t* buf, size_t len, uint8_t lpm_flags);

#endif