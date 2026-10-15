# How SY FM4 works (Syntakt OS 1.40A)

SY FM4 replaces SY TONE (machine id 4, DSP engine 4) as a compatible superset. All addresses below are 1.40A's.

## Main CPU (section 3): `engine/main/main_fm4.c`, `patch/s3patch.py`

| Piece | How |
|---|---|
| code | The blob is appended after the image (0x40330b90). A boot stub copies it to 0x47000000 before the bss clear: DDR above the OS's bss end (0x4554da50) and below its stack, which nothing addresses. |
| page 2/2 | SourcePageView vtable slots 19 (page name) and 47 (knob → descriptor) are overridden. The page view already cycles pages on a second press of its key (`FUN_4003b8a4`), so SY FM4 just gets a two-entry page list. |
| descriptors | 8 unused "Error" placeholders (1, 2, 3, 4, 5, 12, 13, 14) on logical indices 0x36..0x3d. Their knob/formatter/icon info is copied from SY TONE's RATIO/MOD/MENV and from SY DUAL VCO's DET. |
| defaults | Entered in the per-logical-index default tables (end of `FUN_400a4ef0`), so new sounds get them. |
| sound storage | Slots 0x36..0x3d of the sound storage (72 slots, 54 used before). The loader gives a sound saved by a stock OS (zeros there) page 2/2's defaults. |
| pattern locks | The runtime lock table is already 0x47 wide per step. Storage lanes for page 2/2 use ids 0x50..0x57, which a stock OS drops; an id of 0x36 would have loaded as a lock on Trig Note. |
| to the voice CPU | `fm4m_dma_wait` (replaces `FUN_400a10da`, the render's eDMA 47 wait) copies each synth track's page 2/2, locks applied, from the sequencer's per-track values to the shared RAM at 0x700 + voice·16. |

## Voice CPU (section 7): `engine/syn/fm4_syn.c`, `engine/fm4.c`, `patch/s7patch.py`

- Engine 4's prep and render table entries point at SY FM4. The blob is appended after the image (0x4005df10, inside section 7's bss); a stub in an unused zero area (0x4004f5c0) copies it out before the bss clear.
- SY TONE's prep always runs. It turns page 1 into SY TONE's voice state: pitch with TUNE/PNCH, RATIO scale, MOD amount, FDBK, MENV envelope, DEC, declick.
- **ALGO 0:** SY TONE's render, untouched.
- **ALGO ≥ 1:** four operators from that state plus page 2/2, then the firmware's DEC envelope, VCA and gate. OVER is the common per-voice stage after all engines, so it isn't applied here.
- **Units, as measured:**
  - SY TONE renders at 96 kHz, 64 samples a block; the carrier's step ≪ 9 gives the 32-bit increment at 48 kHz.
  - An operator's ratio is its slot scale / 0x4000000; RATIO uses table 0x40021604, and RAT3/RAT4 use the same table.
  - MOD, LEV3 and LEV4 go through table 0x40021804.
  - DET multiplies operators 2–4 by 2^(semitones/12).

## The engine: `engine/fm4.c`

- Operators are evaluated 4, 3, 2, 1 each sample.
- An edge from a later-evaluated operator, or from an operator to itself, reads the previous sample. These are the feedback edges, scaled by the feedback amount.
- A self edge reads the mean of the last two samples, as on the DX.
- Every algorithm is the same graph with some gains at zero, so one branch-free loop serves all eleven.
- Modulator envelopes are applied once per block; carrier envelopes ramp per sample.

## Verified

**In an emulator:**
- ALGO 0 is sample-identical to stock SY TONE (0 of 29 056 samples differ).
- All 11 algorithms sound, and pitches are exact:
  - C4 + TUNE 12 gives a 523.3 Hz carrier;
  - in algorithm 8, RAT3 2.0 and RAT4 3.0 give 1046.5 and 1569.8 Hz;
  - DET +12 moves operators 2–4 up exactly one octave.
- P-locks on page 2/2 reach the voice CPU in the trig's own block, and the base value returns on other steps.
- Persistence, through the firmware's own serialisers:
  - a sound round trip is exact, including page 2/2;
  - a stock-format sound gets the defaults;
  - pattern locks round-trip.
- Main CPU render: worst case 85.8k of 166.7k cycles a block, against 85.0k for stock. Copying page 2/2 costs about 0.9k cycles a block.

**On hardware:**
- installs, runs, all parameters work, p-locks work;
- 8 voices sustained, recorded clean.

## Known limits

- A project saved with page 2/2 locks and opened on a stock OS drops those lanes.
- Descriptors 1–5 and 12–14 had MIDI CC placeholders in 1.40A (CC 1, 2, 6, 7, 10, 120, 121, 123). SY FM4 removes them; on SY TONE those CCs did nothing either.
