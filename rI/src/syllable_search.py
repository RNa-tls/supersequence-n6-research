#!/usr/bin/env python3
"""General-n search for closed long trails built from the syllables of the n = 8 period:
   S_r   = (n-3, bac) (n-1, bac)^r                                  r = 0..n-3
   X_r   = (n-3, cba) (n-2, bac) (n-1, cba) (n-4, bac) (n-1, bac)^r   r = 0..n-3
A cyclic syllable word omega has position product Pi(omega) of order m; the closed trail omega^m is
valid iff all its classes are distinct (independent of the start: S_n acts on the left).
Figure of merit (one trail, opened once): rate = (chains + 1) / classes; phi-cycle rate = 1/(n-2).
The n = 8 period is S_3 S_4 X_4 S_3 S_4 (m = 4, 104 chains, 672 classes, rate 105/672)."""
import sys, os, itertools, json, time
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
n = int(sys.argv[1]); maxlen = int(sys.argv[2]); TL = float(sys.argv[3])
I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
BAC, CBA = (1, 0, n - 1), (n - 1, 1, 0)
T = {s: tuple(list(range(2, n - 1)) + list(s)) for s in (BAC, CBA)}
def step(l, s): return comp(Fp[l - 1], T[s])
syl = {}
for r in range(0, n - 2):
    syl[f"S{r}"] = [(n - 3, BAC)] + [(n - 1, BAC)] * r
    if n - 4 >= 1: syl[f"X{r}"] = [(n - 3, CBA), (n - 2, BAC), (n - 1, CBA), (n - 4, BAC)] + [(n - 1, BAC)] * r
names = sorted(syl)
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
def evaluate(word):
    letters = [x for s in word for x in syl[s]]
    Pi = I
    for l, s in letters: Pi = comp(Pi, step(l, s))
    m = 1; X = Pi
    while X != I and m <= 200: X = comp(X, Pi); m += 1
    if X != I: return None
    P = I; seen = set(); chains = 0
    for rep in range(m):
        for l, s in letters:
            for j in range(l):
                c = canon(comp(P, Fp[j]))
                if c in seen: return None
                seen.add(c)
            chains += 1; P = comp(P, step(l, s))
    return dict(word=" ".join(word), m=m, chains=chains, classes=len(seen), rate=(chains + 1) / len(seen))
t0 = time.time(); found = []; tested = 0
def necklaces(L):
    for w in itertools.product(names, repeat=L):
        if min(w[i:] + w[:i] for i in range(L)) == w: yield w
for L in range(1, maxlen + 1):
    for w in necklaces(L):
        if time.time() - t0 > TL: break
        tested += 1
        r = evaluate(list(w))
        if r: found.append(r)
found.sort(key=lambda r: r["rate"])
if os.environ.get("DUMP"): json.dump([r for r in found if r["rate"] < 1 / (n - 2) - 1e-12], open(os.environ["DUMP"], "w"))
phi = 1 / (n - 2)
print(json.dumps(dict(n=n, maxlen=maxlen, tested=tested, valid=len(found), phi_rate=phi,
                      better_than_phi=sum(r["rate"] < phi - 1e-12 for r in found), sec=round(time.time() - t0, 1))))
for r in found[:12]: print(json.dumps(r))
import os
if os.environ.get("XONLY"):
    for r in [r for r in found if "X" in r["word"]][:15]: print("X", json.dumps(r))
