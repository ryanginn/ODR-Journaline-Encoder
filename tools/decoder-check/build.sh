#!/usr/bin/env bash
# Builds a small command-line checker around the Fraunhofer IIS
# 'NewsService Journaline(R) Decoder' (GPLv2+, non-commercial use), using the
# copy shipped with Qt-DAB. Used to confirm that real receivers decode our output:
#
#   tools/decoder-check/build.sh
#   tools/decoder-check/check.py /path/to/journaline.dat [packet address]
#
# Needs git, g++ and zlib headers (apt install g++ zlib1g-dev git).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$HERE/build"
mkdir -p "$WORK"
if [ ! -d "$WORK/qt-dab" ]; then
    git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/JvanKatwijk/qt-dab.git "$WORK/qt-dab"
    git -C "$WORK/qt-dab" checkout -q HEAD -- sources/backend/data/journaline
fi
J="$WORK/qt-dab/sources/backend/data/journaline"
cd "$WORK"
gcc -c -w -I"$J" "$J/dabdgdec_impl.c" "$J/crc_8_16.c" "$J/log.c"
g++ -O1 -w -I"$J" -o "$HERE/build/jml-decode" "$HERE/main.cpp" "$J/NML.cpp" "$J/newsobject.cpp" "$J/Splitter.cpp" \
    dabdgdec_impl.o crc_8_16.o log.o -lz
echo "built $HERE/build/jml-decode"
