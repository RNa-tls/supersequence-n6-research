#!/bin/bash
# Round U -- one-wrap families: for every orbit representative chain, the fact checks and the bracket-tree bound.
# usage: run_families.sh WORK FROM TO   (indices into the representative list of WORK/chains.json); appends to WORK/fam_results.jsonl
WORK=$1; FROM=$2; TO=$3; HERE=$(cd "$(dirname "$0")" && pwd); X=$HERE/../../rT/external/tholsh_46173
REPS=$(python3 -I -c "import json,sys; print(' '.join(str(r['chain']) for r in json.load(open(sys.argv[1]))['representatives'][int(sys.argv[2]):int(sys.argv[3])]))" $WORK/chains.json $FROM $TO)
for c in $REPS; do
  if grep -q "^{\"chain\": $c," $WORK/fam_results.jsonl 2>/dev/null; then continue; fi
  F=$(python3 -I $HERE/wrapfam.py fam $X/selection.txt $X/base.tsv $X/base.txt $WORK $c $WORK/fam_$FROM.txt) || exit 1
  B=$($WORK/wrap_tree $WORK/fam_$FROM.txt) || exit 1
  echo "{\"chain\": $c, \"facts\": $F, \"bound\": $B}" >> $WORK/fam_results.jsonl
done
