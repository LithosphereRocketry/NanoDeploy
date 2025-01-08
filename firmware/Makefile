MCU = msp430g2452

CC = msp430-elf-gcc

MKDIV = misc/make_divider.py

MSPDEBUG_MODE = tilib

CFLAGS = -mmcu=$(MCU) -Wall -Wextra -Wpedantic
DBGFLAGS = -g3 -O2
RLSFLAGS = -O2

SRC_DIR = src
INC_DIR = include
DEBUG_DIR = debug
RELEASE_DIR = release
LIB_DIR = external
LIB_DIR_I2C = $(LIB_DIR)/msp430_usi_i2c
INC_GEN_DIR = include/generated

DIRS = $(DEBUG_DIR) $(RELEASE_DIR) $(DEP_DIR) $(INC_GEN_DIR)

CORE_SRCS = $(wildcard $(SRC_DIR)/*.c)

LIB_SRCS_I2C = $(wildcard $(LIB_DIR_I2C)/*.c)
SRCS = $(notdir $(CORE_SRCS) $(LIB_SRCS_I2C))
INLCUDE_DIRS = $(INC_DIR) $(LIB_DIR_I2C)

INCLUDE_FLAGS = $(INLCUDE_DIRS:%=-I%)

DEBUG_OBJS = $(SRCS:%.c=$(DEBUG_DIR)/%.o)
RELEASE_OBJS = $(SRCS:%.c=$(RELEASE_DIR)/%.o)

HEADERS = $(wildcard $(INC_DIR)/*.h) $(wildcard $(LIB_DIR_I2C)/*.h) $(INC_GEN_DIR)/atm_div_k.h $(INC_GEN_DIR)/atm_div_tl.h $(INC_GEN_DIR)/gzp_div_conv.h

.PHONY: clean run gdb size generated

# Linker
$(DEBUG_DIR)/firmware.elf: $(DEBUG_OBJS) | $(DEBUG_DIR)
	$(CC) $(CFLAGS) $(DEBUG_OBJS) -o $@
$(RELEASE_DIR)/firmware.elf: $(DEBUG_OBJS) | $(RELEASE_DIR)
	$(CC) $(CFLAGS) $(DEBUG_OBJS) -o $@

# Core source files
$(DEBUG_DIR)/%.o: $(SRC_DIR)/%.c $(HEADERS) | $(DEBUG_DIR)
	$(CC) $(CFLAGS) $(DBGFLAGS) -c $< $(INCLUDE_FLAGS) -o $@
$(RELEASE_DIR)/%.o: $(SRC_DIR)/%.c $(HEADERS) | $(RELEASE_DIR)
	$(CC) $(CFLAGS) $(RLSFLAGS) -c $< $(INCLUDE_FLAGS) -o $@

# USI I2C library source files
$(DEBUG_DIR)/%.o: $(LIB_DIR_I2C)/%.c $(HEADERS) | $(DEBUG_DIR)
	$(CC) $(CFLAGS) $(DBGFLAGS) -c $< $(INCLUDE_FLAGS) -o $@
$(RELEASE_DIR)/%.o: $(LIB_DIR_I2C)/%.c $(HEADERS) | $(RELEASE_DIR)
	$(CC) $(CFLAGS) $(RLSFLAGS) -c $< $(INCLUDE_FLAGS) -o $@

$(DIRS): %:
	mkdir -p $@

# Atmospheric constant K = 5.25588
$(INC_GEN_DIR)/atm_div_k.h: $(MKDIV) | $(INC_GEN_DIR)
	$< -o $@ -n div_k -b 32 5.25588
# Post-scaling step
# Lmb = 0.0065
# Tmb = 288.15
# Using python as a calculator here because bc is weird
$(INC_GEN_DIR)/atm_div_tl.h: $(MKDIV) | $(INC_GEN_DIR)
	$< -o $@ -n div_tl -b 16 `python3 -c "print((0.0065/288.15) * (1<<16))"`
# (DMAX-DMIN) / (PMAX-PMIN) for GZP6816D conversion
$(INC_GEN_DIR)/gzp_div_conv.h: $(MKDIV) | $(INC_GEN_DIR)
	$< -o $@ -n div_conv -b 32 `python3 -c "print((15099494 - 1677722)/(110000 - 30000))"`

run: $(RELEASE_DIR)/firmware.elf
	mspdebug $(MSPDEBUG_MODE) "prog $(RELEASE_DIR)/firmware.elf"

gdb: $(DEBUG_DIR)/firmware.elf
	mspdebug $(MSPDEBUG_MODE) "prog $<" "gdb"

size: $(RELEASE_DIR)/firmware.elf
	msp430-size $<

clean:
	rm -rf $(DIRS)