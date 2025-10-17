#include "flight_logic.h"

#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include "common.h"
#include "pins.h"
#include "gzp6816d.h"
#include "atmosphere.h"
#include "logging.h"
#include "tick.h"
#include "params.h"

#include "generated/kalman_step.h"

#define NUM_CALIB_CYCLES 40

static uint16_t ground_alt;
int16_t kalman_state[] = {0, 0, 0};

static uint8_t log_counter = 0;
static uint8_t state_counter = 0;

static inline void store_log(uint8_t delay, bool tmp) {
    if(log_counter == 0) {
        current_frame->elapsed = elapsed;
        current_frame->altitude = kalman_state[0];
        current_frame->state = flight_state;
        current_frame->temp = 0xFF;
        current_frame->cont_drogue = 0xFF;
        current_frame->cont_main = 0xFF;
        log_counter = delay;
        if(tmp) log_temp(); else log_store();
    } else {
        log_counter --;
    }
}

void flight_init() {
    gzp_request_read(GZP_OSR_PRES_8X, GZP_OSR_TEMP_4X);
}

void flight_step() {
    uint32_t pres_raw, pressure;
    uint16_t temp_raw, alt_meas;
    int16_t kalman_tmp[3];
    gzp_get_raw_data(&pres_raw, &temp_raw);
    gzp_request_read(GZP_OSR_PRES_8X, GZP_OSR_TEMP_4X);

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
            state_counter = param->t_boost;
            P1OUT |= P_LED;
        }
    } else {
        update_kalman(kalman_tmp, kalman_state, alt_meas - ground_alt);
        memcpy(kalman_state, kalman_tmp, sizeof(kalman_state));
        
        state_counter --;
        switch(flight_state) {
            case STATE_READY:
                store_log(param->fd_boost, true);
                if(kalman_state[1] <= param->rate_liftoff*16) {
                    state_counter = param->t_boost;
                } else if(state_counter == 0) {
                    log_flush_temp(current_frame->elapsed);
                    flight_state = STATE_BOOST;
                    state_counter = param->t_coast;
                }
                break;
            case STATE_BOOST:
                store_log(param->fd_boost, false);
                if(kalman_state[1] <= 0 || kalman_state[2] >= 0) {
                    state_counter = param->t_coast;
                } else if(state_counter == 0) {
                    flight_state = STATE_COAST;
                    state_counter = param->t_descent;
                }
                break;
            case STATE_COAST:
                store_log(param->fd_coast, false);
                if(kalman_state[1] >= 0) {
                    state_counter = param->t_coast;
                } else if(state_counter == 0) {
                    // TODO: Fire drogue
                    flight_state = STATE_DESCENT;
                    state_counter = param->t_main;
                }
                break;
            case STATE_DESCENT:
                store_log(param->fd_descent, false);
                if((uint16_t) kalman_state[0] >= param->alt_main) {
                    state_counter = param->t_descent;
                } else if(state_counter == 0) {
                    // TODO: Fire main
                    flight_state = STATE_MAIN;
                    state_counter = param->t_land;
                }
                break;
            case STATE_MAIN:
                store_log(param->fd_main, false);
                if(abs(kalman_state[1]) >= param->rate_land) {
                    state_counter = param->t_main;
                } else if(state_counter == 0) {
                    flight_state = STATE_LANDED;
                }
                break;
            default: break; // should be unreachable
        }
    }
}