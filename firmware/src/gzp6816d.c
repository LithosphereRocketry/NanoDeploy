#include "gzp6816d.h"

#include <msp430.h>

#include <math.h>

#include "common.h"
#include "i2c_helpers.h"
#include "generated/gzp_div_conv.h"

#define GZP6816_ADDR 0x78

// From sensor datasheet:
// Sensor range in Pa
#define GZP6816_PMIN  30000
#define GZP6816_PMAX 110000
// Sensor ADC range
#define GZP6816_DMIN  1677722
#define GZP6816_DMAX 15099494

#define SR_BUSY_FLAG BIT5

static const uint16_t read_seq[] = {
    GZP6816_ADDR << 1 | READ_BIT,
    I2C_READ_N
};
// 6 read bytes, minus size of READ_N instruction
static const uint16_t read_len = sizeof(read_seq)/sizeof(uint16_t) + 6 - 1;


void gzp_request_read_comb(uint8_t combined_osr) {
    uint16_t cmd_seq[] = {
        GZP6816_ADDR << 1 | WRITE_BIT,
        0xB0 | combined_osr
    };
    static const uint16_t cmd_len = sizeof(cmd_seq)/sizeof(uint16_t);

    i2c_send_sync(cmd_seq, cmd_len, 0, SLEEP_BITS);

}

void gzp_request_read(gzp_osr_pres_t pres_osr, gzp_osr_temp_t temp_osr) {
    gzp_request_read_comb(temp_osr | pres_osr);
}

void gzp_get_raw_data(uint32_t* pressure, uint16_t* temperature) {
    uint8_t readbuf[6];
    do {
        // if we plan well, this should be ready and waiting for us; otherwise
        // keep re-requesting until it is
        i2c_send_sync(read_seq, read_len, readbuf, SLEEP_BITS);
    } while(readbuf[0] & SR_BUSY_FLAG);
    *pressure = ((uint32_t) readbuf[1]) << 16
              | ((uint32_t) readbuf[2]) << 8
              | ((uint32_t) readbuf[3]);
    *temperature = ((uint16_t) readbuf[4]) << 8
                 | ((uint16_t) readbuf[5]);
}

uint32_t gzp_pressure_pa(uint32_t pres_raw) {
    return div_conv(pres_raw - GZP6816_DMIN) + GZP6816_PMIN;
}
