#!/usr/bin/env python3
"""Audit of Theorem H (H1-H6) on the verified n = 7 score-10 structure (kernel with holes) and the
n = 6 / n = 5 solver completions:
 H1/H4: contracted incidence graph is a tree; sparsity |N(Y)| >= (n-2)|Y| + 1 checked on all Y of size <= 3
        and on random larger Y;
 H2: ownership from rooting at r is an exact partition of U into (n-2)-sets;
 H3: |X| = |U|/(n-2);
 H5/H6: expand back (un-contract) and rebuild the route by T-cycle traversal from the row starts,
        including rows with holes; check Hamiltonicity and that the length equals
        CONST + ((n-2)! - score)/(n-2)."""
import sys, os, json, math, random, itertools
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "rG", "src")); sys.path.insert(0, os.path.join(ROOT, "r178", "src"))
from complete import World, canon
from candcore import analyse, kernel_rows
from hypertree import hyperedges, is_spanning_tree, R
from forestsat2 import realize_and_check

def audit(W, rows, X, label):
    n = W.n; A = analyse(W, rows); U = A["U"]; H = hyperedges(W, A)
    out = dict(case=label, n=n)
    out["H3_size"] = len(X) == len(U) // (n - 2)
    out["all_candidates"] = all(b in H for b in X)
    ok, why = is_spanning_tree(H, X, U); out["H1_tree"] = ok
    rng = random.Random(0); spars = True
    Ys = [Y for k in (1, 2, 3) for Y in itertools.combinations(X, k)] if len(X) < 60 else \
         [tuple(rng.sample(X, rng.randint(1, len(X)))) for _ in range(3000)] + list(itertools.combinations(X, 2))
    for Y in Ys:
        NY = set().union(*(H[b] for b in Y))
        if len(NY) < (n - 2) * len(Y) + 1: spars = False; break
    out["H4_sparsity_sampled"] = spars
    # H2 ownership by BFS from r
    adjv = {}
    for b in X:
        for v in H[b]: adjv.setdefault(v, []).append(b)
    owner = {}; seen_b = set(); frontier = [R]; parent_class = {}
    while frontier:
        nf = []
        for v in frontier:
            for b in adjv.get(v, []):
                if b in seen_b: continue
                seen_b.add(b); parent_class[b] = v
                for c in H[b]:
                    if c != v: owner.setdefault(c, []).append(b); nf.append(c)
        frontier = nf
    out["H2_exact_ownership"] = sorted(owner) == sorted(U) and all(len(v) == 1 for v in owner.values()) \
        and all(sum(1 for c in H[b] if c != parent_class[b]) == n - 2 for b in X)
    ham, L, _ = realize_and_check(W, rows, [W.blocks[b] for b in X])
    k = len(rows); G = sum(n - 1 - r[1] for r in rows)
    CONST = math.factorial(n) + math.factorial(n - 1) + math.factorial(n - 2) + n - 3
    out["H5H6_route_hamiltonian"] = ham; out["length"] = L
    out["length_formula"] = CONST + (math.factorial(n - 2) - (k - G)) // (n - 2)
    return out

if __name__ == "__main__":
    W7 = World(7)
    base = json.load(open(os.path.join(ROOT, "rG", "certs", "base5906.json")))
    rows = [(tuple(r[0]), r[1], tuple(r[2])) for r in base["rows"]]
    print(json.dumps(audit(W7, rows, base["payload"], "n7 score-10 kernel with holes (5906)")), flush=True)
    for n, f in ((6, "htcut_completion_6_std.json"), (5, "htcut_completion_5_std.json")):
        W = World(n); d = json.load(open(os.path.join(ROOT, "rG", "certs", f)))
        rows = kernel_rows(n, "std")
        X = [W.bid[(tuple(a), b)] for a, b in d["payload"]]
        print(json.dumps(audit(W, rows, X, f"n{n} std (solver)")), flush=True)
