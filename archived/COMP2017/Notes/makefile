# Compiler settings
CC := gcc
CFLAGS := -Wall -Wextra -fsanitize=address,leak -g

# Directories
BUILD_DIR = build

all: $(BUILD_DIR)/dyn_arr $(BUILD_DIR)/l_list $(BUILD_DIR)/errno $(BUILD_DIR)/signal

$(BUILD_DIR)/dyn_arr: w4/dyn_arr.c
	$(CC) $(CFLAGS) $^ -o $@

$(BUILD_DIR)/l_list: w4/l_list.c
	$(CC) $(CFLAGS) $^ -o $@

$(BUILD_DIR)/errno: w5/errno.c
	$(CC) $(CFLAGS) $^ -o $@

$(BUILD_DIR)/signal: w5/signal.c
	$(CC) $(CFLAGS) $^ -o $@

clean:
	rm $(BUILD_DIR)/*
