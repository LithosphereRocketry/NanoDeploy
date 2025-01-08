#ifndef EEPROM_24C
#define EEPROM_24C

#include <stddef.h>
#include <stdint.h>

/**
 * Simple library for 24C series EEPROMs up to 64 KB (24C512). 
 */

/**
 * Write data buffer to EEPROM, single page
 * 
 * If the given block is not 64-byte aligned, write will wrap around from the
 * end of the current page to the beginning of the same page. E.g., writing 8
 * bytes starting at address 0x003C will write addresses 0x003C-0x003F and
 * 0x0000-0x0003.
 */
void eep_write_page(uint8_t dev_sel, uint16_t addr, const uint8_t* data, size_t len);

void eep_read(uint8_t dev_sel, uint16_t addr, uint8_t* data, size_t len);


#endif