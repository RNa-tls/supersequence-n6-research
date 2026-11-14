#!/bin/sh
# Round Z -- two-sided feasibility tables for the line-1 packing lemma kappa1(TH) <= 2 (reproducible):
#   ts1_ltTH.txt       census truncated below TH                        (T0: no primitive part of value >= TH)
#   ts1_lt50_thTH.txt  census truncated below 50, Case B with both ends >= TH excluded   (T1)
#   ts1_full_thTH.txt  full census, Case B with both ends >= TH excluded                  (T1e)
# (T2 = truncated below 50 and T2e = full with Case B >= 50 excluded are Round X's tables.)
# usage: make_line1_tables.sh TWOSIDED_BINARY TH OUTDIR
set -e
TS=$1; TH=$2; OUT=$3
P=rX/certs/lower_bound/census_points_line_4_9_56.txt
awk -v th=$TH '/^#/ {print; next} {printf "%s", $1; for (i = 2; i <= NF; i++) if ($i < th) printf " %s", $i; printf "\n"}' $P > $OUT/pts1_lt$TH.txt
awk '/^#/ {print; next} {printf "%s", $1; for (i = 2; i <= NF; i++) if ($i < 50) printf " %s", $i; printf "\n"}' $P > $OUT/pts1_lt50.txt
$TS $OUT/pts1_lt$TH.txt 800 4 > $OUT/ts1_lt$TH.txt
$TS $OUT/pts1_lt50.txt 800 4 $TH > $OUT/ts1_lt50_th$TH.txt
$TS $P 800 4 $TH > $OUT/ts1_full_th$TH.txt
