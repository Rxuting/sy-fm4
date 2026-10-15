CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wshadow
SRC = fm4.c fm4_tables.c

test: test_fm4
	mkdir -p wav && ./test_fm4

test_fm4: test_fm4.c $(SRC) fm4.h
	$(CC) $(CFLAGS) -fsanitize=address,undefined -o $@ test_fm4.c $(SRC) -lm

fm4_tables.c: gen_tables.py
	python3 gen_tables.py

clean:
	rm -rf test_fm4 wav

.PHONY: test clean
