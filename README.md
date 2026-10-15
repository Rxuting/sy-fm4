# SY FM4 for Elektron Syntakt

A four-operator FM machine for the Syntakt's digital tracks. It upgrades **SY TONE** in place, so existing projects keep sounding the same: ALGO 0 *is* SY TONE, and ALGO 1–11 are four-operator algorithms. The extra parameters go on a second SYN page.

**Target:** Syntakt OS **1.40A** only (SHA-256 `266a5a30…2b5828`). Ports to 1.41 and 1.42 aren't done yet (see [Porting](#porting)).

> **Not affiliated with Elektron.** Modified firmware can make your device unusable and may void your warranty. This repository contains **no Elektron firmware**: the patchers read your own copy of the stock OS and check the SHA-256 of every byte range they overwrite. Don't share built `.syx` files.

## What you get

- **SYN 1/2:** SY TONE's page, unchanged: `TUNE RATIO PNCH DEC` / `FDBK MOD MENV OVER`.
- **SYN 2/2:** press SYN again:
  - top row (operator 3): `ALGO RAT3 LEV3 DEC3`;
  - bottom row (operator 4): `DET RAT4 LEV4 DEC4`.
- **ALGO 0:** SY TONE itself. Its output is sample-identical to the stock machine.
- **ALGO 1–8:** the classic Yamaha 4-op set.
- **ALGO 9–11:** tree, diamond and ring.
- **DET** detunes operators 2–4 by ±16 semitones, with fine steps.
- Page 2/2 is saved with the sound and **p-lockable**. A sound saved by a stock OS opens with page 2/2's defaults, i.e. as SY TONE.

## Status

Tested on a real Syntakt (OS 1.40A):
- the update installs and SY FM4 runs;
- every parameter works, including p-locks on trigs;
- load test: 8 tracks of SY FM4 sustained for 47 s, recorded clean (no clicks, dropouts or clipping).

Verified in an emulator ([digiemu](https://github.com/irpina/digiemu) with a Syntakt port) but not yet on the device:
- sound and pattern-lock save/reload, using the firmware's own serialisers;
- CPU cost: SY FM4 uses about 8.9k cycles per voice per block, comparable to the stock engines (7.2k–9.8k). With 8 voices on SY FM4, the voice CPU stays at about 66 %.

## Build

You need:
- your own `Syntakt_OS1.40A.syx`, downloaded from Elektron;
- [elektron-firmware-tool](https://github.com/mischa85/elektron-firmware-tool);
- a ColdFire cross gcc (`m68k-elf-gcc`, or `CROSS=m68k-linux-gnu-` for the Debian/Ubuntu package);
- `python3` and `make`.

```sh
EFT=/path/to/elektron-firmware-tool ./build.sh path/to/Syntakt_OS1.40A.syx
# -> out/Syntakt_OS1.40A-syfm4.syx
```

The output is deterministic. The build verified here has SHA-256 `252e12ea25773178ecaeab45c4aa59871a9a50e74bf47cc44c85b23d670e4509`, the image that was tested on hardware.

To run the engine's host tests (a double-precision reference, structural checks, and a WAV per algorithm):

```sh
make -C engine test
```

## Flash and recover

- **Flash:** Elektron Transfer, *Drop* page, as for an official OS.
- **Go back:** flash the stock 1.40A the same way.
- **If the unit doesn't boot:** hold [FUNC] at power-on, then [TRIG 4] (OS UPGRADE). Send the stock OS from Transfer's *Legacy OS upgrade* page over **MIDI DIN**; USB doesn't work in this mode. Know this procedure before you flash.

## Layout

| Path | What |
|---|---|
| `engine/fm4.c`, `fm4.h`, `fm4_tables.c` | the portable 4-op engine: fixed point, 32-bit hot loop, one branch-free graph for all 11 algorithms |
| `engine/syn/` | second CPU (section 7): `fm4_syn.c` runs SY TONE's prep, then the 4 operators, then the firmware's DEC/VCA/gate; `stub.S` boot copy |
| `engine/main/` | main CPU (section 3): `main_fm4.c` covers the second SYN page, descriptors, sound storage, pattern-lock lanes and page 2/2 → shared RAM; `stub.S` boot copy |
| `patch/s7patch.py`, `patch/s3patch.py` | apply the blobs to your stock sections, checking every overwritten range by SHA-256 |
| `docs/DESIGN.md` | how it works, with the 1.40A addresses |

## Porting

Everything above the engine is tied to 1.40A addresses. Two lists hold them:
- the `#define`s and comments in `engine/syn/fm4_syn.c` and `engine/main/main_fm4.c`;
- the constants and `put()` sites in the two patchers.

For 1.41/1.42, map each one, for example with the per-region offset approach in [SyntHack's `os-1.42` branch](https://github.com/Rxuting/Synthack-OS/tree/os-1.42) (`tools/build/osver.py`). Then re-check:
- **Section 7's size limit** (0x60000 − 5 bytes in 1.40A).
- **Main OS layout:** the bss end and the 0x47000000 load address.
- **Descriptors 1–5 and 12–14.** Page 2/2 reuses these "Error" placeholder descriptors. In 1.40A they carried MIDI CC placeholders (CC 1, 2, 6, 7, 10, 120, 121, 123), which SY FM4 removes. [SyntHack](https://github.com/Angelo-politek/Synthack-OS) notes that logical ids 1–5 and 11–18 are tied to MIDI CCs, so pick placeholders that are really free in the target OS.

## License

MIT, see [LICENSE](LICENSE). Elektron and Syntakt are trademarks of Elektron Music Machines; this project isn't affiliated with or endorsed by them.
