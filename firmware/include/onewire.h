#ifndef ONEWIRE_H
#define ONEWIRE_H

#include "common.h"

enum onewire_command {
    OWI_CMD_READ = 0x33,
    OWI_CMD_SKIP = 0xCC,
    OWI_CMD_MATCH = 0x55,
    OWI_CMD_SEARCH = 0xF0
};

/**
 * Puts state machine in onewire mode, disabling flight logic. This will happen
 * automatically if the OWI pin is pulled low, or it can be done via this
 * function to prevent erroneous operation if the startup configuration of the
 * flight computer is wrong.
 */
void config_onewire();

/**
 * Command received by OneWire bus. If processor is woken with reason
 * WAKE_OWI_CMD, it should check here to see what command was requested.
 */
extern volatile uint8_t owi_cmd;

/**
 * Make the OneWire interface ready to accept another command.
 */
void owi_select();


/**
 * Start a OneWire search with the specified array as the 8-byte ROM value. On
 * success, goes into command-waiting mode; on failure, goes into idle and waits
 * for bus reset
 */
void owi_search(const uint8_t* rom);

/**
 * Receive len bytes from the OWI bus into buf. On completion, wake up the
 * processor and flag the wakeup reason as WAKE_OWI_CMD.
 */
void owi_receive(volatile uint8_t* buf, size_t len);

/**
 * Send len bytes from buf to the OWI bus. On completion, wake up the processor
 * and flag the wakeup reason as WAKE_OWI_CMD.
 */
void owi_send(const uint8_t* buf, size_t len);

#endif