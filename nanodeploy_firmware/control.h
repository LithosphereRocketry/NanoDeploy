#ifndef CONTROL_H
#define CONTROL_H

#include <assert.h>
typedef struct {
    uint32_t time_ms;
} flight_state_t;

static_assert(sizeof(flight_state_t) <= 64);

#endif