#!/usr/bin/env python3
"""Round Omega -- two-sided tables with a two-threshold exclusion in Case B (generalises rX/csrc/twosided.c THETA).

Case A of the two-sided lemma (core point, head point, tail point) does not depend on any exclusion; it is taken from
the output of rX/csrc/twosided.c run on the same (truncated) census points WITHOUT a threshold (the flags A / AB).
Case B is recomputed here, written separately: points (l1, u1), (l2, u2) with u1, u2 >= v, a middle of m >= 1 pieces
of value v - u1 - u2 >= (a - 6 b) m, r = l1 + l2 + m, a r = v (mod b).  A pair (u1, u2) is not used when it is
excluded by one of the rectangles (p, q): (u1 >= p and u2 >= q) or (u1 >= q and u2 >= p).  The two ends of Case B are
row-disjoint primitive parts of one chain, so a rectangle may be used exactly when no two row-disjoint primitive
parts of values >= p and >= q can exist in the chain's class of covers (coexistence table, rOmega/src/compat2d.py).
Check mode: with the single rectangle (t, t) the output must equal twosided.c with THETA = t (compared by the caller).
usage: twosided_compat.py POINTS.txt TWOSIDED_NO_THETA_OUTPUT RMAX p1,q1 [p2,q2 ...] > OUT.txt   ('-' = no rectangle)"""
import sys
pts = {}; a = b = c = None
for l in open(sys.argv[1]):
    if l.startswith('#'):
        t = l.split(); a, b, c = int(t[2]), int(t[3]), int(t[4]); continue
    t = l.split()
    if len(t) > 1: pts[int(t[0])] = sorted(int(x) for x in t[1:])
caseA = {}
for l in open(sys.argv[2]):
    if l.startswith('#'):
        assert ' theta %d' % (1 << 29) in l or 'theta' not in l, 'the case-A source must be run without THETA'; continue
    t = l.split(); r = int(t[0])
    caseA[r] = {int(x.split(':')[0]) for x in t[1:] if 'A' in x.split(':')[1]}
RMAX = int(sys.argv[3])
rects = [] if sys.argv[4:] == ['-'] else [tuple(map(int, s.split(','))) for s in sys.argv[4:]]
lo = a - 6 * b
def excluded(u1, u2):
    return any((u1 >= p and u2 >= q) or (u1 >= q and u2 >= p) for p, q in rects)
# least r (= l1 + l2 + m) for each v in Case B, written as: for each value pair, the least l1, l2 carrying them
best_len = {}                                  # value u -> least piece count of a point with that value
for l, vs in pts.items():
    for u in vs:
        if u not in best_len or l < best_len[u]: best_len[u] = l
U = sorted(best_len)
Bmin = {}
for v in range(1, c + 1):
    m_best = None
    for u1 in U:
        if u1 < v: continue
        for u2 in U:
            if u2 < v or excluded(u1, u2): continue
            x = u1 + u2 - v                    # the middle must have value -x >= lo * m, m >= 1
            m = max(1, -(-x // (-lo)))
            tot = best_len[u1] + best_len[u2] + m
            if m_best is None or tot < m_best: m_best = tot
    Bmin[v] = m_best
print('# twosided line %d %d %d RMAX %d rectangles %s (rOmega twosided_compat; case A from twosided.c)' % (a, b, c, RMAX, ' '.join('%d,%d' % r for r in rects) or '-'))
for r in range(1, RMAX + 1):
    out = []
    for v in range(1, c + 1):
        if (a * r - v) % b: continue
        A = v in caseA.get(r, ())
        B = Bmin[v] is not None and r >= Bmin[v]
        if A or B: out.append('%d:%s' % (v, 'AB' if A and B else ('A' if A else 'B')))
    print(r, ' '.join(out))
