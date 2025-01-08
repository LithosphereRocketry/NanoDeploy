#include "atmosphere.h"

#include "generated/atm_div_k.h"
#include "generated/atm_div_tl.h"

// Number of Taylor terms for each approximation step
// These values are the smallest to give +-3m precision with floating-point
// Taylor approximation; it's not possible to do much better than this without
// increasing the precision of the fixed-point approximation step to 32-bit
// and 3 meters should be plenty for rocketry purposes
static const uint16_t n_log = 14;
static const uint16_t n_exp = 4;

static inline uint16_t mul_uxp16(uint16_t a, uint16_t b) {
    // This should optimize to an upper-word multiply
    // (still soft multiply on MSP430 but whatev)
    return (((uint32_t) a) * ((uint32_t) b)) >> 16;
}

static inline uint16_t as_uxp16_ratio(uint16_t n, uint16_t d) {
    return (uint16_t) ((((uint32_t) n) << 16) / d);
}

// See misc/baro_approx.py for derivation

uint16_t atm_pressure_alt(uint32_t pressure, uint32_t base_pressure) {
    if(pressure >= base_pressure) return 0; // we don't handle negative altitude
    uint32_t l = 0;
    // Our barometer is only accurate to 12 Pa, so losing one bit of precision
    // to fit in a uint16_t is no big deal
    uint16_t one_minus_ppb = -as_uxp16_ratio(pressure >> 1, base_pressure >> 1);
    uint16_t exp_val_l = one_minus_ppb;
    for(uint16_t i = 0; i < n_log; i++) {
        l += exp_val_l / (i+1);
        exp_val_l = mul_uxp16(exp_val_l, one_minus_ppb);
    }

    uint16_t q = 0;
    // Note that this division is 32-bit because l is, but can be truncated to
    // 16 bits afterward
    uint16_t l_over_k = (uint16_t) div_k(l);
    uint16_t exp_val_e = l_over_k;
    uint16_t fact_val = 1;
    for(uint16_t i = 1; i < n_exp; i++) {
        fact_val *= i;
        uint16_t term = exp_val_e / fact_val;
        exp_val_e = mul_uxp16(exp_val_e, l_over_k);
        if((i & 1) == 0) {
            q += term;
        } else {
            q -= term;
        }
    }

    return div_tl(-q);
}