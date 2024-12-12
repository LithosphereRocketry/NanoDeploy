MCU = msp430g2452

CC = msp430-elf-gcc
GDB = msp430-gdb

MSPDEBUG_MODE = tilib

CFLAGS = -mmcu=$(MCU) -Wall -Wextra -O2
DBGFLAGS = -g3
RLSFLAGS = 

SRC_DIR = src
INC_DIR = include
DEBUG_DIR = debug
RELEASE_DIR = release
LIB_DIR = external
LIB_DIR_I2C = $(LIB_DIR)/msp430_usi_i2c

DIRS = $(DEBUG_DIR) $(RELEASE_DIR) $(DEP_DIR)

CORE_SRCS = $(wildcard $(SRC_DIR)/*.c)

LIB_SRCS_I2C = $(wildcard $(LIB_DIR_I2C)/*.c)
SRCS = $(notdir $(CORE_SRCS) $(LIB_SRCS_I2C))
INLCUDE_DIRS = $(INC_DIR) $(LIB_DIR_I2C)

INCLUDE_FLAGS = $(INLCUDE_DIRS:%=-I%)

$(info $(LIB_SRCS))

DEBUG_OBJS = $(SRCS:%.c=$(DEBUG_DIR)/%.o)
RELEASE_OBJS = $(SRCS:%.c=$(RELEASE_DIR)/%.o)

HEADERS = $(wildcard $(INC_DIR)/*.h) $(wildcard $(LIB_DIR_I2C)/*.h)

$(info $(DEBUG_OBJS))

.PHONY: clean run gdb size

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

run: $(RELEASE_DIR)/firmware.elf
	mspdebug $(MSPDEBUG_MODE) "prog $(RELEASE_DIR)/firmware.elf"

gdb: $(DEBUG_DIR)/firmware.elf
	mspdebug $(MSPDEBUG_MODE) "prog $<" "gdb"

size: $(RELEASE_DIR)/firmware.elf
	msp430-readelf -l $<

clean:
	rm -rf $(DIRS)