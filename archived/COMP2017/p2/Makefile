CC       := gcc
CFLAGS   := -Wall -Wextra -std=c11 -Ilibs
LDFLAGS  := -lm

SRC_DIR  := source
LIB_DIR  := libs

.PHONY: all clean

all: server client

server: server.o markdown.o
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

client: client.o markdown.o
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

server.o: $(SRC_DIR)/server.c $(LIB_DIR)/markdown.h $(LIB_DIR)/document.h
	$(CC) $(CFLAGS) -c $< -o $@

client.o: $(SRC_DIR)/client.c $(LIB_DIR)/markdown.h $(LIB_DIR)/document.h
	$(CC) $(CFLAGS) -c $< -o $@

markdown.o: $(SRC_DIR)/markdown.c $(LIB_DIR)/markdown.h $(LIB_DIR)/document.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f server client *.o