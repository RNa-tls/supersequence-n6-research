#!/usr/bin/env python3
"""Round Z -- second implementation of the triple test: for every disjoint placement (X, o, g) of a pair list
(rZ/csrc/disjoint_z.c, LIST=1) write the union X + g(Y) (o = 0) or X + g(rev Y) (o = 1) as a pseudo-chain in the
first-passage list format; rZ/csrc/disjoint_z.c run on (pseudo-chains, chain list) then counts, for every union U and
every chain Z, the placements h(Z), h(rev Z) disjoint from U.  Three pairwise disjoint placements exist iff some count
is nonzero (as in rX/csrc/triple_test.c).  Entries of g(rev Y) are listed block by block, so they form rows of one
block each (arcs of length 1), which keeps the 2-cycle filter of disjoint_z exact.
usage: union_pseudochains.py FPLIST DISJOINT_Z_LIST_OUTPUT OUT"""
import sys
fact = [1, 1, 2, 6, 24, 120, 720, 5040, 40320]
def unrank(r):
    avail = list(range(8)); g = []
    for i in range(8):
        f = fact[7 - i]; d, r = divmod(r, f); g.append(avail.pop(d))
    return g
chains = {}
for l in open(sys.argv[1]):
    t = l.split(); chains[t[0]] = t[2:]
n = 0
with open(sys.argv[3], 'w') as out:
    for l in open(sys.argv[2]):
        if l.startswith('#') or not l.strip(): continue
        head, _, tail = l.partition('|'); h = head.split()
        X, Y = chains[h[0]], chains[h[1]]
        for p in tail.split():
            o, s, rank = map(int, p.split(':')); g = unrank(rank)
            ents = []
            for e in Y:
                d = [int(c, 16) - 1 for c in e]
                if o: d = d[::-1]
                ents.append(''.join('%x' % (g[x] + 1) for x in d))
            if o:      # one block per row: insert a non-door neighbour order (each entry is its own row anyway)
                pass
            allents = X + ents
            out.write('U%d_%s_%s_o%d_s%d %d %s\n' % (n, h[0], h[1], o, s, len(allents), ' '.join(allents))); n += 1
print('pseudo-chains', n)
