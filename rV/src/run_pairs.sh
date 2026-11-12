#!/bin/bash
# Round V -- two-wrap families: for the pair (C1, C2): arcs and fact checks (wrapfam2.py), exact best path (path_witness),
# and with MODE=tree the bracket-tree bound (wrap_tree).  usage: run_pairs.sh WORKU WORKV C1 C2 MODE  -> one JSON line
WU=$1; WV=$2; A=$3; B=$4; MODE=$5; HERE=$(cd "$(dirname "$0")" && pwd); X=$HERE/../../rT/external/tholsh_46173
F=$(python3 -I $HERE/wrapfam2.py $X/selection.txt $X/base.tsv $X/base.txt $WU $A $B $WV/pair_${A}_${B}.txt) || exit 1
if [ "$MODE" = "tree" ]; then R=$($WU/wrap_tree $WV/pair_${A}_${B}.txt) || exit 1; echo "{\"pair\": [$A, $B], \"facts\": $F, \"tree\": $R}"
else $WV/path_witness $WV/pair_${A}_${B}.txt $WV/pair_${A}_${B}.json > /dev/null || exit 1; echo "{\"pair\": [$A, $B], \"facts\": $F, \"path\": $(cat $WV/pair_${A}_${B}.json | tr '\n' ' ')}"; fi
rm -f $WV/pair_${A}_${B}.txt $WV/pair_${A}_${B}.json
