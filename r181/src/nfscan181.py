#!/usr/bin/env python3
"""Round 181 -- measure the number of non-full rows N_nf of Bridge instances against m, D.
Falsification probe for a 'non-full budget' lemma NF: N_nf <= theta * m (or theta * D)."""
import os, random, sys
from collections import Counter
sys.path.insert(0, "r178/src"); sys.path.insert(0, "r176/src")
from bridge178 import coarsen, normalize
from run178 import words, to_route, perturb, greedy
rng = random.Random(181)
rows = []
for n, lim, npert, ngr in ((5, 40, 30, 10), (6, 12, 20, 10), (7, 3, 2, 0)):
    ws = words(n, lim)
    plan = [("archive", w, None) for w in ws] + [("perturbed", rng.choice(ws), 1 + rng.randrange(8)) for _ in range(npert)] \
         + [("greedy", None, rng.choice([0.0, 0.05, 0.2])) for _ in range(ngr)]
    for kind, w, prm in plan:
        route = normalize(to_route(w, n), n) if kind == "archive" else (perturb(to_route(w, n), n, rng, prm) if kind == "perturbed" else greedy(n, rng, prm))
        res = coarsen(route, n, rng)
        flat = [x for t in res["instance"] for x in t]
        ch = Counter((n - 1 - x[1]) + len(x[2]) for x in flat)
        nnf = sum(v for c, v in ch.items() if c >= 1)
        rows.append((n, kind, res["m"], res["r"], res["D"], len(flat), nnf, dict(sorted(ch.items()))))
for n in (5, 6, 7):
    for kind in ("archive", "perturbed", "greedy"):
        R = [x for x in rows if x[0] == n and x[1] == kind]
        if not R: continue
        rat_m = [x[6] / x[2] for x in R if x[2] > 0]; rat_D = [x[6] / x[4] for x in R if x[4] > 0]
        print(f"n={n} {kind:9s} routes {len(R):3d}  N_nf/m max {max(rat_m) if rat_m else None:.3f}  N_nf/D max {max(rat_D):.3f}  "
              f"example (m, r, D, rows, N_nf, charge hist) {R[0][2:]}")
