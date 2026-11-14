#!/usr/bin/env python3
"""Round Z -- profile of first-passage lists: rows (maximal door runs), moving symbol of every row, label changes,
seam types, row sizes.  usage: fp_profile.py LIST [LIST ...]"""
import sys, collections
def exc(c): return ((c & 15) << 28) | (c >> 4)
def door(x): return ((x & 0xFFFFFF) << 8) | (((x >> 24) & 15) << 4) | (x >> 28)
def seamtype(y, e):
    # y = exit z v1 v2 y4..y8, e = y4..y8 + pi(z v1 v2)
    a, b, c = y >> 28, (y >> 24) & 15, (y >> 20) & 15
    t = (e >> 0) & 0xFFF; t = ((e >> 8) & 15, (e >> 4) & 15, e & 15)
    return {(a, c, b): 'c', (b, a, c): 'b', (b, c, a): 'e', (c, a, b): 'f', (c, b, a): 'd'}.get(t, '?')
for path in sys.argv[1:]:
    nlab = collections.Counter(); nsyms = collections.Counter(); seams = collections.Counter(); sizes = collections.Counter(); n = 0
    vmax_by_lab = {}
    for line in open(path):
        t = line.split(); name = t[0]; ents = [int(x, 16) for x in t[2:]]
        v = int(name.split('v')[1].split('_')[0])
        rows = []
        for q, e in enumerate(ents):
            if q > 0 and e == door(exc(ents[q - 1])): rows[-1].append(e)
            else: rows.append([e])
        zs = [r[0] & 15 for r in rows]
        lab = 0
        for i in range(len(rows) - 1):
            y = exc(rows[i][-1]); st = seamtype(y, rows[i + 1][0]); seams[st] += 1
            if st in 'bcf': lab += 1
        nlab[lab] += 1; nsyms[len(set(zs))] += 1; n += 1
        for r in rows: sizes[len(r)] += 1
        vmax_by_lab[lab] = max(vmax_by_lab.get(lab, -1), v)
    print(path.split('/')[-1], 'chains', n, 'label_changes', dict(sorted(nlab.items())), 'symbols_used', dict(sorted(nsyms.items())),
          'seams', dict(sorted(seams.items())), 'row_sizes', dict(sorted(sizes.items())), 'max_value_by_label_changes', dict(sorted(vmax_by_lab.items())))
