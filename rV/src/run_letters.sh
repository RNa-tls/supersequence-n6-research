#!/bin/bash
# Round V -- letter-level exact path optimum of one-wrap families (wrap + class-inside cuts, one piece per trail of F_C).
# usage: run_letters.sh WORKU WORKV OUT.jsonl CHAIN...   (resumable: chains already in OUT are skipped)
WU=$1; WV=$2; OUT=$3; shift 3; HERE=$(cd "$(dirname "$0")" && pwd); X=$HERE/../../rT/external/tholsh_46173
for c in "$@"; do
  grep -q "^{\"chain\": $c," $OUT 2>/dev/null && continue
  A=$(python3 -I $HERE/fam_letters.py $X/selection.txt $X/base.tsv $X/base.txt $WU $c $WV/letters_run.txt) || exit 1
  $WV/path_witness_big $WV/letters_run.txt $WV/letters_run.json > /dev/null || exit 1
  J=$(python3 -c "import json; print(json.load(open('$WV/letters_run.json'))['optimal_J'])")
  echo "{\"chain\": $c, \"arcs\": $A, \"letter_level_optimal_J\": $J}" >> $OUT
done
