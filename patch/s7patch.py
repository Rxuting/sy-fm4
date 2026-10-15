"""Patch Syntakt OS 1.40A's section 7 (the second CPU) with the SY FM4 engine.

    python3 s7patch.py STOCK_SECTION7 BLOB STUB OUT --hijack 4

Layout (all addresses as the second CPU sees them; section 7 loads at
0x40000400):

  0x4004f5c0  the boot stub (engine/syn/stub.S): 256 bytes of zeros that
              nothing in section 7 reads or writes, so it survives a restart
              of section 7's bring-up after bzero.
  0x4005df10  the engine blob, appended after the image. 0x4004f6e0 to here
              is the SRAM's initial data (0x400004bc copies it to 0x80000000
              and 0x80008000) and from 0x4004f6e0 on is bss, which 0x40000512
              clears: so the stub copies the blob out before that.
  0x400010b4  `jsr 0x400004bc; jsr 0x40000512` (8 bytes) becomes
              `jsr stub.l; nop`. The stub makes both calls itself.
  tables      --hijack N points engine N's prep and render at FM4 (a test
              of the engine alone, on a machine that already exists).
              The release build hijacks engine 4 (SY TONE): SY FM4's ALGO 0
              is SY TONE itself.

The section must stay below 0x60000 - 5 bytes: the main CPU's boot task
refuses a larger one (0x40081d92 in MAIN OS 1.40A).

Nothing here stores firmware bytes: it reads the stock section given, checks
the SHA-256 of every byte range it overwrites against 1.40A's, and writes OUT.
"""
import argparse
import hashlib
import struct
import sys

LOAD = 0x40000400
IMAGE_END = 0x4005df10          # 1.40A's section 7 ends here; the blob follows
STUB_AT = 0x4004f5c0            # 256 bytes nothing in section 7 touches
STUB_ROOM = 0x100
MAX_SIZE = 0x60000 - 5
CALL_SITE = 0x400010b4
CALL_WAS = (8, '6756cbf3a5025d1c73312200e906c6c4c691b2f87a719aedbeda37221436cc3e')  # jsr 0x400004bc; jsr 0x40000512
RENDER_TABLE = 0x400148f0
PREP_TABLE = 0x40014920
MAP_TABLE = 0x40014950
ENGINES = 12
BLOB_ADDR = 0x47000000


def u32(img, addr):
    return struct.unpack_from('>I', img, addr - LOAD)[0]


def put(img, addr, data, expect=None):
    """Write data at addr. expect = (length, sha256 hex) of the stock bytes there:
    the patch refuses an image that is not stock 1.40A (no firmware bytes stored here)."""
    off = addr - LOAD
    if expect is not None:
        n, digest = expect
        if hashlib.sha256(bytes(img[off:off + n])).hexdigest() != digest:
            raise SystemExit('unexpected bytes at 0x%08x: not stock 1.40A?' % addr)
    if off + len(data) > len(img):
        img.extend(bytes(off + len(data) - len(img)))
    img[off:off + len(data)] = data


def patch(stock, blob, stub, hijack=None):
    img = bytearray(stock)
    if struct.unpack_from('>I', img, 0)[0] != 0x40001070:
        raise SystemExit('not section 7 of Syntakt OS 1.40A (entry 0x%08x)'
                         % struct.unpack_from('>I', img, 0)[0])
    if len(stub) % 4:
        raise SystemExit('stub must be a whole number of longwords')
    prep, render = struct.unpack_from('>II', blob, 0)
    if not (BLOB_ADDR <= prep < BLOB_ADDR + len(blob) and
            BLOB_ADDR <= render < BLOB_ADDR + len(blob)):
        raise SystemExit('blob entry table does not point into the blob')
    # the stub into its hole, the blob into the dead tail
    if len(stub) > STUB_ROOM:
        raise SystemExit('stub is %d bytes; the hole has %d' % (len(stub), STUB_ROOM))
    if any(img[STUB_AT - LOAD:STUB_AT - LOAD + len(stub)]):
        raise SystemExit('the stub hole is not empty: not stock 1.40A?')
    put(img, STUB_AT, stub)
    if len(img) != IMAGE_END - LOAD:
        raise SystemExit('section 7 is %d bytes, not 1.40A\'s %d' % (len(img), IMAGE_END - LOAD))
    put(img, IMAGE_END, blob)
    if len(img) > MAX_SIZE:
        raise SystemExit('section 7 would be %d bytes; the limit is %d'
                         % (len(img), MAX_SIZE))
    # the boot call
    put(img, CALL_SITE, b'\x4e\xb9' + struct.pack('>I', STUB_AT) + b'\x4e\x71',
        expect=CALL_WAS)
    if hijack is not None:
        put(img, PREP_TABLE + 4 * hijack, struct.pack('>I', prep))
        put(img, RENDER_TABLE + 4 * hijack, struct.pack('>I', render))
    return bytes(img), prep, render


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stock')
    ap.add_argument('blob')
    ap.add_argument('stub')
    ap.add_argument('out')
    ap.add_argument('--hijack', type=int, help='engine index to replace (test)')
    a = ap.parse_args()
    stock = open(a.stock, 'rb').read()
    out, prep, render = patch(stock, open(a.blob, 'rb').read(),
                              open(a.stub, 'rb').read(), a.hijack)
    open(a.out, 'wb').write(out)
    print('section 7: %d -> %d bytes (limit %d); prep 0x%08x render 0x%08x%s'
          % (len(stock), len(out), MAX_SIZE, prep, render,
             '; engine %d hijacked' % a.hijack if a.hijack is not None else ''))


if __name__ == '__main__':
    sys.exit(main())
