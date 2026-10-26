#!/bin/bash
# planted mutation test, full pipeline at THR 19 (the full THR-20 mutated search did not fit the 2-hour limit):
# the mutated tables put both planted configurations at G = 19, so the symmetry-reduced search + exact evaluation
# with the mutation must report min G = 19 and return the planted orbits.
source /tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/env.sh
M=$SP/mut
(time CKB_MUT=$M/planted2.txt $SP/rR/ckM2_search2 $SP/ckB $SP/ckB/out $M/tab 19 $M/full19.json) > $M/full19.log 2>&1
tail -4 $M/full19.log
cat $M/full19.json.patterns.* > $M/full19.pat; echo "mutated patterns: $(wc -l < $M/full19.pat)"
CKB_MUT=$M/planted2.txt OMP_NUM_THREADS=4 $SP/rR/ckM_eval7 $SP/ckB $M/full19.pat 19 $M/full19_eval.json $M/full19_wit.jsonl > /dev/null 2> $M/full19_eval.err
echo "mutated full evaluation: $(cat $M/full19_eval.json)"
echo "MUT19 DONE"
