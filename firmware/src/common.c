#include "common.h"

volatile enum wake_reason wakeup;

enum state flight_state = STATE_CALIB;

uint8_t databuf[];
