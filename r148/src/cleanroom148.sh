#!/bin/bash
# Round 148 Phase 4 -- CLEAN CHECKOUT reproduction.
# Rebuilds every executable from committed source and reruns the whole
# certification.  No file from the development workspace is used.
set -u
cd "$(dirname "$0")/../.." || exit 2
ROOT=$PWD
echo "== environment"
echo "commit:        $(git rev-parse HEAD)"
echo "branch:        $(git rev-parse --abbrev-ref HEAD)"
echo "dirty:         $(git status --porcelain | wc -l) files"
echo "compiler:      $(gcc --version | head -1)"
echo "flags:         -O2 -Wall -Wextra"
echo "python:        $(python3 --version)"
echo "os:            $(uname -sro)"
echo "cpus:          $(nproc)"
echo
echo "== deleting every inherited executable, then rebuilding from source"
find . -name '*.exe' -print -delete
gcc -O2 -Wall -Wextra -o r147/l6chain147b.exe r147/src/l6_chain_capacity_147.c || exit 2
gcc -O2 -Wall -Wextra -o r147/chain2_147.exe  r147/src/chain2_147.c          || exit 2
gcc -O2 -Wall          -o r147/l6catdump147.exe r147/src/l6_catalogue_dump_147.c 2>/dev/null
cp r147/l6chain147b.exe r147/l6chain147.exe   # the fail-closed tests drive this name
gcc -O2 -o outputs/l6cap_p_144.exe src/l6_marked_capacity_pruned_144.c 2>/dev/null
gcc -O2 -o outputs/l6cap_144.exe   src/l6_marked_capacity_144.c        2>/dev/null
gcc -O2 -o outputs/l6chain_144.exe src/l6_chain_capacity_144.c         2>/dev/null
echo "rebuilt hashes:"; sha256sum r147/*.exe
echo
fail=0
step () { echo "== $1"; shift; "$@"; rc=$?; echo "   -> exit $rc"; [ $rc -ne 0 ] && fail=1; echo; }
step "catalogue reconstruction"          python3 r147/src/catalogue147.py
step "regenerate the C header and diff"  bash -c 'cp r147/src/catalogue147.h /tmp/h.$$ && python3 r147/src/genheader147.py >/dev/null && diff -q /tmp/h.$$ r147/src/catalogue147.h'
step "fail-closed table loader"          python3 r147/src/failclosed147.py
step "monotonicity of the cell table"    python3 r147/src/monotone147.py
step "rows from definitions (r147)"      python3 r147/src/rows147.py
step "constructed solver controls"       python3 r148/src/synthetic_control148.py 40
step "fresh L=870 / L=871 census"        python3 r148/src/rows148.py 3 4
step "equality witnesses + coexistence"  python3 r148/src/witness148.py
step "MASTER VERIFIER"                   python3 r148/src/verifier148.py
step "final proof DAG"                   python3 r148/src/dag148.py
step "regression suite"                  python3 tests/test_l6_endgame_144.py
echo "=============================================="
[ $fail -eq 0 ] && echo "CLEAN CHECKOUT REPRODUCED THE VERDICT" || echo "CLEAN CHECKOUT FAILED"
exit $fail
