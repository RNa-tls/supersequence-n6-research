#!/bin/bash
# Round V -- second implementation check of the letter-level one-wrap optima: the arcs of each listed family are rebuilt
# (fam_letters.py) and the optimum is recomputed by the layered DP rV/csrc/path_layer.c (written separately from
# path_witness.c); the value is compared with the one in REF.jsonl (run_letters.sh output).
# usage: check_letters_layer.sh WORKU WORKV REF.jsonl OUT.jsonl CHAIN...
WU=$1; WV=$2; REF=$3; OUT=$4; shift 4; HERE=$(cd "$(dirname "$0")" && pwd); X=$HERE/../../rT/external/tholsh_46173
for c in "$@"; do
  grep -q "^{\"chain\": $c," $OUT 2>/dev/null && continue
  python3 -I $HERE/fam_letters.py $X/selection.txt $X/base.tsv $X/base.txt $WU $c $WV/check_layer_arcs.txt > /dev/null || exit 1
  R=$($WV/path_layer $WV/check_layer_arcs.txt) || exit 1
  V=$(grep "^{\"chain\": $c," $REF | python3 -c "import sys, json; print(json.loads(sys.stdin.readline())['letter_level_optimal_J'])")
  L=$(echo "$R" | python3 -c "import sys, json; print(json.loads(sys.stdin.readline())['optimal_J'])")
  echo "{\"chain\": $c, \"path_witness\": $V, \"path_layer\": $L, \"agree\": $([ "$V" = "$L" ] && echo true || echo false)}" >> $OUT
done
