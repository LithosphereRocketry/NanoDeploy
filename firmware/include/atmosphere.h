#ifndef ATMOSPHERE_H
#define ATMOSPHERE_H

#include <stdint.h>

// Calculates altitude in meters from pressure in Pa, valid within reference
// level 0 or 11,000 m. Result is in integer meters - the sensor only has a
// relative accuracy of 1m and maximum altitude of ~10km, so this shouldn't
// overflow for any reasonable flight conditions.
uint16_t atm_pressure_alt(uint32_t pressure, uint32_t base_pressure);

#endif