#include "eeprom_24c.h"

#include <msp430.h>

#include "common.h"
#include "i2c_helpers.h"

#define EEPROM_I2C_BASE 0b1010000

void eep_write_page(uint8_t dev_sel, uint16_t addr, const uint8_t* data, size_t len) {
    uint16_t seq[] = {
        ((EEPROM_I2C_BASE | dev_sel) << 1) | WRITE_BIT,
        addr >> 8,
        addr & 0xFF,
        I2C_WRITE_N
    };
    static const size_t seq_len = sizeof(seq)/sizeof(uint16_t) - 1;

    // We know (but the compiler doesn't) that this sequence won't violate const
    i2c_send_sync(seq, seq_len + len, (uint8_t*) data, SLEEP_BITS);
}


// void eep_write(uint8_t dev_sel, uint16_t addr, const uint8_t* data, size_t len) {
//     uint16_t seq[] = {
//         ((EEPROM_I2C_BASE | dev_sel) << 1) | WRITE_BIT,
//         0,
//         0,
//         I2C_WRITE_N
//     };
//     const size_t seq_len = sizeof(seq)/sizeof(uint16_t) - 1;

//     size_t prologue_len = (-addr) & 0x4F; // Number of writes to page-align
//     insert_addr(seq, addr);
//     // We know (but the compiler doesn't) that this sequence won't violate const
//     i2c_send_sync(seq, seq_len + prologue_len, (uint8_t*) data, SLEEP_BITS);
//     addr += prologue_len;
//     data += prologue_len;
//     len -= prologue_len;

//     // Write in multiples of 64-byte pages using page write mode for better perf
//     while(len > 64) {
//         insert_addr(seq, addr);
//         i2c_send_sync(seq, seq_len + 64, (uint8_t*) data, SLEEP_BITS);
//         addr += 64;
//         data += 64;
//         len -= 64;
//     }

// }

void eep_read(uint8_t dev_sel, uint16_t addr, uint8_t* data, size_t len) {
    uint16_t seq[] = {
        ((EEPROM_I2C_BASE | dev_sel) << 1) | WRITE_BIT,
        addr >> 8,
        addr & 0xFF,
        I2C_RESTART,
        ((EEPROM_I2C_BASE | dev_sel) << 1) | READ_BIT,
        I2C_READ_N
    };
    static const size_t seq_len = sizeof(seq)/sizeof(uint16_t) - 1;

    // eep_write_page(dev_sel, addr, NULL, 0);
    i2c_send_sync(seq, seq_len + len, data, SLEEP_BITS);
}