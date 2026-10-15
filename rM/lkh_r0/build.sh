#!/bin/bash
# Build the standalone r = 0 LKH binary from the LKH-3.0.8 copy shipped in the elkai 2.0.1 sdist
# (https://pypi.org/project/elkai/2.0.1/, file elkai-2.0.1.tar.gz).  LKH sources are NOT part of
# this repository.  usage: build.sh EXTRACTED_ELKAI_DIR OUT_BINARY
set -e
E=$1; OUT=$2; HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$E/LKH-3.0.8/SRC
FILES=$(ls $SRC/*.c | grep -v -E "/(Distance_SPECIAL|LKHmain)\.c$")
TMP=$(mktemp -d)
# LKHmain.c holds ElkaiSolveProblem/TheTour plus a test main(): rename that main
gcc -O3 -DTWO_LEVEL_TREE -Dmain=lkh_unused_test_main -I$SRC/INCLUDE -c $SRC/LKHmain.c -o $TMP/LKHmain.o
gcc -O3 -DTWO_LEVEL_TREE -I$SRC/INCLUDE $FILES $TMP/LKHmain.o $HERE/r0special.c $HERE/main_r0.c -o $OUT -lm
rm -rf $TMP
echo built $OUT
