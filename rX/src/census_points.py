#!/usr/bin/env python3
"""Round X -- extract the census points (number of pieces r, value v) of the kept chains of one line search from a
Round W per-piece census file (rW/certs/lower_bound/census_by_pieces_line_*.json: for every r the set of values
a r - b d of the kept chains with r pieces, as five 64-bit hex words, bit v of word v/64).
Writes one line per r with a nonempty set:  r v_1 v_2 ...      usage: census_points.py CENSUS.json OUT.txt"""
import sys, json
L = open(sys.argv[1]).read().strip().split("\n"); h = json.loads(L[0]); b = json.loads(L[1])
a, bb, c = h["params"]; vb = b["values_by_pieces"]; out = []
for r in sorted(vb, key=int):
    words = [int(x, 16) for x in vb[r]]; vals = [w * 64 + i for w in range(len(words)) for i in range(64) if words[w] >> i & 1]
    if not vals: continue
    for v in vals: assert 0 < v <= c and (a * int(r) - v) % bb == 0, (r, v)
    out.append("%s %s\n" % (r, " ".join(map(str, vals))))
open(sys.argv[2], "w").write("# line %d %d %d greatest_number_of_pieces %d\n" % (a, bb, c, int(h["greatest_number_of_pieces"])) + "".join(out))
print(len(out), "piece counts with kept chains; max r", max(int(l.split()[0]) for l in out), "points", sum(len(l.split()) - 1 for l in out))
