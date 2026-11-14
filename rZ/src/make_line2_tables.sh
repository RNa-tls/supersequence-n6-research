#!/bin/sh
# Round Z -- two-sided feasibility tables for the line-2 exceptional-chain lemma at threshold TH (reproducible):
#   pts2_ltTH.txt     census points of line 2 with values < TH   (chains with no primitive part of value >= TH)
#   ts2_ltTH.txt      twosided on them                            (table N: every chain but the exceptional one)
#   ts2_full_thTH.txt twosided on the full census, Case B with u1, u2 >= TH excluded   (table X: the exceptional chain)
# usage: make_line2_tables.sh TWOSIDED_BINARY TH OUTDIR
set -e
TS=$1; TH=$2; OUT=$3
P=rX/certs/lower_bound/census_points_line_17_38_264.txt
awk -v th=$TH '/^#/ {print; next} {printf "%s", $1; for (i = 2; i <= NF; i++) if ($i < th) printf " %s", $i; printf "\n"}' $P > $OUT/pts2_lt$TH.txt
$TS $OUT/pts2_lt$TH.txt 800 4 > $OUT/ts2_lt$TH.txt
$TS $P 800 4 $TH > $OUT/ts2_full_th$TH.txt
