#!/usr/bin/env python3
"""Round Y -- block profiles of first-passage chains (input: the chain lists of rX, "name nb entry entry ...").
For a chain X and a symbol s in 1..7 the {8,s}-blocks are indexed by the cyclic orders D of the six symbols other than
8 and s; the label-8 rows of X lie in groups (8, C), and the {8,s}-block of (8, C) is C minus s.  Output per chain:
  name H A[s][t] for s = 1..7, t = 1..6
where A[s][t] = number of {8,s}-blocks containing at least t distinct label-8 groups of X, and
H = sum over the label-8 groups used by X of (7 - number of classes of the group covered by X)  (= the holes of the
label-8 part of X; equal to its deficit when no group carries two rows).  Also checks that consecutive entries of a
piece are linked by doors and reports chains with rows of other labels.
usage: fp_profiles.py CHAINS.txt[.gz] OUT.txt"""
import sys, gzip, collections
def door(e): return e[1:7] + e[0] + e[7]          # entry e1..e7 z -> next entry e2..e7 e1 z
def cls(w):
    i = w.index('8'); return w[i:] + w[:i]
def canon_cyc(seq):
    j = seq.index(min(seq)); return seq[j:] + seq[:j]
def main():
    f = gzip.open(sys.argv[1], 'rt') if sys.argv[1].endswith('.gz') else open(sys.argv[1])
    out = open(sys.argv[2], 'w'); nother = 0; n = 0
    for line in f:
        t = line.split()
        if len(t) < 3: continue
        name, nb, E = t[0], int(t[1]), t[2:]
        assert len(E) == nb
        rows = []; cur = [E[0]]
        for a, b in zip(E, E[1:]):
            if b == door(a): cur.append(b)
            else: rows.append(cur); cur = [b]
        rows.append(cur)
        groups = collections.defaultdict(set); other = 0
        for r in rows:
            z = r[0][-1]
            if z != '8': other += 1; continue
            for e in r:
                c = cls(e); C = c[1:]                # class with 8 first: the cyclic order of the rest is C
                groups[canon_cyc(C)].add(c)
        nother += other > 0; n += 1
        H = sum(7 - len(v) for v in groups.values())
        A = []
        for s in '1234567':
            cnt = collections.Counter(canon_cyc(C.replace(s, '')) for C in groups)
            A.append([sum(1 for v in cnt.values() if v >= t) for t in range(1, 7)])
        out.write(name + ' ' + str(H) + ' ' + ' '.join(str(x) for a in A for x in a) + '\n')
    print('chains', n, 'with rows of other labels', nother)
main()
