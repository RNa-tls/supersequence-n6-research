#!/usr/bin/env python3
"""Heuristic completion search via Theorem H.
With |X| = |U|/(n-2) candidate blocks, the incidence graph on (U + {r}) + X has E = V - 1 edges, so
it is a spanning tree  <=>  it is connected  <=>  #components C(X) = 1.  Simulated annealing over
X (fixed size), objective C(X), moves = swap one block out / one candidate in, biased toward blocks
touching small components.  Any X with C = 1 is checked independently (union-find tree check and
flowsat.verify on the original incidence graph)."""
import sys, os, json, time, random, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from candcore import analyse, kernel_rows
from complete import World
from hypertree import hyperedges, is_spanning_tree, R


def components(H, X, V):
    par = {v: v for v in V}
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for b in X:
        vs = H[b]; r0 = f(vs[0])
        for v in vs[1:]:
            r1 = f(v)
            if r1 != r0: par[r1] = r0
    comp = {}
    for v in V: comp.setdefault(f(v), []).append(v)
    # cycles reduce connectivity: C = V_components ; with |E| = |V|-1 (block nodes merged into their
    # vertex sets) the blocks are implicitly merged, so C counts vertex components.
    return comp, f


def anneal(H, U, P, seconds, seed, T0=1.5, T1=0.05):
    rng = random.Random(seed)
    cand = sorted(H); Hl = {b: list(H[b]) for b in cand}
    V = list(U) + [R]
    byv = {}
    for b in cand:
        for v in Hl[b]: byv.setdefault(v, []).append(b)
    X = set(rng.sample(cand, P)); out = [b for b in cand if b not in X]
    def score(X):
        comp, f = components(Hl, X, V)
        # cycle rank = E - V_tot + C_tot with block nodes; equivalently penalize via vertex components
        return len(comp), comp, f
    cur, comp, f = score(X); best = cur; t0 = time.time(); it = 0
    while time.time() - t0 < seconds:
        it += 1
        T = T0 * (T1 / T0) ** ((time.time() - t0) / seconds)
        # biased add: a candidate containing a vertex from a smallest component
        small = min(comp.values(), key=len) if len(comp) > 1 else None
        if small is not None and rng.random() < 0.7:
            v = rng.choice(small); add = rng.choice(byv.get(v, cand))
            if add in X: continue
        else:
            add = rng.choice(cand)
            if add in X: continue
        rem = rng.choice(list(X))
        X2 = set(X); X2.discard(rem); X2.add(add)
        new, comp2, f2 = score(X2)
        if new <= cur or rng.random() < math.exp(-(new - cur) / T):
            X, cur, comp, f = X2, new, comp2, f2
            if cur < best: best = cur
            if cur == 1: return X, dict(iterations=it, seconds=round(time.time() - t0, 1))
    return None, dict(iterations=it, best_components=best, seconds=round(time.time() - t0, 1))


if __name__ == "__main__":
    secs = float(sys.argv[1]); seeds = int(sys.argv[2])
    from flowsat import verify
    worlds = {}
    for job in sys.argv[3:]:
        n, spec = int(job.split("/")[0]), job.split("/")[1]
        W = worlds.setdefault(n, World(n)); rows = kernel_rows(n, spec)
        A = analyse(W, rows); U = A["U"]; H = hyperedges(W, A); P = len(U) // (n - 2)
        k = len(rows); G = sum(n - 1 - r[1] for r in rows)
        for sd in range(seeds):
            X, info = anneal(H, U, P, secs, sd)
            line = dict(n=n, kernel=spec[:60], score=k - G, seed=sd, found=X is not None, **info)
            if X:
                ok1, why = is_spanning_tree(H, list(X), U); ok2, why2 = verify(W, rows, list(X), n)
                line.update(tree_check=ok1, forest_check=ok2)
                if ok1 and ok2:
                    json.dump(dict(n=n, kernel=spec, rows=[[list(r[0]), r[1], list(r[2])] for r in rows],
                                   payload=[[list(W.blocks[b][0]), W.blocks[b][1]] for b in X]),
                              open(os.path.join(HERE, "..", "certs", f"anneal_completion_{n}_{spec[:60]}.json"), "w"))
            print(json.dumps(line), flush=True)
            if X: break
