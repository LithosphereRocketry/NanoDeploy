#include "commands.h"

#include "onewire.h"
#include "params.h"
#include "gzp6816d.h"
#include "atmosphere.h"

#include <string.h>

enum {
    XFER_RESELECT,
    XFER_MATCH
} xfer_done_event;

static uint8_t addr_buf[8];

static struct measurement_buffer {
    uint32_t pres;
    uint16_t alt;
    uint16_t temp;
}* const meas_buf = (struct measurement_buffer*) databuf;

void owi_command() {
    switch(owi_cmd) {
        // OWI common interface commands
        case OWI_CMD_SEARCH:     
            owi_search(param->owi_id);
            break;
        case OWI_CMD_SKIP:
            owi_select();
            break;
        case OWI_CMD_READ:
            owi_send(param->owi_id, 8);
            xfer_done_event = XFER_RESELECT;
            break;
        case OWI_CMD_MATCH:
            owi_receive((volatile uint8_t*) addr_buf, 8);
            xfer_done_event = XFER_MATCH;
            break;
        // Device-specific commands
        case DEV_CMD_READ:
            owi_send(databuf, 64);
            xfer_done_event = XFER_RESELECT;
        case DEV_CMD_MEASURE:
            gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);
            for(int i = 0; i < 10000; i++) NOP;
            gzp_get_raw_data(&meas_buf->pres, &meas_buf->temp);
            meas_buf->pres = gzp_pressure_pa(meas_buf->pres);
            meas_buf->alt = atm_pressure_alt(meas_buf->pres, 101325);
            owi_select();
            break;
        default:
            break;
    }
}

void owi_transfer() {
    switch(xfer_done_event) {
        case XFER_RESELECT:
            owi_select();
            break;
        case XFER_MATCH:
            if(memcmp(addr_buf, param->owi_id, 8) == 0) {
                owi_select();
            }
            break;
        default:
            break;
    }
}