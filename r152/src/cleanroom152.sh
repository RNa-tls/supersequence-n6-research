#!/bin/bash
# Round 152 -- clean reproduction of the capacity certification.
#
# Rebuilds both checkers from committed source and reverifies the certificate.
# Nothing from the development workspace is used: every executable is deleted
# and rebuilt first.  The certificate itself is an input (that is the point --
# it is what a third party would be handed), and both checkers re-establish
# every value in it independently.
#
# usage: cleanroom152.sh [cert.txt] [node_cap]
set -u
cd "$(dirname "$0")/../.." || exit 2
CERT=${1:-r152/certs/cap_cert_pilot_152.txt}
NODECAP=${2:-200000000}
echo "== environment"
echo "commit:   $(git rev-parse HEAD)"
echo "branch:   $(git rev-parse --abbrev-ref HEAD)"
echo "dirty:    $(git status --porcelain | wc -l) files"
echo "compiler: $(cc --version | head -1)"
echo "python:   $(python3 --version)"
echo "os:       $(uname -sro)"
echo "cert:     $CERT  ($(sha256sum "$CERT" | cut -c1-16)...)"
echo "node cap: $NODECAP"
echo
echo "== deleting round-152 executables and rebuilding from source"
rm -f r152/src/*.exe
cc -O2 -o r152/src/checker152.exe  r152/src/checker152.c  || exit 2
cc -O2 -o r152/src/producer152.exe r152/src/producer152.c || exit 2
sha256sum r152/src/*.exe r152/src/checker152.c r152/src/checker152.py
echo
fail=0
step () { echo "== $1"; shift; "$@"; rc=$?; echo "   -> exit $rc"; [ $rc -ne 0 ] && fail=1; echo; }

step "C checker"      bash -c "./r152/src/checker152.exe '$CERT' $NODECAP | tail -1"
step "Python checker" python3 r152/src/checker152.py --cert "$CERT" --node-cap "$NODECAP" \
                              --report /tmp/r152_clean_py.json
step "the two checkers agree cell by cell" python3 r152/src/agree152.py \
                              --cert "$CERT" --node-cap "$NODECAP"
step "mutation tests"  python3 r152/src/mutate152.py --cert "$CERT" \
                              --node-cap "$NODECAP" --report /tmp/r152_clean_mut.json
step "provenance"      python3 r152/src/provenance152.py

echo "=============================================="
[ $fail -eq 0 ] && echo "CLEAN REPRODUCTION OK" || echo "CLEAN REPRODUCTION FAILED"
exit $fail
