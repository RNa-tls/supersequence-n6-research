#!/bin/bash
# usage: run_subtrees.sh WORD T TOPCERT WORKER_INDEX NWORKERS TLIMIT_PER_SUBTREE
WORD=$1; T=$2; TOP=$3; W=$4; NW=$5; TL=$6
PY=/tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/venv/bin/python
BASE=${TOP%.json}
i=0
$PY -c "import json; [print(f['id'], json.dumps(f['fix']).replace(' ','')) for f in json.load(open('$TOP.frontier.json'))['frontier']]" | while read id fx; do
  if [ $((i % NW)) -eq $W ]; then
    if [ ! -f ${BASE}_sub_${id}.json ]; then
      INIT_FIX="$fx" GLOBAL_FIX0=$TOP INIT_POOL=$TOP timeout $((TL + 600)) $PY -I rJ/src/chainset_bc.py $WORD $T ${BASE}_sub_${id}.json $TL > ${BASE}_sub_${id}.stdout 2>&1
    fi
  fi
  i=$((i + 1))
done
