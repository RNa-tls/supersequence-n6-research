#!/bin/bash
# Round 153 Phase 13 -- clean verification of L6 = 872.
#
# Rebuilds every executable from committed source and reruns the whole
# verification chain.  The multi-hour capacity SEARCHES are not rerun: round
# 152's capacity certificates are inputs here, and what is checked is that they
# are complete, carry no UNKNOWN_CAP or DISAGREE, and that the two equality
# cells they certify are the ones the equality layer is attached to.
set -u
cd "$(dirname "$0")/../.." || exit 2
echo "== environment"
echo "commit:   $(git rev-parse HEAD)"
echo "branch:   $(git rev-parse --abbrev-ref HEAD)"
echo "dirty:    $(git status --porcelain | wc -l) files"
echo "compiler: $(cc --version | head -1)"
echo "python:   $(python3 --version)"
echo
echo "== deleting round-152/153 executables and rebuilding from source"
rm -f r152/src/*.exe r153/src/*.exe
cc -O2 -o r152/src/checker152.exe r152/src/checker152.c || exit 2
cc -O2 -o r152/src/piece152.exe   r152/src/piece152.c   || exit 2
cc -O2 -o r153/src/eqwit153.exe   r153/src/eqwit153.c   || exit 2
sha256sum r152/src/*.exe r153/src/*.exe | sed 's|.*/||'
echo
fail=0
step () { echo "== $1"; shift; "$@"; rc=$?; echo "   -> exit $rc"; [ $rc -ne 0 ] && fail=1; echo; }

step "1a round-152 capacity certificates, not regenerated" python3 - <<'PY'
import json, sys
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
ok = True
for f, n in (("r152/certs/verify_all_c152.json", 1101),
             ("r152/certs/verify_piece_c152.json", 220)):
    d = json.load(open(f))
    bad = [r["cell"] for r in d["rows"] if r["status"] not in GOOD]
    print(f"   {f}: {len(d['rows'])}/{n} cells, {len(bad)} not certified")
    ok &= len(d["rows"]) == n and not bad
for cell, cap in (("0|14|0|0|0|0", 96), ("0|8|0|0|0|1", 92)):
    r = next(x for x in json.load(open("r152/certs/verify_all_c152.json"))["rows"]
             if x["cell"] == cell)
    print(f"   {cell}: cap={r['cap']} status={r['status']}")
    ok &= r["cap"] == cap and r["status"] == "EXACT_CERTIFIED"
sys.exit(0 if ok else 1)
PY
step "1b the round-152 capacity DAG"          python3 r152/src/dag152.py
step "2  re-enumerate the equality witnesses" bash -c '
  ./r153/src/eqwit153.exe 0 14 0 0 0 0 96 /tmp/r153_E1.jsonl --table r153/certs/prune_certified_153.txt 200000000000 &&
  ./r153/src/eqwit153.exe 0 8 0 0 0 1 92 /tmp/r153_E2.jsonl --table r153/certs/prune_certified_153.txt 200000000000 &&
  cmp /tmp/r153_E1.jsonl r153/certs/E1_table.jsonl &&
  cmp /tmp/r153_E2.jsonl r153/certs/E2_table.jsonl'
step "2b all five enumeration routes agree"   python3 r153/src/eqcompare153.py
step "3  coexistence exclusion trees"         python3 r153/src/covertree153.py validate --tree r153/certs/covertree_153.txt
step "3b coexistence solvers and controls"    python3 r153/src/coexist153.py
step "4  the explicit length-872 cover"       python3 r153/src/witness872_153.py
step "5  certified-only row census"           python3 r152/src/rows152.py \
        --verify r152/certs/verify_all_c152.json \
        --verify-piece r152/certs/verify_piece_c152.json --layers 0 1 2 3 4 \
        --out /tmp/r153_census.json
step "6  adversarial trace"                   python3 r153/src/adversarial153.py
step "6b integrated certified-only theorem"   python3 r153/src/theorem153.py
step "6c final DAG"                           python3 r153/src/dag153.py
step "7  mutation tests"                      python3 r153/src/mutate153.py
step "8  provenance hashes"                   python3 r153/src/provenance153.py

echo "=============================================="
[ $fail -eq 0 ] && echo "CLEAN VERIFICATION OK: L6 = 872" || echo "CLEAN VERIFICATION FAILED"
exit $fail
