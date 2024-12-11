MCU = msp430g2452

CC = msp430-gcc
GDB = msp430-gdb

MSPDEBUG_MODE = tilib

CFLAGS = -mmcu=$(MCU) -Wall -Wextra

SRC_DIR = src
INC_DIR = include
DEBUG_DIR = debug
RELEASE_DIR = release
DEP_DIR = deps

DIRS = $(DEBUG_DIR) $(RELEASE_DIR) $(DEP_DIR)

DEBUG_OBJS = $(patsubst $(SRC_DIR)/%.c,$(DEBUG_DIR)/%.o,$(wildcard $(SRC_DIR)/*.c))
RELEASE_OBJS = $(patsubst $(SRC_DIR)/%.c,$(RELEASE_DIR)/%.o,$(wildcard $(SRC_DIR)/*.c))

HEADERS = $(wildcard $(INC_DIR)/*.h)

$(info $(DEBUG_OBJS))

.PHONY: clean run gdb size

$(DEBUG_DIR)/firmware.elf: $(DEBUG_OBJS) | $(DEBUG_DIR)
	$(CC) $(CFLAGS) $(DEBUG_OBJS) -o $@

$(RELEASE_DIR)/firmware.elf: $(DEBUG_OBJS) | $(RELEASE_DIR)
	$(CC) $(CFLAGS) $(DEBUG_OBJS) -o $@

$(DEBUG_DIR)/%.o: $(SRC_DIR)/%.c $(HEADERS) | $(DEBUG_DIR)
	$(CC) $(CFLAGS) -O0 -g3 -c $< -I$(INC_DIR) -o $@

$(RELEASE_DIR)/%.o: $(SRC_DIR)/%.c $(HEADERS) | $(RELEASE_DIR)
	$(CC) $(CFLAGS) -O0 -c $< -I$(INC_DIR) -o $@

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