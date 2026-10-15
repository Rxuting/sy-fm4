CROSS ?= m68k-elf-
CC = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
NM = $(CROSS)nm
CFLAGS = -mcpu=54418 -O2 -ffreestanding -fno-builtin -fno-common -Wall -Wextra \
         -fomit-frame-pointer -I.. $(EXTRA)
OBJS = entries.o fm4_syn.o fm4_syn_tables.o fm4.o fm4_tables.o

all: blob.bin stub.bin

fm4.o: ../fm4.c ../fm4.h
	$(CC) $(CFLAGS) -c $< -o $@
fm4_tables.o: ../fm4_tables.c
	$(CC) $(CFLAGS) -c $< -o $@
%.o: %.c ../fm4.h
	$(CC) $(CFLAGS) -c $< -o $@
fm4_syn_tables.c: gen_syn_tables.py
	python3 gen_syn_tables.py

blob.elf: $(OBJS) blob.ld
	$(CC) $(CFLAGS) -nostdlib -T blob.ld -o $@ $(OBJS) -lgcc
blob.bin: blob.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@
	$(NM) -n blob.elf > blob.map

# The stub needs the blob's size and bss: assembled after the blob.
stub.bin: stub.S blob.elf
	$(CC) -mcpu=54418 -c stub.S -o stub.o \
	  -DBLOB_ADDR=0x47000000 -DBLOB_SRC=0x4005df10 \
	  -DBLOB_ENTRY0=0x$$($(NM) blob.elf | awk '/ syn_fm4_prep$$/{print $$1}') \
	  -DBLOB_WORDS=$$(( ( $$(wc -c < blob.bin) + 3 ) / 4 )) \
	  -DBSS_WORDS=$$(( ( 0x$$($(NM) blob.elf | awk '/__bss_end/{print $$1}') - 0x$$($(NM) blob.elf | awk '/__blob_end/{print $$1}') ) / 4 ))
	$(OBJCOPY) -O binary stub.o $@

clean:
	rm -f *.o *.elf *.bin blob.map
.PHONY: all clean
