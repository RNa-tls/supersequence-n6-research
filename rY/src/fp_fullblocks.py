#!/usr/bin/env python3
"""Round Y -- full-row block counts of single-label chains (input: chain lists "name nb entry ...", all anchored at the
moving symbol 8).  For each s in 1..7, F[s] = number of {8,s}-blocks (cyclic orders of the six symbols other than 8, s)
that contain the group of at least one FULL row (7 blocks) of the chain.  Output: name H F[1..7] nrows nfull.
Full-full lemma: if X (label 8) and g(Y) (label g(8) = s != 8) are class-disjoint, no {8,s}-block contains a full row
of both (a full row covers its whole group, and a label-8 group and a label-s group of one block always meet), hence
F_X[s] + F_Y[y] <= 120 with y = g^-1(8).  So X, Y have no disjoint placement with a change of label when
min_s F_X[s] + min_y F_Y[y] > 120.
usage: fp_fullblocks.py CHAINS.txt[.gz] OUT.txt"""
import sys, gzip, collections
def door(e): return e[1:7] + e[0] + e[7]
def cls(w):
    i = w.index('8'); return w[i:] + w[:i]
def canon_cyc(seq):
    j = seq.index(min(seq)); return seq[j:] + seq[:j]
def main():
    f = gzip.open(sys.argv[1], 'rt') if sys.argv[1].endswith('.gz') else open(sys.argv[1])
    out = open(sys.argv[2], 'w'); n = 0; bad = 0
    for line in f:
        t = line.split()
        if len(t) < 3: continue
        name, nb, E = t[0], int(t[1]), t[2:]
        rows = []; cur = [E[0]]
        for a, b in zip(E, E[1:]):
            if b == door(a): cur.append(b)
            else: rows.append(cur); cur = [b]
        rows.append(cur)
        if any(r[0][-1] != '8' for r in rows): bad += 1; continue
        groups = collections.defaultdict(set); full = []
        for r in rows:
            C = canon_cyc(cls(r[0])[1:])
            for e in r: groups[C].add(cls(e))
            if len(r) == 7: full.append(C)
        H = sum(7 - len(v) for v in groups.values())
        Fs = [len({canon_cyc(C.replace(s, '')) for C in full}) for s in '1234567']
        out.write(f"{name} {H} {' '.join(map(str, Fs))} {len(rows)} {len(full)}\n"); n += 1
    print('chains', n, 'skipped (other labels)', bad)
main()
