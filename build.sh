#!/bin/sh
# Build SY FM4 into your own copy of Syntakt OS 1.40A.
#
#   ./build.sh path/to/Syntakt_OS1.40A.syx [out.syx]
#
# Needs: elektron-firmware-tool (https://github.com/mischa85/elektron-firmware-tool,
# set EFT=/path/to/it if it is not in PATH), a ColdFire cross gcc (m68k-elf-gcc by
# default; CROSS=m68k-linux-gnu- for the Debian/Ubuntu package), python3, make.
set -eu

STOCK=$1
OUT=${2:-out/Syntakt_OS1.40A-syfm4.syx}
EFT=${EFT:-elektron-firmware-tool}
STOCK_SHA256=266a5a3022ff565bf470173147b7f3005b7da8ef80724b6271836818ac2b5828

sha=$( (sha256sum "$STOCK" 2>/dev/null || shasum -a 256 "$STOCK") | cut -d' ' -f1)
if [ "$sha" != "$STOCK_SHA256" ]; then
    echo "$STOCK is not the stock Syntakt OS 1.40A (sha256 $sha)" >&2
    exit 1
fi

rm -rf out/stock && mkdir -p out/stock "$(dirname "$OUT")"
"$EFT" -i "$STOCK" -d 3 -d 7 -o out/stock >/dev/null
S3=$(ls out/stock/section_3_*)
S7=$(ls out/stock/section_7_*)

make -C engine/syn
make -C engine/main

python3 patch/s7patch.py "$S7" engine/syn/blob.bin engine/syn/stub.bin out/section7.raw --hijack 4
python3 patch/s3patch.py "$S3" engine/main/blob.bin engine/main/stub.bin engine/main/blob.map out/section3.bin

"$EFT" -i "$STOCK" -l 3 -c 3 out/section3.bin -c 7 out/section7.raw -o "$OUT" >/dev/null
"$EFT" -i "$OUT" | grep -q 'checksums : ok' || { echo "checksums failed" >&2; exit 1; }
echo "OK $OUT"
