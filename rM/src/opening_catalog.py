#!/usr/bin/env python3
"""Round M (section 3) -- OPENING CATALOG of the closed trails of a family (family_export.py JSON).

A closed trail version is a cyclic sequence of runs st[0..m-1]; its cyclic edges e_k = st[k-1] -> st[k]
have weight w_k = w(last(st[k-1]), st[k]) in {2 (F-step inside a chain), 3 (cost-3 join)}.
An r = 0 OPENING is a nonempty set C of cyclic edges; it leaves |C| pieces and changes
        Delta E = #(w2 edges in C)              (exact: a cut F-step splits a world-orbit segment)
and every piece has entry st[k] (k with e_k in C) and exit last(st[k'-1]) (the next cut k').
Exhaustiveness: every opening is a subset of the m cyclic edges, Delta E and the endpoint set are
additive over the cut edges, so the single-edge table below (all m edges, grouped into orbits of the
trail's automorphism group Aut = {(d, g in S_8) : g(st[k]) = st[k+d] for all k}) is a complete
description of all openings; inequivalent openings with c cuts = Aut-orbits of c-subsets.
For every edge orbit: weight, chain position, join type, entry/exit world and moving symbol, the
phi-frame C (the 6-cycle left after deleting the special and the moving symbol), and the boundary
weight profile: exits of other trails (any version, any cut) entering this entry with weight w, and
entries of other trails reachable from this exit with weight w (w = 2..5), plus the counts of
IDEAL boundaries (w = cut weight of the target + 1) and of e <= 1 boundaries.
usage: opening_catalog.py FAMILY.json OUT.json"""
import sys, json, itertools
from collections import Counter, defaultdict
import numpy as np

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
SIG = {(1, 0, 7): "bac", (0, 1, 7): "skip", (0, 7, 1): "s071", (1, 7, 0): "s170", (7, 1, 0): "cba"}
def join_type(x, t):
    for s, name in SIG.items():
        if x[2:n - 1] + tuple(x[k] for k in s) == t: return name
    return None
def frame(p):
    """world a = p[7], moving symbol w = p[0]; frame = cyclic 6-word of p[1..6] (canonical rotation)"""
    c = p[1:7]; return min(c[i:] + c[:i] for i in range(6))

def automorphisms(st):
    m = len(st); pos = {s: i for i, s in enumerate(st)}; out = []
    for d in range(m):
        g = [0] * n
        for i in range(n): g[st[0][i]] = st[d][i]
        ok = True
        for k in range(m):
            img = tuple(g[x] for x in st[k])
            if pos.get(img) != (k + d) % m: ok = False; break
        if ok: out.append((d, tuple(g)))
    return out

def main():
    fam = json.load(open(sys.argv[1]))
    T = []
    for tr in fam["trails"]:
        T.append([[tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)] for s in tr["versions"]])
    # global index of all cut positions (trail, version, k): entry st[k], exit last(st[k-1]), cut weight
    entries = defaultdict(list); exits = defaultdict(list)
    for t, vers in enumerate(T):
        for v, st in enumerate(vers):
            for k in range(len(st)):
                c = wt(last(st[k - 1]), st[k])
                entries[st[k]].append((t, v, k, c)); exits[last(st[k - 1])].append((t, v, k, c))
    def out_profile(u, t0):
        """entries of OTHER trails reachable from exit u: counts by weight, ideal (w = c+1), e<=1"""
        prof = Counter(); ideal = 0; e1 = 0
        for w_ in range(2, 6):
            for perm in itertools.permutations(u[:w_]):
                y = u[w_:] + perm
                if wt(u, y) != w_: continue
                for (t, v, k, c) in entries.get(y, []):
                    if t == t0: continue
                    prof[w_] += 1; ideal += (w_ == c + 1); e1 += (w_ <= c + 2)
        return dict(sorted(prof.items())), ideal, e1
    def in_profile(y, t0, c0):
        prof = Counter(); ideal = 0; e1 = 0
        for w_ in range(2, 6):
            # exits x with w(x, y) = w_: x[w_:] = y[:8-w_]; x = perm(remaining) + y[:8-w_]
            rest = [s for s in range(n) if s not in y[:n - w_]]
            for perm in itertools.permutations(rest):
                x = tuple(perm) + y[:n - w_]
                if wt(x, y) != w_: continue
                for (t, v, k, c) in exits.get(x, []):
                    if t == t0: continue
                    prof[w_] += 1; ideal += (w_ == c0 + 1); e1 += (w_ <= c0 + 2)
        return dict(sorted(prof.items())), ideal, e1
    cat = []
    for t, vers in enumerate(T):
        kind = "phi" if len(vers[0]) == 42 else ("A" if len(vers[0]) == 672 else "other%d" % len(vers[0]))
        for v, st in enumerate(vers):
            m = len(st)
            w = [wt(last(st[k - 1]), st[k]) for k in range(m)]
            assert set(w) <= {2, 3}, "closed trail with an edge of weight > 3"
            # chain decomposition: chain starts are k with w_k = 3
            cs = [k for k in range(m) if w[k] == 3]
            chain_of = {};
            for a, b in zip(cs, cs[1:] + [cs[0] + m]):
                for k in range(a, b): chain_of[k % m] = (a, b - a, k - a)    # (chain start, length, position)
            aut = automorphisms(st)
            # edge orbits under the shift part of Aut
            shifts = sorted({d for d, g in aut})
            seen = set(); orbits = []
            for k in range(m):
                if k in seen: continue
                orb = sorted({(k + d) % m for d in shifts}); seen |= set(orb); orbits.append(orb)
            rows = []
            for orb in orbits:
                k = orb[0]; entry = st[k]; ex = last(st[k - 1])
                a, ln, ps = chain_of[k]
                jt = join_type(st[k - 1], st[k]) if w[k] == 3 else None
                op, oi, oe = out_profile(ex, t); ip, ii, ie = in_profile(entry, t, w[k])
                rows.append(dict(edge=k, orbit_size=len(orb), cut_w=w[k], dE=3 - w[k], join=jt,
                                 chain_len=ln, pos_in_chain=ps,
                                 entry=dict(start="".join(map(str, entry)), world=entry[7], moving=entry[0], frame="".join(map(str, frame(entry)))),
                                 exit=dict(perm="".join(map(str, ex)), run_start="".join(map(str, st[k - 1])), world=st[k - 1][7], moving=st[k - 1][0]),
                                 in_profile=ip, in_ideal=ii, in_e1=ie, out_profile=op, out_ideal=oi, out_e1=oe))
            chains = Counter(chain_of[k][1] for k in cs)
            joins = Counter(join_type(st[k - 1], st[k]) for k in cs)
            cat.append(dict(trail=t, version=v, kind=kind, runs=m, chains=len(cs), E_T=len(cs) - m / 7,
                            chain_lengths=dict(sorted(chains.items())), join_types=dict(sorted(joins.items())),
                            worlds=dict(sorted(Counter(s[7] for s in st).items())),
                            aut_order=len(aut), edge_orbits=len(orbits), openings=rows))
            print(json.dumps(dict(trail=t, version=v, kind=kind, runs=m, chains=len(cs), aut=len(aut), orbits=len(orbits),
                                  w3=sum(1 for x in w if x == 3), joins=dict(joins))), flush=True)
    json.dump(dict(family=sys.argv[1], trails=cat), open(sys.argv[2], "w"))

if __name__ == "__main__":
    main()
