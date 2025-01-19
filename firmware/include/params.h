#ifndef PARAMS_H
#define PARAMS_H

#include "stdint.h"

// 64 bytes, grouped in 8 x 8-byte lines
struct parameters {
    uint8_t owi_id[8];
    
    uint16_t tick_div;
    uint8_t fd_ready;
    uint8_t fd_boost;
    uint8_t fd_coast;
    uint8_t fd_descent;
    uint8_t fd_main;
    uint8_t baro_mode;

    uint8_t t_boost;
    uint8_t t_coast;
    uint8_t t_descent;
    uint8_t t_main;
    uint8_t t_land;
    uint8_t res_3[3];

    uint16_t rate_liftoff;
    uint16_t rate_land;
    uint8_t res_4[4];

    uint8_t res_5[8];

    uint32_t base_pres;
    uint16_t alt_main;
    uint8_t dur_drogue;
    uint8_t dur_main;

    char name[15];
    uint8_t crc;
} __attribute__((packed));

extern const struct parameters* const param;

#endif