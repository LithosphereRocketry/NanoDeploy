#ifndef FLIGHT_LOGIC_H
#define FLIGHT_LOGIC_H

#include <stdint.h>

extern int16_t kalman_state[3];

void flight_step();

#endif