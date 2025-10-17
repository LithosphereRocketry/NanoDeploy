#ifndef LOGGING_H
#define LOGGING_H

#include <stdint.h>

struct data_frame {
    uint16_t elapsed;
    uint16_t altitude;
    uint8_t state;
    uint8_t temp;
    uint8_t cont_drogue;
    uint8_t cont_main;
} __attribute__((packed));

extern struct data_frame* current_frame;

/**
 * Log the data stored in current_frame tentatively. Tentative data will be
 * accumulated until the common memory buffer is full, then older data will be
 * discarded in a rolling window.
 */
void log_temp();

/**
 * Commit all temporary data to EEPROM. Assumes at least one full wrap of the
 * buffer has occurred; otherwise a small amount of garbage data may be
 * recorded.
 */
void log_flush_temp(uint16_t start_time);

/**
 * Log the data stored in the current frame. Will accumulate data until the
 * buffer is full, then commit the entire buffer to EEPROM.
 */
void log_store();

/**
 * Force any non-committed data to be committed to EEPROM. Logging should not
 * be restarted to the same file after this is called as there may be additional
 * garbage data past the end of the correct data.
 */
void log_close();

#endif