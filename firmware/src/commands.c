#include "commands.h"

#include "onewire.h"
#include "params.h"
#include "gzp6816d.h"
#include "atmosphere.h"
#include "flashcfg.h"
#include "eeprom_24c.h"

#include <string.h>

enum {
    XFER_RESELECT,
    XFER_MATCH,
    XFER_EEPROM_DUMP
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
            break;
        case DEV_CMD_WRITE:
            owi_receive(databuf, 64);
            xfer_done_event = XFER_RESELECT;
            break;
        case DEV_CMD_LOAD_CFG:
            fcfg_read(databuf);
            owi_select();
            break;
        case DEV_CMD_MEASURE:
            gzp_request_read(GZP_OSR_PRES_128X, GZP_OSR_TEMP_8X);
            gzp_get_raw_data(&meas_buf->pres, &meas_buf->temp);
            meas_buf->pres = gzp_pressure_pa(meas_buf->pres);
            meas_buf->alt = atm_pressure_alt(meas_buf->pres, 101325);
            owi_select();
            break;
        case DEV_CMD_LOAD_DATA:
            owi_receive(addr_buf, 2);
            xfer_done_event = XFER_EEPROM_DUMP;
            break;
        case DEV_CMD_SAVE_CFG:
            fcfg_write(databuf);
            break;
        default:
            NOP;
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
        case XFER_EEPROM_DUMP:
            eep_read(0b111, *(uint16_t*) addr_buf, databuf, 64);
            // owi_receive(databuf, 64);
            // xfer_done_event = XFER_RESELECT;
            owi_select();
            break;
        default:
            break;
    }
}