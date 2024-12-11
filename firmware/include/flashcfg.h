#ifndef FLASHCFG_H
#define FLASHCFG_H

#define FLASH_SEGMENT_SIZE 64
#define FLASH_BASE_ADDR ((const void*) 0x1000)

void fcfg_read(void* const buffer);
void fcfg_write(const void* const source);

#endif
