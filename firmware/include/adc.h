#ifndef ADC_H
#define ADC_H

#include <stdint.h>

volatile extern uint16_t adc_buf[6];

void adc_init();
void adc_start();

#endif