#!/usr/bin/env python3
"""Generalized bundle scan: period = (cyclic arrangement of) NS S-syllables S_r (r in RS) and one hub
detour D = (l1,s1)(l2,bac)(l3,s3)(l4,bac)(n-1,bac)^rD with s1,s3 in {cba,bca}, l_i in {n-4..n-1},
rD in RS.  Reports every closed valid bundle with its saving k(n-1)-(q+1)."""
import sys, os, itertools, json, time
from collections import Counter
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
n = int(sys.argv[1]); NS = int(sys.argv[2]); RS = [int(x) for x in sys.argv[3].split(",")]; TL = float(sys.argv[4])
I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
BAC, CBA, BCA = (1, 0, n - 1), (n - 1, 1, 0), (1, n - 1, 0)
T = {s: tuple(list(range(2, n - 1)) + list(s)) for s in (BAC, CBA, BCA)}
STEP = {(l, s): comp(Fp[l - 1], T[s]) for l in range(1, n) for s in (BAC, CBA, BCA)}
PHI = (n - 2) * (n - 1)
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def S(r): return [(n - 3, BAC)] + [(n - 1, BAC)] * r
def evaluate(letters):
    Pi = I
    for x in letters: Pi = comp(Pi, STEP[x])
    m = 1; X = Pi
    while X != I and m <= 60: X = comp(X, Pi); m += 1
    if X != I: return None
    if (m * sum(l for l, _ in letters)) % PHI: return None
    P = I; seen = set(); chains = 0
    for _ in range(m):
        for (l, s) in letters:
            for j in range(l):
                c = canon(comp(P, Fp[j]))
                if c in seen: return None
                seen.add(c)
            chains += 1; P = comp(P, STEP[(l, s)])
    for u, v in itertools.combinations(range(n), 2):
        cnt = Counter(cyc_canon([x for x in c if x not in (u, v)]) for c in seen)
        if set(cnt.values()) == {PHI}:
            k = len(cnt); return dict(pair=(u, v), k=k, chains=chains, m=m, saving=k * (n - 1) - (chains + 1))
    return None
lens = list(range(max(1, n - 4), n))
detours = []
for l1, s1, l2, l3, s3, l4, rD in itertools.product(lens, (CBA, BCA), lens, lens, (CBA, BCA), lens, RS):
    detours.append(((l1, s1), (l2, BAC), (l3, s3), (l4, BAC)) + ((n - 1, BAC),) * rD)
t0 = time.time(); found = {}; tested = 0
for Ss in itertools.product(RS, repeat=NS):
    for d in detours:
        if time.time() - t0 > TL: break
        for pos in range(NS + 1):            # detour position among the S syllables
            sy = [S(r) for r in Ss]; sy.insert(pos, list(d))
            letters = tuple(x for s in sy for x in s)
            tested += 1
            r = evaluate(letters)
            if r:
                key = (r["k"], r["chains"], r["saving"])
                desc = " ".join(["S%d" % x for x in Ss[:pos]] + ["D" + str([(l, 'c' if s == CBA else ('b' if s == BCA else 'a')) for l, s in d[:4]]) + "+%d" % (len(d) - 4)] + ["S%d" % x for x in Ss[pos:]])
                found.setdefault(key, []).append(desc)
print(json.dumps(dict(n=n, NS=NS, RS=RS, tested=tested, bundle_types=len(found), sec=round(time.time() - t0, 1))))
for key, v in sorted(found.items(), key=lambda kv: -kv[0][2]):
    print(json.dumps(dict(k=key[0], chains=key[1], saving=key[2], examples=sorted(set(v))[:40], count=len(v))))
