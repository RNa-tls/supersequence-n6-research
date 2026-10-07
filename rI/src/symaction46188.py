#!/usr/bin/env python3
"""Action of the partition stabilizer (order 12, from symmetry46188.json) on the six long trails and
on the 24 phi-cycles; isomorphism type via element orders and centre."""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
def canon(t):
    k = t.index(0); return t[k:] + t[:k]
def classes(t): return frozenset(canon(S[i]) for ch in t for i in ch)
longs = [classes(t) for t in trails if len(t) == 104]
phis = [classes(t) for t in trails if len(t) == 6]
phis.append(frozenset().union(*[classes(t) for t in trails if len(t) not in (6, 104)]))
sym = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "symmetry46188.json")))
G = [tuple(g) for g in sym["StabPartition"]]
img = lambda g, C: frozenset(canon(tuple(g[x] for x in c)) for c in C)
comp = lambda a, b: tuple(a[b[i]] for i in range(n))
def order(g):
    e = tuple(range(n)); x = g; k = 1
    while x != e: x = comp(g, x); k += 1
    return k
act_long = [[longs.index(img(g, C)) for C in longs] for g in G]
act_phi = [[phis.index(img(g, C)) for C in phis] for g in G]
orbits_phi = set()
for j in range(len(phis)): orbits_phi.add(frozenset(a[j] for a in act_phi))
centre = [g for g in G if all(comp(g, h) == comp(h, g) for h in G)]
res = dict(order=len(G), element_orders=dict(Counter(order(g) for g in G)), centre_size=len(centre), abelian=len(centre) == len(G),
           long_action=act_long, long_orbits=sorted(len(o) for o in {frozenset(a[j] for a in act_long) for j in range(6)}),
           long_point_stabilizer_sizes=[sum(a[j] == j for a in act_long) for j in range(6)],
           phi_orbit_sizes=sorted(len(o) for o in orbits_phi))
print(json.dumps(res))
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "symaction46188.json"), "w"))
