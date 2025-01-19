#ifndef GZP6816D_H
#define GZP6816D_H

#include <stdint.h>

typedef enum {
    GZP_OSR_TEMP_4X = 0<<3,
    GZP_OSR_TEMP_8X = 1<<3
} gzp_osr_temp_t;

typedef enum {
    GZP_OSR_PRES_128X = 0b000,
    GZP_OSR_PRES_64X = 0b001,
    GZP_OSR_PRES_32X = 0b010,
    GZP_OSR_PRES_16X = 0b011,
    GZP_OSR_PRES_8X = 0b100,
    GZP_OSR_PRES_4X = 0b101,
    GZP_OSR_PRES_2X = 0b110,
    GZP_OSR_PRES_1X = 0b111
} gzp_osr_pres_t;

// Initiates a read request. Stalls for duration of I2C transaction (~200us at
// standard speed)
void gzp_request_read(gzp_osr_pres_t pres_osr, gzp_osr_temp_t temp_osr);
// Equivalent, but the two values above are already bitwise-or'ed
void gzp_request_read_comb(uint8_t combined_osr);

// Initiates a read request. Stalls until data is ready (minimum ~700us at
// standard speed, maximum time dependant on oversample rate)
void gzp_get_raw_data(uint32_t* pressure, uint16_t* temperature);

// Converts a GZP6816 raw reading to integer pascals. Slight loss of precision
// but none that matters given the rated accuracy of the sensor.
uint32_t gzp_pressure_pa(uint32_t pres_raw);

#endif