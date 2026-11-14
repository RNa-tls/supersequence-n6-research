#!/usr/bin/env python3
"""Round Z -- split the output of rZ/csrc/fpdump.c into one first-passage list per threshold, in the input format of
the disjoint-placement tools:  name nb entry_1 .. entry_nb   (name = F<theta>v<v>_r<r>_d<d>_<index>), and a summary.
usage: fp_split.py FPDUMP_OUTPUT OUTDIR PREFIX"""
import sys, os, collections, hashlib, json
src, outdir, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
files = {}; counts = collections.Counter(); summary = None; idx = collections.Counter()
for line in open(src):
    if line.startswith('S '):
        summary = line.strip(); continue
    if not line.startswith('F '):
        continue
    head, ents = line.split('|')
    h = head.split(); thetas = [int(t) for t in h[1].split(',')]; r, d, v = int(h[2]), int(h[3]), int(h[4])
    pieces = [int(x) for x in h[5:]]; ents = ents.split()
    assert len(pieces) == r and sum(pieces) == len(ents) and d == sum(7 - p for p in pieces)
    for t in thetas:
        if t not in files:
            files[t] = open(os.path.join(outdir, '%s_fp%d.txt' % (prefix, t)), 'w')
        name = 'F%dv%d_r%d_d%d_%d' % (t, v, r, d, idx[t]); idx[t] += 1
        files[t].write('%s %d %s\n' % (name, len(ents), ' '.join(ents)))
        counts[t] += 1
for f in files.values():
    f.close()
print(summary)
print(dict(sorted(counts.items())))
