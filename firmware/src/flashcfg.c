
#include "flashcfg.h"

#include <msp430.h>
#include <stdint.h>
#include <string.h>


void fcfg_read(void* const buffer) {
    memcpy(buffer, FLASH_BASE_ADDR, FLASH_SEGMENT_SIZE);
}

void fcfg_write(const void* const buffer) {
    uint16_t* flash_ptr = (uint16_t*) FLASH_BASE_ADDR;
    uint16_t* buf_ptr = (uint16_t*) buffer;

    // Assumes ACCVIE = NMIIE = OFIE = 0.
    // disable WDT
    FCTL2 = FWKEY | FSSEL_2 | (40-1); // source SMCLK, divide by 40 -> 16MHz/40 = 400kHz
    FCTL3 = FWKEY; // Unlock flash
    FCTL1 = FWKEY | ERASE; // Set erase mode

    *flash_ptr = 0; // dummy write to trigger erase

    FCTL1 = FWKEY | WRT; // disable erase, enable write

    uint8_t i;
    for(i = 0; i < FLASH_SEGMENT_SIZE/sizeof(uint16_t); i++) {
        flash_ptr[i] = buf_ptr[i];
    }

    FCTL1 = FWKEY; // disable write
    FCTL3 = FWKEY | LOCK; // set lock
    // reenable WDT
}
