#!/bin/bash
# Round V -- letter-level exact path optimum of two-wrap families (both wraps used, class-inside cuts allowed, one piece
# per trail of the 18-trail family), by the layered DP rV/csrc/path_layer.c.
# usage: run_letters2.sh WORKU WORKV OUT.jsonl C1,C2 ...   (resumable: pairs already in OUT are skipped)
WU=$1; WV=$2; OUT=$3; shift 3; HERE=$(cd "$(dirname "$0")" && pwd); X=$HERE/../../rT/external/tholsh_46173
for p in "$@"; do
  c1=${p%,*}; c2=${p#*,}
  grep -q "^{\"pair\": \[$c1, $c2\]," $OUT 2>/dev/null && continue
  A=$(python3 -I $HERE/fam_letters2.py $X/selection.txt $X/base.tsv $X/base.txt $WU $c1 $c2 $WV/letters2_run.txt) || exit 1
  R=$($WV/path_layer $WV/letters2_run.txt 24) || exit 1
  echo "{\"pair\": [$c1, $c2], \"arcs\": $A, \"letter_level\": $R}" >> $OUT
done
