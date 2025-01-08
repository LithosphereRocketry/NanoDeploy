#ifndef I2C_HELPERS_H
#define I2C_HELPERS_H

#include "usi_i2c.h"

#define READ_BIT 1
#define WRITE_BIT 0

// Synchronous i2c transaction send; waits in LPM0 until transaction is complete
// Technically you can probably make things faster by interleaving i2c with
// other things, but it shouldn't really matter here
static inline void i2c_send_sync(uint16_t const * sequence, uint16_t sequence_length, uint8_t *received_data, uint16_t wakeup_sr_bits) {
    i2c_send_sequence(sequence, sequence_length, received_data, wakeup_sr_bits);
    do {
        // Keep going back to sleep until the wakeup is i2c_send_sequence
        // We'll accumulate a bit of an "inbox" this way but these
        // transfers should be fast enough to be OK
        __bis_SR_register(wakeup_sr_bits);
    } while(!i2c_done());
}

#endif