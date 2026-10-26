#!/bin/bash
# Build the standalone LKH-3.0.8 (elkai 2.0.1 sdist copy, https://pypi.org/project/elkai/2.0.1/,
# sha256 1d8204b85fc960d2619c280e6143b14c1b62e09c532b388fff51e40e18404ba4) with the explicit-matrix driver.
# usage: build.sh EXTRACTED_ELKAI_DIR OUT_BINARY
set -e
E=$1; OUT=$2; HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$E/LKH-3.0.8/SRC
FILES=$(ls $SRC/*.c | grep -v -E "/LKHmain\.c$")
TMP=$(mktemp -d)
gcc -O3 -DTWO_LEVEL_TREE -Dmain=lkh_unused_test_main -I$SRC/INCLUDE -c $SRC/LKHmain.c -o $TMP/LKHmain.o
gcc -O3 -DTWO_LEVEL_TREE -I$SRC/INCLUDE $FILES $TMP/LKHmain.o $HERE/main_atsp.c -o $OUT -lm
rm -rf $TMP
echo built $OUT
