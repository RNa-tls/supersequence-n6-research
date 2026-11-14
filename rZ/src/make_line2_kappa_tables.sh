#!/bin/sh
# Round Z -- two-level line-2 tables for kappa2(LO) <= 2 together with the exceptional-chain lemma at HI (LO < HI):
#   U0  = ts2_ltLO.txt          census < LO                                  (no primitive part >= LO)
#   U1  = ts2_ltHI_thLO.txt     census < HI, Case B with both ends >= LO excluded   (one part >= LO, none >= HI)
#   U1e = ts2_full_thLO.txt     full census, Case B with both ends >= LO excluded   (the exceptional chain, one part)
#   U2  = ts2_ltHI.txt          census < HI                                  (two parts >= LO, none >= HI)
#   U2e = ts2_full_thHI.txt     full census, Case B with both ends >= HI excluded   (the exceptional chain, two parts)
# usage: make_line2_kappa_tables.sh TWOSIDED_BINARY LO HI OUTDIR
set -e
TS=$1; LO=$2; HI=$3; OUT=$4
P=rX/certs/lower_bound/census_points_line_17_38_264.txt
for th in $LO $HI; do
  awk -v th=$th '/^#/ {print; next} {printf "%s", $1; for (i = 2; i <= NF; i++) if ($i < th) printf " %s", $i; printf "\n"}' $P > $OUT/pts2_lt$th.txt
done
$TS $OUT/pts2_lt$LO.txt 800 4 > $OUT/ts2_lt$LO.txt
$TS $OUT/pts2_lt$HI.txt 800 4 $LO > $OUT/ts2_lt${HI}_th$LO.txt
$TS $P 800 4 $LO > $OUT/ts2_full_th$LO.txt
$TS $OUT/pts2_lt$HI.txt 800 4 > $OUT/ts2_lt$HI.txt
$TS $P 800 4 $HI > $OUT/ts2_full_th$HI.txt
