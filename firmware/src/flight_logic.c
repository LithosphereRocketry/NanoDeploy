#include "flight_logic.h"

#include <string.h>

#include "common.h"
#include "gzp6816d.h"
#include "atmosphere.h"

#include "generated/kalman_step.h"

#define NUM_CALIB_CYCLES 40

static uint16_t ground_alt;
int16_t kalman_state[] = {0, 0, 0};

void flight_step() {
    uint32_t pres_raw, pressure;
    uint16_t temp_raw, alt_meas;
    int16_t kalman_tmp[3];
    gzp_get_raw_data(&pres_raw, &temp_raw);
    gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);

    pressure = gzp_pressure_pa(pres_raw);
    alt_meas = atm_pressure_alt(pressure, /*param->base_pres*/101325UL);
    if(flight_state == STATE_CALIB) {
        static uint32_t base_altitude_acc = 0;
        static size_t calib_cycles = NUM_CALIB_CYCLES;

        base_altitude_acc += alt_meas;
        calib_cycles --;
        if(calib_cycles == 0) {
            ground_alt = base_altitude_acc / NUM_CALIB_CYCLES;
            flight_state = STATE_READY;
        }
    } else {
        update_kalman(kalman_tmp, kalman_state, alt_meas - ground_alt);
        memcpy(kalman_state, kalman_tmp, sizeof(kalman_state));
        
        switch(flight_state) {
            case STATE_READY:
                break;
            default: break; // should be unreachable
        }
    }
}