#!/usr/bin/env python3
"""Refined bundle-join lemma: classify the cheap (cost <= 4) joins leaving a bundle B.
Target chain starts t (OUT) / source last starts x (IN) are admissible if they occur in a phi-cycle
(pair symbols at positions 6,7 for starts; 0,7 for last starts) or in some A-bundle image G
(relabelling of 1..6, orientation, realization X/X').  A cheap join is REALIZABLE in an exact
partition only if t (resp. x) belongs to a cycle whose arrangement set is disjoint from B.
For phi-type targets the cycle is P(C_t) (single arrangement, disjoint from B iff C_t not in B).
For bundle-type targets we list all images G containing t as a chain start and test G cap B = empty."""
import sys, os, json, itertools
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from variant_search import setup
from r0verifyA import cost
src, orb = sys.argv[1], sys.argv[2]
n, F, cycles = setup(src, orb, 2)
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):
    k = p.index(0); w_ = list(p[k:] + p[:k]); return cyc_canon([v for v in w_ if v not in (0, n - 1)])
Rinv = lambda s: s[-1:] + s[:-1]
sw = {0: n - 1, n - 1: 0}
def last_of(s, l):
    x = s
    for _ in range(l - 1): x = comp(x, F)
    return x
def chains_of(real, g, ori):
    out = []
    for s, l in cycles[0][real]:
        s2 = tuple(g[v] for v in s)
        if ori: s2 = tuple(sw.get(v, v) for v in s2)
        out.append((s2, last_of(s2, l), l))
    return out
def Cset(chs):
    B = set()
    for s, x, l in chs:
        y = s
        for _ in range(l): B.add(Cof(y)); y = comp(y, F)
    return frozenset(B)
# all images: start -> list of image C-sets containing it; last -> list of C-sets
start_imgs = {}; last_imgs = {}
for perm in itertools.permutations(range(1, n - 1)):
    g = [0] + list(perm) + [n - 1]
    for real in (0, 1):
        for ori in (0, 1):
            chs = chains_of(real, g, ori); CS = Cset(chs)
            for s, x, l in chs:
                start_imgs.setdefault(s, set()).add(CS); last_imgs.setdefault(x, set()).add(CS)
pairs = (0, n - 1)
phi_start = lambda t: t[n - 2] in pairs and t[n - 1] in pairs
phi_last = lambda x: x[0] in pairs and x[n - 1] in pairs
allp = [p for p in itertools.permutations(range(n)) if p[n - 1] in pairs]
byprefix = {}; tails = {}
for p in allp:
    for k in range(4, n): byprefix.setdefault(p[:k], []).append(p); tails.setdefault(Rinv(p)[n - k:], []).append(p)
report = []
for real in (0, 1):
    for ori in (0, 1):
        g0 = list(range(n)); chs = chains_of(real, g0, ori); B = Cset(chs)
        stats = Counter()
        for s, x, l in chs:
            e = Rinv(x)
            for k in range(4, n):
                for t in byprefix.get(e[n - k:], []):
                    if Cof(t) in B: continue
                    if phi_start(t): stats["OUT->phi-start (realizable)"] += 1
                    elif t in start_imgs:
                        ok = [G for G in start_imgs[t] if not (G & B)]
                        stats["OUT->bundle-start realizable" if ok else "OUT->bundle-start only in images overlapping B"] += 1
                    else: stats["OUT->non-admissible"] += 1
            for k in range(4, n):
                for xp in tails.get(s[:k], []):
                    if Cof(xp) in B: continue
                    if phi_last(xp): stats["IN<-phi-last (realizable)"] += 1
                    elif xp in last_imgs:
                        ok = [G for G in last_imgs[xp] if not (G & B)]
                        stats["IN<-bundle-last realizable" if ok else "IN<-bundle-last only in images overlapping B"] += 1
                    else: stats["IN<-non-admissible"] += 1
        report.append(dict(realization="X" if real == 0 else "X'", orientation=ori, **stats))
        print(json.dumps(report[-1]), flush=True)
json.dump(report, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "bundle_join_lemma2.json"), "w"))
