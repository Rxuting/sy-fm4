CROSS ?= m68k-elf-
CC = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
NM = $(CROSS)nm
CFLAGS = -mcpu=54418 -O2 -ffreestanding -fno-builtin -fno-common -Wall -Wextra \
         -fomit-frame-pointer $(EXTRA)
IMAGE_END = 0x40330b90
OBJS = main_fm4.o

all: blob.bin stub.bin

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

blob.elf: $(OBJS) blob.ld
	$(CC) $(CFLAGS) -nostdlib -T blob.ld -o $@ $(OBJS) -lgcc
blob.bin: blob.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@
	$(NM) -n blob.elf > blob.map

# The stub sits at the image end; the blob follows it at the next 16 bytes
# past STUB_ROOM.
STUB_ROOM = 0x80
stub.bin: stub.S blob.elf
	$(CC) -mcpu=54418 -c stub.S -o stub.o \
	  -DBLOB_ADDR=0x47000000 -DBLOB_SRC=$$(( $(IMAGE_END) + $(STUB_ROOM) )) \
	  -DBOOT_FN=0x$$($(NM) blob.elf | awk '/ fm4m_boot$$/{print $$1}') \
	  -DBLOB_WORDS=$$(( ( $$(wc -c < blob.bin) + 3 ) / 4 )) \
	  -DBSS_WORDS=$$(( ( 0x$$($(NM) blob.elf | awk '/__bss_end/{print $$1}') - 0x$$($(NM) blob.elf | awk '/__blob_end/{print $$1}') ) / 4 ))
	$(OBJCOPY) -O binary stub.o $@

clean:
	rm -f *.o *.elf *.bin blob.map
.PHONY: all clean
