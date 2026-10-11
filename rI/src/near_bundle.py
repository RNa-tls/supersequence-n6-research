#!/usr/bin/env python3
"""Near-bundle diagnostics: for valid closed syllable trails, the best pair {u,v} and the coverage
profile over arrangements C (how many classes of P({u,v},C) the trail covers).  full = number of C
fully covered, partial = number touched but not full, frac_full = share of classes lying in full C's."""
import sys, os, itertools, json, time
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
n = int(sys.argv[1]); L = int(sys.argv[2]); alpha = sys.argv[3].split(","); TL = float(sys.argv[4])
I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
BAC, CBA = (1, 0, n - 1), (n - 1, 1, 0)
T = {s: tuple(list(range(2, n - 1)) + list(s)) for s in (BAC, CBA)}
step = lambda l, s: comp(Fp[l - 1], T[s])
syl = {}
for r in range(0, n - 2):
    syl[f"S{r}"] = [(n - 3, BAC)] + [(n - 1, BAC)] * r
    syl[f"X{r}"] = [(n - 3, CBA), (n - 2, BAC), (n - 1, CBA), (n - 4, BAC)] + [(n - 1, BAC)] * r
PHI = (n - 2) * (n - 1)
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
res = []; t0 = time.time()
for Lw in range(1, L + 1):
    for w in itertools.product(alpha, repeat=Lw):
        if min(w[i:] + w[:i] for i in range(Lw)) != w: continue
        if time.time() - t0 > TL: break
        letters = [x for s in w for x in syl[s]]
        Pi = I
        for l, s in letters: Pi = comp(Pi, step(l, s))
        m = 1; X = Pi
        while X != I and m <= 400: X = comp(X, Pi); m += 1
        if X != I: continue
        P = I; seen = set(); ok = True; chains = 0
        for _ in range(m):
            for l, s in letters:
                for j in range(l):
                    c = canon(comp(P, Fp[j]))
                    if c in seen: ok = False; break
                    seen.add(c)
                if not ok: break
                chains += 1; P = comp(P, step(l, s))
            if not ok: break
        if not ok: continue
        best = None
        for u, v in itertools.combinations(range(n), 2):
            cnt = Counter(cyc_canon([x for x in c if x not in (u, v)]) for c in seen)
            full = sum(1 for x in cnt.values() if x == PHI)
            fr = sum(x for x in cnt.values() if x == PHI) / len(seen)
            if best is None or fr > best[0]: best = (fr, (u, v), full, len(cnt) - full, sorted(Counter(cnt.values()).items()))
        res.append(dict(word=" ".join(w), m=m, chains=chains, classes=len(seen), rate=(chains + 1) / len(seen),
                        frac_full=round(best[0], 4), pair=best[1], full=best[2], partial=best[3], profile=best[4][:8]))
res.sort(key=lambda r: (-r["frac_full"], r["rate"]))
print(json.dumps(dict(n=n, valid=len(res), sec=round(time.time() - t0, 1))))
for r in res[:12]: print(json.dumps(r))
json.dump(res[:200], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"near_bundle_n{n}.json"), "w"))
