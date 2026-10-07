#!/usr/bin/env python3
"""Full-chain rigidity: chain from s of length n-1 (classes of s F^i, i=0..n-2), last start x = s F^(n-2),
cost-3 successor t = x o T_sigma.  For each sigma != bac (and != cab = R^2 x, same class) list the
pairs (j, i) with class(t F^j) = class(s F^i), and the explicit rotation.  Printed for n = 5..12."""
import itertools, json
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
for n in range(5, 13):
    F = tuple(list(range(1, n - 1)) + [0, n - 1])
    Fp = [tuple(range(n))]
    for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
    s = tuple(range(n))
    def canon(p): return min(p[i:] + p[:i] for i in range(n))
    cl = {canon(comp(s, Fp[i])): i for i in range(n - 1)}
    x = comp(s, Fp[n - 2]); res = {}
    for sig in itertools.permutations((0, 1, n - 1)):
        name = "".join("abc"[[0, 1, n - 1].index(z)] for z in sig)
        t = comp(x, tuple(list(range(2, n - 1)) + list(sig)))
        hits = [(j, cl[canon(comp(t, Fp[j]))]) for j in range(n - 1) if canon(comp(t, Fp[j])) in cl]
        res[name] = dict(t=t, hits=hits)
    print(n, json.dumps({k: v["hits"] for k, v in res.items()}), "t(bca)=", res["bca"]["t"], "t(abc)=", res["abc"]["t"])
