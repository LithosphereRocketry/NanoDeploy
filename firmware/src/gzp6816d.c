#include "gzp6816d.h"

#include <msp430.h>

#include "usi_i2c.h"

#define GZP6816_ADDR 0x78
#define READ_BIT 1
#define WRITE_BIT 0

#define SR_BUSY_FLAG BIT5

static const uint16_t read_seq[] = {
    GZP6816_ADDR << 1 | READ_BIT,
    I2C_READ,
    I2C_READ,
    I2C_READ,
    I2C_READ,
    I2C_READ,
    I2C_READ
};
static const uint16_t read_len = sizeof(read_seq)/sizeof(uint16_t);

// Synchronous i2c transaction send; waits in LPM0 until transaction is complete
// Technically you can probably make things faster by interleaving i2c with
// other things, but it shouldn't really matter here
static void i2c_send_sync(uint16_t const * sequence, uint16_t sequence_length, uint8_t *received_data, uint16_t wakeup_sr_bits) {
    i2c_send_sequence(sequence, sequence_length, received_data, wakeup_sr_bits);
    do {
        // Keep going back to sleep until the wakeup is i2c_send_sequence
        // We'll accumulate a bit of an "inbox" this way but these
        // transfers should be fast enough to be OK
        __bis_SR_register(wakeup_sr_bits);
    } while(!i2c_done());
}

void gzp_request_read(gzp_osr_pres_t pres_osr, gzp_osr_temp_t temp_osr) {
    uint16_t cmd_seq[] = {
        GZP6816_ADDR << 1 | WRITE_BIT,
        0xB0 | temp_osr | pres_osr
    };
    static const uint16_t cmd_len = sizeof(cmd_seq)/sizeof(uint16_t);

    i2c_send_sync(cmd_seq, cmd_len, 0, LPM0_bits);
}

void gzp_get_data(uint32_t* pressure, uint16_t* temperature) {
    uint8_t readbuf[6];
    do {
        // if we plan well, this should be ready and waiting for us; otherwise
        // keep re-requesting until it is
        i2c_send_sync(read_seq, read_len, readbuf, LPM0_bits);
    } while(readbuf[0] & SR_BUSY_FLAG);
    *pressure = ((uint32_t) readbuf[1]) << 16
              | ((uint32_t) readbuf[2]) << 8
              | ((uint32_t) readbuf[3]);
    *temperature = ((uint16_t) readbuf[4]) << 8
                 | ((uint16_t) readbuf[5]);
}