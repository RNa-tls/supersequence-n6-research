#!/bin/sh
# Round Z -- line-1 packing tables for kappa1(K) <= 2 with the line-1 exceptional-chain lemma at E1 (K < E1):
#   T0 = ts1_ltK.txt, T1 = ts1_ltE1_thK.txt, T1e = ts1_full_thK.txt, T2 = ts1_ltE1.txt, T2e = ts1_full_thE1.txt
# (E1 = 50 is Round X's exceptional chain).  usage: make_line1_tables_e.sh TWOSIDED K E1 OUTDIR
set -e
TS=$1; K=$2; E1=$3; OUT=$4
P=rX/certs/lower_bound/census_points_line_4_9_56.txt
for th in $K $E1; do
  awk -v th=$th '/^#/ {print; next} {printf "%s", $1; for (i = 2; i <= NF; i++) if ($i < th) printf " %s", $i; printf "\n"}' $P > $OUT/pts1_lt$th.txt
done
$TS $OUT/pts1_lt$K.txt 800 4 > $OUT/ts1_lt$K.txt
$TS $OUT/pts1_lt$E1.txt 800 4 $K > $OUT/ts1_lt${E1}_th$K.txt
$TS $P 800 4 $K > $OUT/ts1_full_th$K.txt
$TS $OUT/pts1_lt$E1.txt 800 4 > $OUT/ts1_lt$E1.txt
$TS $P 800 4 $E1 > $OUT/ts1_full_th$E1.txt
