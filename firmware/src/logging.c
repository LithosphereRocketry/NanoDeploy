#include "logging.h"

#include "common.h"
#include "eeprom_24c.h"

static struct data_frame* const frame_buf = (struct data_frame*) databuf;
// Note: the VSCode linter doesn't know MSP430 int sizes, so it may be confused
// about the size of struct data_frame; when compiled it seems to be correct

// This ensures that we don't have problems on the off-chance that sizeof struct
// data_frame isn't a factor of our buffer size by rounding to multiples of the
// frame size
static struct data_frame* const fbuf_endptr = frame_buf + dbuf_sz / (sizeof(struct data_frame));

struct data_frame* current_frame = frame_buf;

uint16_t eeprom_addr = 0;

void log_temp() {
    current_frame ++;
    if(current_frame == fbuf_endptr) current_frame = frame_buf;
}

void log_flush_temp() {
    /*
    We can use a bit of a trick here by exploiting the EEPROM's page-wrapping
    behavior. We want from current_frame...fbuf_endptr to land starting at 0,
    followed by frame_buf...current_frame. We can accomplish this by writing
    the more recent frame_buf...current_frame segment to EEPROM *first*, and
    then wrapping around to the beginning of the page for the remainder of
    the rolling buffer. e.g.:
    
    RAM frame no. [7 8 9 a b c d e f 0 1 2 3 4 5 6]
    current                          ^
    EEPROM        [                                ... ]
    EEPROM write                 ^

    EEPROM        [              7 8 9 ...         ... ]
    EEPROM write                       ^

    EEPROM        [              7 8 9 a b c d e f ... ]
    EEPROM write   ^ *wraps*

    EEPROM        [0 1 2 3 4 5 6 7 8 9 a b c d e f ... ]

    We do need to make sure our value wraps if the current pointer is at 0, or
    our write will start on the second page of EEPROM - this is easy with a
    mod-64, which will be optimized as a bitmask.
    */
    uint16_t eeprom_wrap_addr = (dbuf_sz - (current_frame - frame_buf) * sizeof(struct data_frame)) % dbuf_sz;
    eep_write_page(0b111, eeprom_wrap_addr, databuf, page_size);
    eeprom_addr = page_size;
}

void log_store() {
    current_frame ++;
    if(current_frame == fbuf_endptr) {
        eep_write_page(0b111, eeprom_addr, databuf, page_size);
        eeprom_addr += page_size;
        current_frame = frame_buf;
    };
}

void log_close() {
    uint16_t data_sz = (current_frame - frame_buf) * sizeof(struct data_frame);
    eep_write_page(0b111, eeprom_addr, databuf, data_sz);
}
