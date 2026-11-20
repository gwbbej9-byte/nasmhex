#!/bin/sh
# Linux host dump — no Docker. Builds if needed, prints samples/hello.bin.
set -eu
cd "$(dirname "$0")/.."
if [ ! -x ./nasmhex ]; then
    make
fi
./nasmhex samples/hello.bin
