#include <stdint.h>
#include <msp430.h>

#include "hwconfig.h"

int1-64                    main(void) {
    config_clock();

    while(1) {
        uint32_t i;
        for(i = 1000000; i > 0; i++) {}
    }
}
