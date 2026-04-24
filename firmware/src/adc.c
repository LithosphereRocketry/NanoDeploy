#include "adc.h"

#include <msp430.h>

volatile uint16_t adc_buf [6];

void adc_init() {
    ADC10CTL0 &= ~ENC;
    ADC10CTL0 = SREF_1      // internal reference / vss
              | ADC10SHT_3  // 64 cycle sample+hold
              | ADC10SR     // low rate
              | REFBURST    // reference only during burst
              | MSC         // multiple samples
              | REF2_5V     // 2.5V reference
              | REFON       // enable reference
              | ADC10ON;    // enable adc
    ADC10CTL1 = INCH_5      // highest channel is 5
              | CONSEQ_1;   // sequence of channels
    ADC10AE0 = BIT0         // channel 1
             | BIT3         // channel 0
             | BIT5;        // battery
    ADC10SA = (unsigned) &adc_buf;
    ADC10DTC0 = ADC10CT;
    ADC10DTC1 = 6;
    ADC10CTL0 |= ENC;
}

void adc_start() {
    while(ADC10CTL1 & ADC10BUSY);
    ADC10CTL0 |= ADC10SC;
    while(!(ADC10CTL1 & ADC10BUSY));
}