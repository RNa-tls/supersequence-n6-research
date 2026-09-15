#!/bin/bash
# Round 152 -- clean reproduction of the capacity certification.
#
# Deletes every round-152 executable, rebuilds from committed source, and
# reruns the whole verification.  The certificates are inputs -- that is the
# point: they are what a third party would be handed -- and both checkers of
# each kind re-establish every value in them independently.
#
# The two full runs (1,101 chain cells, 220 piece cells) take hours and are NOT
# rerun here; this script reruns the fast, load-bearing part and rechecks the
# stored reports.  Use r152/REPRODUCE.md for the full runs.
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
cc -O2 -o r152/src/piece152.exe    r152/src/piece152.c    || exit 2
cc -O2 -o r152/src/extree152.exe   r152/src/extree152.c   || exit 2
sha256sum r152/src/*.exe r152/src/*.c r152/src/*.py | sed 's|r152/src/||'
echo
fail=0
step () { echo "== $1"; shift; "$@"; rc=$?; echo "   -> exit $rc"; [ $rc -ne 0 ] && fail=1; echo; }

step "catalogue invariants I1-I6"        python3 r152/src/invariants152.py
step "catalogue cross-check vs round 147" python3 r152/src/catcheck152.py
step "C checker on the pilot"            bash -c "./r152/src/checker152.exe '$CERT' $NODECAP | tail -1"
step "Python checker on the pilot"       python3 r152/src/checker152.py --cert "$CERT" \
                                            --node-cap "$NODECAP" --report /tmp/r152_clean_py.json
step "the two chain checkers agree"      python3 r152/src/agree152.py --cert "$CERT" \
                                            --node-cap "$NODECAP" --out /tmp/r152_clean_agree.json
step "explicit exhaustion tree"          python3 r152/src/extree152.py \
                                            --tree r152/certs/extree_pilot_152.txt \
                                            --cert r152/certs/cap_cert_pilot_152.txt \
                                            --report /tmp/r152_clean_tree.json
step "the two piece checkers agree"      python3 r152/src/agree152.py --kind piece \
                                            --cert r152/certs/pcert_pysubset_152.txt \
                                            --node-cap 20000000 --out /tmp/r152_clean_pagree.json
step "chain certificate mutations"       python3 r152/src/mutate152.py \
                                            --node-cap "$NODECAP" --report /tmp/r152_clean_mut.json
step "piece certificate mutations"       python3 r152/src/pmutate152.py \
                                            --node-cap "$NODECAP" --report /tmp/r152_clean_pmut.json
step "exhaustion-tree mutations"         python3 r152/src/mutextree152.py \
                                            --report /tmp/r152_clean_tmut.json
step "pipeline hygiene"                  python3 r152/src/hygiene152.py
step "equality row provenance"           python3 r152/src/equality152.py
step "capacity-layer DAG"                python3 r152/src/dag152.py
step "provenance hashes"                 python3 r152/src/provenance152.py

echo "=============================================="
[ $fail -eq 0 ] && echo "CLEAN REPRODUCTION OK" || echo "CLEAN REPRODUCTION FAILED"
exit $fail
