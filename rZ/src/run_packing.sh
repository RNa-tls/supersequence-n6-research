#!/bin/sh
# Round Z -- the kappa(46) packing knapsack of Round X (rX/src/frontier_packing.py) with the line-2 exceptional-chain
# tables at threshold TH2 (TH2 = 230 reproduces Round X's 40 cells).  usage: run_packing.sh TABDIR TH2 OUT.json
set -e
T=$1; TH=$2; OUT=$3; C=rX/certs/lower_bound
if [ "$TH" = "230" ]; then N=$C/twosided_feasible_line_17_38_264_truncated_below_230.txt; X=$C/twosided_feasible_line_17_38_264_exceptional_caseB_230.txt
else N=$T/ts2_lt$TH.txt; X=$T/ts2_full_th$TH.txt; fi
python3 -I rX/src/frontier_packing.py $C/twosided_feasible_line1_ts1_lt46.txt $C/twosided_feasible_line1_ts1_lt50_th46.txt \
  $C/twosided_feasible_line1_ts1_full_th46.txt $C/twosided_feasible_line_4_9_56_truncated_below_50.txt \
  $C/twosided_feasible_line_4_9_56_exceptional_caseB_50.txt $N $X rW/certs/lower_bound/frontier_46135_knapsack.json $OUT
