"""Patch Syntakt OS 1.40A's section 3 (MAIN OS) for SY FM4.

    python3 s3patch.py STOCK_SECTION3 BLOB STUB BLOB_MAP OUT

  0x40330b90  image end: the boot stub (engine/main/stub.S), padded to
              STUB_ROOM, then the blob. 0x40322000.. is bss (cleared by
              0x400004b2), so the stub copies the blob to 0x47000000 first.
  0x4000053e  `jsr 0x4000045c; jsr 0x400004b2` (pc-relative, 8 bytes)
              becomes `jsr stub.l; nop`.
  vtable      SourcePageView (vptr 0x401b645c): slot 19 (page name) and
              slot 47 (knob -> descriptor) point into the blob.
  records     eight unused "Error" descriptors become page 2/2's, from the
              blob's fm4m_records.
  names       machine 4 "SY TONE"/"SYTN" becomes "SY FM4"/"SYF4".
  storage     the sound (de)serialisers (0x400a640a, 0x400a6022) walk the
              blob's 0x47-entry slot tables to logical index 0x3d (the
              loader through fm4m_load_shim, which also gives sounds saved
              by a stock OS page 2/2's defaults); the
              pattern-lock writers (0x400a71be, 0x400a7320) take lane ids
              from the blob; the lane reader (0x400a6fb0) accepts ids to
              0x57; FUN_400a5d5e (slot/lane -> logical index) becomes
              fm4m_phys_to_lix.
  transport   FUN_400a10da (the render's eDMA 47 wait) becomes fm4m_dma_wait,
              which also copies page 2/2 to the shared RAM.
  defaults    FUN_400a4ef0's last store calls fm4m_index_done, which enters
              page 2/2 in the per-logical-index default tables.

Every overwritten byte is checked against what 1.40A has there. Nothing
here stores firmware bytes.
"""
import hashlib
import struct
import sys

LOAD = 0x40000400
IMAGE_END = 0x40330b90
STUB_ROOM = 0x80
BLOB_ADDR = 0x47000000
CALL_SITE = 0x4000053e
CALL_WAS = (8, 'dbd7ee3ac848bc629a889c3a534a8b23d8bb88fb05c5dd9f8f825696a3c6b633')  # jsr 0x4000045c; jsr 0x400004b2 (pc-relative)
SRC_VPTR = 0x401b645c
SLOT_TITLE, TITLE_WAS = 19, 0x40043bfc
SLOT_RECORD, RECORD_WAS = 47, 0x40043f9c
RECORDS = 0x40219a9c
REC = 0x34
PAGE2_N = 8
ERROR_NAME = 0x402360ca
NAME_AT, NAME_NEW = 0x4023cd50, b'SY FM4\0\0'      # was 'SY TONE'
SHORT_AT, SHORT_NEW = 0x4023cd58, b'SYF4\0'         # was 'SYTN'


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


def was(b):
    """(length, sha256) of bytes we can state ourselves (an address, an opcode)."""
    return (len(b), hashlib.sha256(b).hexdigest())


def symbols(path):
    out = {}
    for line in open(path):
        a, _t, name = line.split()
        out[name] = int(a, 16)
    return out


