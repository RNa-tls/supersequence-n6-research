#!/usr/bin/env python3
"""Which closed syllable trails are BUNDLES: class set = disjoint union of whole phi-cycle sets
P({u,v},C) for one pair {u,v} (every C, obtained by deleting u and v, occurs exactly (n-2)(n-1)
times).  For a bundle with k = classes/((n-2)(n-1)) arrangements and q chains, the saving against
k free phi-cycles is  sav = k(n-1) - (q + 1)  (each phi-cycle costs n-2 chains + 1 trail)."""
import sys, os, itertools, json, time
from collections import Counter
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
n = int(sys.argv[1]); maxlen = int(sys.argv[2]); TL = float(sys.argv[3]); minlen = int(sys.argv[4]) if len(sys.argv) > 4 else 1
I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
BAC, CBA = (1, 0, n - 1), (n - 1, 1, 0)
T = {s: tuple(list(range(2, n - 1)) + list(s)) for s in (BAC, CBA)}
step = lambda l, s: comp(Fp[l - 1], T[s])
syl = {}
for r in range(0, n - 2):
    syl[f"S{r}"] = [(n - 3, BAC)] + [(n - 1, BAC)] * r
    if n - 4 >= 1: syl[f"X{r}"] = [(n - 3, CBA), (n - 2, BAC), (n - 1, CBA), (n - 4, BAC)] + [(n - 1, BAC)] * r
names = sorted(syl)
if os.environ.get("ALPHA"): names = [x for x in os.environ["ALPHA"].split(",")]
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
PHI = (n - 2) * (n - 1)
def evaluate(word):
    letters = [x for s in word for x in syl[s]]
    tot = sum(l for l, _ in letters)
    Pi = I
    for l, s in letters: Pi = comp(Pi, step(l, s))
    m = 1; X = Pi
    while X != I and m <= 400: X = comp(X, Pi); m += 1
    if X != I: return None
    if (m * tot) % PHI: return dict(bundle=False, prefilter=True)
    P = I; seen = set(); chains = 0
    for rep in range(m):
        for l, s in letters:
            for j in range(l):
                c = canon(comp(P, Fp[j]))
                if c in seen: return None
                seen.add(c)
            chains += 1; P = comp(P, step(l, s))
    if len(seen) % PHI: return dict(bundle=False)
    for u, v in itertools.combinations(range(n), 2):
        cnt = Counter(cyc_canon([x for x in c if x not in (u, v)]) for c in seen)
        if set(cnt.values()) == {PHI}:
            k = len(cnt)
            return dict(bundle=True, pair=(u, v), k=k, chains=chains, m=m, word=" ".join(word),
                        saving=k * (n - 1) - (chains + 1), saving_per_C=(k * (n - 1) - (chains + 1)) / k)
    return dict(bundle=False)
t0 = time.time(); found = []; tested = valid = 0
for L in range(minlen, maxlen + 1):
    for w in itertools.product(names, repeat=L):
        if min(w[i:] + w[:i] for i in range(L)) != w: continue
        if time.time() - t0 > TL: break
        tested += 1
        r = evaluate(list(w))
        if r is None: continue
        if not r.get("prefilter"): valid += 1
        if r["bundle"]: found.append(r)
found.sort(key=lambda r: -r["saving_per_C"])
print(json.dumps(dict(n=n, maxlen=maxlen, tested=tested, valid=valid, bundles=len(found), positive=sum(r["saving"] > 0 for r in found),
                      sec=round(time.time() - t0, 1))))
for r in found[:15]: print(json.dumps(r))
json.dump(found, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"bundles_n{n}_L{minlen}-{maxlen}.json"), "w"))
