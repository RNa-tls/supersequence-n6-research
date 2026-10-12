#!/usr/bin/env python3
"""Packing-independent bundle-join lemma (n = 8, pair {0,7}).
For a bundle realization (closed trail covering a set B of arrangements C, pair {0,7}):
  OUT: for every chain of the bundle with last start x (end e = R^-1 x) and every permutation t whose
       special t[7] is 0 or 7 (i.e. every possible chain start of any {0,7}-system chain set) with
       cost(e, t) <= 4:  C(t) must lie in B;
  IN : for every chain start t of the bundle and every permutation x with x[7] in {0,7} (every possible
       last start) with cost(R^-1 x, t) <= 4:  C(x) must lie in B.
If both hold, any join of cost <= 4 touching the bundle connects two chains whose classes lie in B,
i.e. (in an exact partition) two chains of the same bundle.  Hence every join between a bundle and a
different cycle of a {0,7}-system partition costs >= 5.  The property is invariant under relabelling
symbols 1..6 and under (0 7), so checking the template (both orientations) proves it for every image.
Realizations checked: X (46188 trail 0) and X' (variant), both orientations."""
import sys, os, json, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from variant_search import setup                 # bundle templates with X and X' realizations
from r0verifyA import cost
src, orb = sys.argv[1], sys.argv[2]
n, F, cycles = setup(src, orb, 2)
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):
    k = p.index(0); w_ = list(p[k:] + p[:k]); return cyc_canon([v for v in w_ if v not in (0, n - 1)])
Rinv = lambda s: s[-1:] + s[:-1]
pairperms = [p for p in itertools.permutations(range(n)) if p[n - 1] in (0, n - 1)]
byprefix = {}
for p in pairperms:
    for j in range(4, n): byprefix.setdefault(p[:j], []).append(p)
# admissible chain starts / last starts of any packing built from A-bundle images (X/X', both
# orientations, any relabelling of 1..6) and phi-cycles (pair symbols at positions 6,7):
sw = {0: n - 1, n - 1: 0}
def last_of(s, l):
    x = s
    for _ in range(l - 1): x = comp(x, F)
    return x
tmpl = []
for real in (0, 1):
    for s, l in cycles[0][real]: tmpl.append((s, last_of(s, l)))
# bring template chains to canonical labels: relabel by every g fixing 0 and 7
bundle_starts = set(); bundle_lasts = set()
for perm in itertools.permutations(range(1, n - 1)):
    g = [0] + list(perm) + [n - 1]
    for ori in (0, 1):
        for s, x in tmpl:
            s2 = tuple(g[v] for v in s); x2 = tuple(g[v] for v in x)
            if ori: s2 = tuple(sw.get(v, v) for v in s2); x2 = tuple(sw.get(v, v) for v in x2)
            bundle_starts.add(s2); bundle_lasts.add(x2)
phi_ok = lambda p: p[n - 2] in (0, n - 1) and p[n - 1] in (0, n - 1)
admissible_start = lambda t: phi_ok(t) or t in bundle_starts
admissible_last = lambda x: (x[0] in (0, n - 1) and x[n - 1] in (0, n - 1)) or x in bundle_lasts   # phi last start = (b, c0..c5, a)
results = []
for real in (0, 1):
    for ori in (0, 1):
        cy = cycles[0][real]
        sw = {0: n - 1, n - 1: 0}
        chs = []
        for s, l in cy:
            if ori: s = tuple(sw.get(v, v) for v in s)
            x = s
            for _ in range(l - 1): x = comp(x, F)
            chs.append((s, x))
        B = set()
        for s, l in [(c[0], None) for c in chs]: pass
        for (s, x), (_, l) in zip(chs, cy):
            y = s
            for _ in range(l): B.add(Cof(y)); y = comp(y, F)
        bad_out = bad_in = 0; mincost_out_other = 9; mincost_in_other = 9
        for s, x in chs:
            e = Rinv(x)
            # OUT: t with cost(e,t) <= 4 <=> t[:k] == e[n-k:] for some k >= 4
            for k in range(4, n):
                for t in byprefix.get(e[n - k:], []):
                    if Cof(t) not in B and admissible_start(t): bad_out += 1; mincost_out_other = min(mincost_out_other, n - k)
            # IN: x' with cost(R^-1 x', s) <= 4 <=> (R^-1 x')[n-k:] == s[:k]; R^-1 x' = (x'7, x'0..x'6)
        tails = {}
        for xp in pairperms:
            e = Rinv(xp)
            for k in range(4, n): tails.setdefault(e[n - k:], []).append(xp)
        for s, x in chs:
            for k in range(4, n):
                for xp in tails.get(s[:k], []):
                    if Cof(xp) not in B and admissible_last(xp): bad_in += 1; mincost_in_other = min(mincost_in_other, n - k)
        results.append(dict(realization="X" if real == 0 else "X'", orientation="special 0" if ori == 0 else "special 7",
                            arrangements=len(B), chains=len(chs), cheap_joins_leaving_B_out=bad_out, cheap_joins_leaving_B_in=bad_in))
        print(json.dumps(results[-1]), flush=True)
json.dump(results, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "bundle_join_lemma.json"), "w"))
