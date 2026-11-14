#!/bin/sh
# Round Z -- the packing knapsack of Round X (rX/src/frontier_packing.py) with the line-1 packing tables at TH1
# (kappa1(TH1) <= 2; TH1 = 46 is Round X) and the line-2 exceptional-chain tables at TH2 (TH2 = 230 is Round X).
# usage: run_packing.sh TABDIR TH1 TH2 OUT.json
set -e
T=$1; TH1=$2; TH2=$3; OUT=$4; C=rX/certs/lower_bound
if [ "$TH1" = "46" ]; then A=$C/twosided_feasible_line1_ts1_lt46.txt; B=$C/twosided_feasible_line1_ts1_lt50_th46.txt; Be=$C/twosided_feasible_line1_ts1_full_th46.txt
else A=$T/ts1_lt$TH1.txt; B=$T/ts1_lt50_th$TH1.txt; Be=$T/ts1_full_th$TH1.txt; fi
if [ "$TH2" = "230" ]; then N=$C/twosided_feasible_line_17_38_264_truncated_below_230.txt; X=$C/twosided_feasible_line_17_38_264_exceptional_caseB_230.txt
else N=$T/ts2_lt$TH2.txt; X=$T/ts2_full_th$TH2.txt; fi
python3 -I rX/src/frontier_packing.py $A $B $Be $C/twosided_feasible_line_4_9_56_truncated_below_50.txt \
  $C/twosided_feasible_line_4_9_56_exceptional_caseB_50.txt $N $X rW/certs/lower_bound/frontier_46135_knapsack.json $OUT
