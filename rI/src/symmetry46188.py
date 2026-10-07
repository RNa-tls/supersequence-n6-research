#!/usr/bin/env python3
"""Exact symbol-relabelling symmetry of the 46188 r=0 partition.
For every g in S_8 (value relabelling) test g(C_0) = C_j where C_j = class set of long trail j.
Lambda = {g : g(C_0) is a long-trail class set};  Stab = {g : g(C_0) = C_0}.  Also the stabilizer of
the union of the long trails, of the union of the phi-cycles, and of the whole partition."""
import sys, os, json, itertools
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
def canon(t):
    k = t.index(0); return t[k:] + t[:k]
def classes(t):
    out = set()
    for ch in t:
        for i in ch: out.add(canon(S[i]))
    return frozenset(out)
longs = [classes(t) for t in trails if len(t) == 104]
phis = [classes(t) for t in trails if len(t) == 6]
resid = frozenset().union(*[classes(t) for t in trails if len(t) not in (6, 104)])
phis.append(resid)
Lset = {c: j for j, c in enumerate(longs)}
LU = frozenset().union(*longs); PU = frozenset().union(*phis)
C0 = longs[0]; C0l = list(C0)
Lam, Stab, StabLU, StabPU, StabPart = [], [], [], [], []
phiset = set(phis)
for g in itertools.permutations(range(n)):
    img = frozenset(canon(tuple(g[x] for x in c)) for c in C0l)
    if img in Lset:
        Lam.append((g, Lset[img]))
        if img == C0: Stab.append(g)
for g in itertools.permutations(range(n)):
    # union stabilizers (cheap rejection on a sample first)
    if all(canon(tuple(g[x] for x in c)) in LU for c in list(LU)[:50]):
        if frozenset(canon(tuple(g[x] for x in c)) for c in LU) == LU:
            StabLU.append(g)
            if frozenset(frozenset(canon(tuple(g[x] for x in c)) for c in P) for P in phis) == phiset and \
               set(frozenset(canon(tuple(g[x] for x in c)) for c in Lc) for Lc in longs) == set(longs):
                StabPart.append(g)
def comp(a, b): return tuple(a[b[i]] for i in range(n))
def is_group(G):
    Gs = set(G); return all(comp(a, b) in Gs for a in Gs for b in Gs)
def ct(p):
    seen = set(); c = []
    for i in range(n):
        if i in seen: continue
        j = i; L = 0
        while j not in seen: seen.add(j); j = p[j]; L += 1
        c.append(L)
    return tuple(sorted(c, reverse=True))
lam = [g for g, _ in Lam]
res = dict(Lambda_size=len(Lam), Lambda_per_trail=dict(Counter(j for _, j in Lam)), Lambda_is_group=is_group(lam),
           Lambda_fixed_points=sorted(set.intersection(*[{i for i in range(n) if g[i] == i} for g in lam])),
           Lambda_cycle_types=dict(Counter(map(str, map(ct, lam)))),
           Stab_size=len(Stab), Stab=Stab, Stab_is_group=is_group(Stab),
           StabLU_size=len(StabLU), StabLU_is_group=is_group(StabLU), StabLU_cycle_types=dict(Counter(map(str, map(ct, StabLU)))),
           StabPartition_size=len(StabPart), StabPartition=StabPart)
print(json.dumps(res, default=str))
json.dump(dict(res, Lambda=[(g, j) for g, j in Lam], StabLU=StabLU), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "symmetry46188.json"), "w"), default=str)
