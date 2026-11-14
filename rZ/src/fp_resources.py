#!/usr/bin/env python3
"""Round Z -- 2-cycle resources of first-passage chains (exact): rows, used 2-cycles (and repeats), 5-rows (hole pairs).
usage: fp_resources.py LIST"""
import sys, collections
def exc(c): return ((c & 15) << 28) | (c >> 4)
def door(x): return ((x & 0xFFFFFF) << 8) | (((x >> 24) & 15) << 4) | (x >> 28)
def digits(e): return [(e >> (4 * (7 - i))) & 15 for i in range(8)]
def canon(t): k = t.index(min(t)); return tuple(t[k:] + t[:k])
stat = collections.Counter(); rel = collections.Counter(); nrows = []; n5 = []; reps = 0; n = 0
for l in open(sys.argv[1]):
    t = l.split(); ents = [int(x, 16) for x in t[2:]]; n += 1
    rows = []
    for q, e in enumerate(ents):
        if q > 0 and e == door(exc(ents[q - 1])): rows[-1].append(e)
        else: rows.append([e])
    G = [canon(digits(r[0])[:7]) + (digits(r[0])[7],) for r in rows]
    reps += len(G) - len(set(G)); nrows.append(len(rows)); n5.append(sum(1 for r in rows if len(r) == 5))
print(dict(chains=n, rows_min=min(nrows), rows_max=max(nrows), rows_mean=round(sum(nrows) / n, 1), five_rows_mean=round(sum(n5) / n, 1),
           five_per_row=round(sum(n5) / sum(nrows), 4), repeated_2cycles=reps))
