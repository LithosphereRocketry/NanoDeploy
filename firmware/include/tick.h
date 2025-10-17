#ifndef TICK_H
#define TICK_H

#include <stdint.h>

void config_tick();

extern volatile uint8_t tone_pitch;
extern volatile uint16_t perfcount;
extern volatile uint16_t elapsed;

#endif