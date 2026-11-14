#!/usr/bin/env python3
"""Round X -- second implementation of rX/csrc/twosided.c (different loop structure, written separately).

For every r <= RMAX and every value v in (0, c] with v = a r (mod b), decide whether a chain of r pieces can have
value v under the two-sided piece-count lemma:
  case A: a core point (l, w) with w >= v and a head point (l', u') with l <= l' <= r and v <= u' <= w determine the
          tail point (l'', u) = (r + l - l', v - u' + w), which must be a census point; empty head (l' = l) needs
          u' = w, empty tail (l'' = l) needs u = w; head and tail values >= (a - 6 b) x pieces.
  case B: points (l1, u1), (l2, u2) with u1, u2 >= v, m = r - l1 - l2 >= 1 and v - u1 - u2 >= (a - 6 b) m
          (with THETA: not both u1, u2 >= THETA).
The search stops at the first witness.  Output: the same format as twosided.c; the caller compares the two files.
usage: check_twosided.py POINTS.txt RMAX [THETA] > OUT.txt"""
import sys
pts = {}; a = b = c = None
for l in open(sys.argv[1]):
    if l.startswith("#"):
        t = l.split(); a, b, c = int(t[2]), int(t[3]), int(t[4]); continue
    t = l.split()
    if len(t) > 1: pts[int(t[0])] = sorted(int(x) for x in t[1:])
RMAX = int(sys.argv[2]); THETA = int(sys.argv[3]) if len(sys.argv) > 3 else 1 << 29
lo = a - 6 * b; L = sorted(pts); VS = {l: set(v) for l, v in pts.items()}
cores_by_w = sorted(((w, l) for l in L for w in pts[l]), reverse=True)          # cores with large w first
def caseA(r, v):
    for w, l in cores_by_w:
        if w < v: break
        if l > r: continue
        for l1 in range(l, r + 1):
            if l1 not in VS: continue
            for u1 in pts[l1]:
                if u1 < v or u1 > w: continue
                if l1 == l and u1 != w: continue
                if u1 - w < lo * (l1 - l): continue
                l2 = r + l - l1; u2 = v - u1 + w
                if l2 < l or l2 not in VS or u2 not in VS[l2]: continue
                if l2 == l and u2 != w: continue
                if u2 - w < lo * (l2 - l): continue
                return True
    return False
big = sorted(((u, l) for l in L for u in pts[l]), reverse=True)
minL = {v: min((l for u, l in big if u >= v), default=10 ** 9) for v in range(1, c + 1)}
def caseB(r, v):
    if 2 * minL[v] + 1 > r: return False
    for u1, l1 in big:
        if u1 < v: break
        for u2, l2 in big:
            if u2 < v: break
            if u1 >= THETA and u2 >= THETA: continue
            m = r - l1 - l2
            if m >= 1 and v - u1 - u2 >= lo * m: return True
    return False
print("# twosided line %d %d %d RMAX %d theta %d (second implementation)" % (a, b, c, RMAX, THETA))
for r in range(1, RMAX + 1):
    out = []
    for v in range(1, c + 1):
        if (a * r - v) % b: continue
        A = caseA(r, v); B = caseB(r, v)
        if A or B: out.append("%d:%s" % (v, "AB" if A and B else ("A" if A else "B")))
    print(r, " ".join(out))
