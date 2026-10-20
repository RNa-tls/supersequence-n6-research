#!/usr/bin/env python3
"""Round Q, section 1 -- exact length identity for multi-opening routes, checked on real words.

A route is a sequence of fragments (t, v, i, n): trail t, version v, start run i, n consecutive runs of that
version (cyclic).  The fragments of a trail must partition its runs (one version per trail).  The word is the
greedy overlap concatenation of the permutation route (each run = 8 left rotations of its first permutation).

Claimed identities (c_r = version join weight into run r, cut runs = fragment starts):
  (I1)  L = 46136 + (P - 1) + sum_b e_b - c(first fragment start),   e_b = w(exit, entry) - c(entry) - 1
  (I2)  J = L - 46085 = 48 + (P - 1) + [c_first = 2] + sum_b e_b
  (I3)  virtual cover: every cut run a of trail T gives the single-piece option T(a) (entry a, exit a-1).  Each
        route boundary (exit run x of trail T_x, entry run y of trail T_y) is the option pair
        T_x(x+1) -> T_y(y).  Every option has in-degree <= 1 and out-degree <= 1 (exactly one start, one end),
        so the options form one path plus disjoint cycles; e_b is the Round P option-pair excess.
The script builds random fragmentations (random cut sets, random fragment order, including adjacent fragments of
the same trail), measures L from the word itself, and checks I1-I3 and the cycle count.
usage: identity_check.py FAMILY.json NTEST SEED OUT.json"""
import sys, json, random

def w(x, y):
    for s in range(1, 8):
        if x[s:] == y[:8 - s]: return s
    return 8

def main():
    fam = json.load(open(sys.argv[1])); NT = int(sys.argv[2]); rng = random.Random(int(sys.argv[3]))
    RUNS = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]): RUNS[t, v] = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
    first = lambda t, v, k: RUNS[t, v][k % len(RUNS[t, v])]
    last = lambda t, v, k: (lambda p: p[7:] + p[:7])(first(t, v, k))
    cut = lambda t, v, k: w(last(t, v, k - 1), first(t, v, k))
    def word_len(frags):
        seen = set(); L = 0; prev = None
        for (t, v, i, n) in frags:
            for j in range(n):
                p = first(t, v, i + j)
                for r in range(8):
                    q = p[r:] + p[:r]; seen.add(q)
                    L += 8 if prev is None else w(prev, q); prev = q
        return L, len(seen)
    res = []; ok_all = True
    for it in range(NT):
        frags = []
        for t in range(30):
            v = rng.randrange(2); m = len(RUNS[t, v])
            k = 1 if rng.random() < 0.6 else rng.choice([2, 2, 3, 4, 6])
            cuts = sorted(rng.sample(range(m), k))
            for j, c in enumerate(cuts):
                nxt = cuts[(j + 1) % k]; n = (nxt - c) % m or m
                frags.append((t, v, c, n))
        rng.shuffle(frags)
        if it % 3 == 0:   # make some same-trail fragments adjacent
            frags.sort(key=lambda f: (f[0] * rng.random()))
        L, nperm = word_len(frags)
        P = len(frags)
        sum_e = 0; edges = []
        for f, g in zip(frags, frags[1:]):
            t, v, i, n = f; t2, v2, i2, n2 = g
            ex = last(t, v, i + n - 1); en = first(t2, v2, i2)
            e = w(ex, en) - cut(t2, v2, i2) - 1; sum_e += e
            # virtual edge: option of trail t whose exit is run i+n-1  ->  option of t2 with entry i2
            edges.append(((t, v, (i + n) % len(RUNS[t, v])), (t2, v2, i2 % len(RUNS[t2, v2]))))
        c0 = cut(*frags[0][:3])
        I1 = 46136 + (P - 1) + sum_e - c0
        J = L - 46085; I2 = 48 + (P - 1) + (1 if c0 == 2 else 0) + sum_e
        # virtual cover structure
        verts = {(t, v, i % len(RUNS[t, v])) for (t, v, i, n) in frags}
        outd = {}; ind = {}
        for a, b in edges: outd[a] = outd.get(a, 0) + 1; ind[b] = ind.get(b, 0) + 1
        deg_ok = all(outd.get(x, 0) <= 1 and ind.get(x, 0) <= 1 for x in verts) and set(outd) | set(ind) <= verts
        succ = dict(edges); starts = [x for x in verts if ind.get(x, 0) == 0]
        seen = set(); comps = 0
        for s in starts:
            x = s
            while x is not None and x not in seen: seen.add(x); x = succ.get(x)
        cycles = 0
        for x0 in verts:
            if x0 in seen: continue
            cycles += 1; x = x0
            while x not in seen: seen.add(x); x = succ[x]
        ok = (I1 == L and I2 == J and nperm == 40320 and deg_ok and len(starts) == 1)
        ok_all &= ok
        res.append(dict(test=it, pieces=P, L=L, J=J, identity_I1=I1, identity_I2=I2, all_perms=nperm == 40320, sum_e=sum_e,
                        same_trail_edges=sum(1 for a, b in edges if a[0] == b[0]), virtual_path_starts=len(starts), virtual_cycles=cycles, ok=ok))
    json.dump(dict(all_ok=ok_all, tests=res), open(sys.argv[4], "w"), indent=1)
    print(json.dumps(dict(all_ok=ok_all, n=NT, min_J=min(r["J"] for r in res), max_pieces=max(r["pieces"] for r in res),
                          with_cycles=sum(1 for r in res if r["virtual_cycles"] > 0), with_same_trail_edges=sum(1 for r in res if r["same_trail_edges"] > 0))))

main()