def patch(stock, blob, stub, syms):
    img = bytearray(stock)
    if len(img) != IMAGE_END - LOAD:
        raise SystemExit('section 3 is %d bytes, not 1.40A\'s %d' % (len(img), IMAGE_END - LOAD))
    if len(stub) > STUB_ROOM:
        raise SystemExit('stub is %d bytes; room %d' % (len(stub), STUB_ROOM))
    put(img, IMAGE_END, stub + bytes(STUB_ROOM - len(stub)) + blob)
    put(img, CALL_SITE, b'\x4e\xb9' + struct.pack('>I', IMAGE_END) + b'\x4e\x71',
        expect=CALL_WAS)
    entries = struct.unpack_from('>2I', blob, 0)
    put(img, SRC_VPTR + 4 * SLOT_RECORD, struct.pack('>I', entries[0]),
        expect=was(struct.pack('>I', RECORD_WAS)))
    put(img, SRC_VPTR + 4 * SLOT_TITLE, struct.pack('>I', entries[1]),
        expect=was(struct.pack('>I', TITLE_WAS)))
    recs = syms['fm4m_records'] - BLOB_ADDR
    idx = syms['fm4m_record_index'] - BLOB_ADDR
    for i in range(PAGE2_N):
        r = struct.unpack_from('>I', blob, idx + 4 * i)[0]
        at = RECORDS + r * REC
        old = struct.unpack_from('>13I', img, at - LOAD)
        if old[0] != 0xffffffff or old[1] != 0xffffffff or old[10] != ERROR_NAME:
            raise SystemExit('descriptor %d is not an unused placeholder' % r)
        put(img, at, blob[recs + REC * i:recs + REC * (i + 1)])
    def lea(at, opcode, old, sym):
        put(img, at, opcode + struct.pack('>I', syms[sym]), expect=was(opcode + struct.pack('>I', old)))

    lea(0x400a6462, b'\x41\xf9', 0x402205a4, 'fm4m_sound_l2p')   # lea table,a0
    put(img, 0x400a647e, b'\x72\x7c', expect=(2, '52df7f2f1048dc2201a77314d0f8b6896e89a31c0d6f679874a9f29a4dea2bf3'))          # moveq #0x3e*2,d1
    # the deserialiser's slot loop -> jsr fm4m_load_shim; lea p2l,a1; nops
    put(img, 0x400a6096,
        b'\x4e\xb9' + struct.pack('>I', syms['fm4m_load_shim'])
        + b'\x43\xf9' + struct.pack('>I', syms['fm4m_sound_p2l']) + b'\x4e\x71' * 11,
        expect=(34, '05940b0d2349f1f1c2ab4128a080a7a1663c0ed93299b900b0c038eb396ea31b'))
    lea(0x400a71f6, b'\x4b\xf9', 0x402205a4, 'fm4m_lane_of_lix')  # lea table,a5
    lea(0x400a7362, b'\x45\xf9', 0x402205a4, 'fm4m_lane_of_lix')  # lea table,a2
    put(img, 0x400a706a, b'\x7a\x57', expect=(2, 'cb0f6349d7f4b961d8b4c8deb6f4744d68bdc98d27283aefd7b40869c9d0c2fe'))          # moveq #0x57,d5
    jmp = lambda sym: b'\x4e\xf9' + struct.pack('>I', syms[sym])
    put(img, 0x400a5d5e, jmp('fm4m_phys_to_lix'), expect=(6, '3be507936205af3def3579799b294d7edfd234979554e6c0dd020b9b0d8f8740'))
    put(img, 0x400a10da, jmp('fm4m_dma_wait'), expect=(6, '1d0f8d759721ca0afb32976fc47fd063ea80bed69b7aa8927c10146be4d173fa'))
    put(img, 0x400a51dc, b'\x4e\xb9' + struct.pack('>I', syms['fm4m_index_done']),
        expect=(6, '9afe6ac16a3c77f05bd62a80e1554027625cb4c1eda2dfd69e986eb36491a906'))
    put(img, NAME_AT, NAME_NEW, expect=(8, 'd7e4479bceefa3f00a29e38e34dddd9bf3fe0f282248a4dfed4506266ba21ef5'))
    put(img, SHORT_AT, SHORT_NEW, expect=(5, '74e17376873aceed5a8c09e09452536cc08ca0f25cf379fc308b05c59bb3c16d'))
    return bytes(img)


def main():
    stock, blob, stub, mp, out = sys.argv[1:6]
    blob_b = open(blob, 'rb').read()
    res = patch(open(stock, 'rb').read(), blob_b, open(stub, 'rb').read(), symbols(mp))
    open(out, 'wb').write(res)
    print('section 3: %d -> %d bytes (+%d)' % (IMAGE_END - LOAD, len(res),
                                             len(res) - (IMAGE_END - LOAD)))


if __name__ == '__main__':
    sys.exit(main())
