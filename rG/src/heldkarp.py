#!/usr/bin/env python3
"""Final attack, dual thread -- Held-Karp LP bound for the exact ATSP model of L_n.
L_n = n + min weight of a Hamiltonian path in G_n (Houston notes, Lemma transfer; R178 route formula).
LP: depot node d; x_a >= 0 on arcs; out = in = 1 at every node; subtour cuts x(delta^+(S)) >= 1 for
nonempty S not containing d (separated exactly by max-flow from every node to d and from d to every node).
Columns: arcs of weight <= wmax initially, then pricing over ALL arcs with exact reduced costs, so the
final LP value is a valid lower bound (dual feasible for the full arc set)."""
import sys, math, itertools
import numpy as np
import highspy
import networkx as nx

def overlap_cost(u, v, n):
    for j in range(n - 1, 0, -1):
        if u[n - j:] == v[:j]: return n - j
    return n

def run(n, wmax0=3, verbose=True):
    P = list(itertools.permutations(range(n))); N = len(P); D = N    # depot index N
    idx = {p: i for i, p in enumerate(P)}
    # all arcs among perms with their weights, by weight class (generate lazily via suffix map)
    pref = {}
    for i, p in enumerate(P):
        for j in range(1, n): pref.setdefault(p[:j], []).append(i)
    def arcs_of_weight_le(w):
        out = []
        for i, p in enumerate(P):
            for c in range(1, w + 1):
                for jdx in pref.get(p[c:], []) if c < n else range(N):
                    if jdx != i and overlap_cost(p, P[jdx], n) == c: out.append((i, jdx, c))
        return out
    arcs = arcs_of_weight_le(wmax0) + [(D, i, 0) for i in range(N)] + [(i, D, 0) for i in range(N)]
    aset = set((a, b) for a, b, _ in arcs)
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    inf = highspy.kHighsInf
    # rows: out-degree (N+1), in-degree (N+1); cuts appended later
    nrows = 2 * (N + 1)
    for r in range(nrows): h.addRow(1.0, 1.0, 0, np.array([], dtype=np.int32), np.array([]))
    def add_cols(newarcs):
        for (a, b, w) in newarcs:
            h.addCol(float(w), 0.0, inf, 2, np.array([a, N + 1 + b], dtype=np.int32), np.array([1.0, 1.0]))
    add_cols(arcs)
    cuts = []
    it = 0
    while True:
        it += 1
        h.run()
        sol = h.getSolution(); x = np.array(sol.col_value); val = h.getInfo().objective_function_value
        # separation: support graph
        G = nx.DiGraph()
        for k, (a, b, w) in enumerate(arcs):
            if x[k] > 1e-9: G.add_edge(a, b, capacity=float(x[k]))
        newcuts = []
        for t in range(N):
            if t % 1 != 0: continue
        # min cut from depot to each node and each node to depot (exact separation)
        seen_sets = set()
        for t in range(N):
            for (s_, t_) in ((D, t), (t, D)):
                if s_ not in G or t_ not in G:
                    cut_val, (A, B) = 0.0, ({s_}, set(G.nodes) - {s_})
                else:
                    cut_val, (A, B) = nx.minimum_cut(G, s_, t_)
                if cut_val < 1 - 1e-6:
                    S = frozenset(B) if s_ == D else frozenset(A)     # S excludes depot
                    S = frozenset(v for v in S if v != D)
                    if S and S not in seen_sets: seen_sets.add(S); newcuts.append(S)
            if len(newcuts) > 60: break
        if newcuts:
            for S in newcuts:
                idxs = [k for k, (a, b, w) in enumerate(arcs) if a in S and b not in S]
                h.addRow(1.0, inf, len(idxs), np.array(idxs, dtype=np.int32), np.ones(len(idxs)))
                cuts.append(S)
            if verbose: print(f"  it {it}: LP {val:.4f}, +{len(newcuts)} cuts (total {len(cuts)})", flush=True)
            continue
        # pricing over all arcs with exact reduced costs
        duals = np.array(h.getSolution().row_dual)
        uo, ui = duals[:N + 1], duals[N + 1:2 * (N + 1)]
        cd = duals[2 * (N + 1):]
        def rc(a, b, w):
            r = w - uo[a] - ui[b]
            for j, S in enumerate(cuts):
                if a in S and b not in S: r -= cd[j]
            return r
        neg = []
        for i, p in enumerate(P):
            for jdx in range(N):
                if jdx == i or (i, jdx) in aset: continue
                w = overlap_cost(p, P[jdx], n)
                if w - uo[i] - ui[jdx] - (cd.max() if len(cd) else 0) * len(cuts) < -1e-9 or True:
                    r = rc(i, jdx, w)
                    if r < -1e-7: neg.append((i, jdx, w))
            if len(neg) > 5000: break
        if neg:
            for a in neg: aset.add((a[0], a[1]))
            arcs += neg; add_cols(neg)
            if verbose: print(f"  it {it}: LP {val:.4f}, priced in {len(neg)} arcs", flush=True)
            continue
        return val, len(cuts), len(arcs)

if __name__ == "__main__":
    for n in [int(a) for a in sys.argv[1:]] or [3, 4, 5]:
        val, nc, na = run(n)
        CONST = math.factorial(n) + math.factorial(n - 1) + math.factorial(n - 2) + n - 3
        print(f"n={n}: Held-Karp path LP = {val:.4f}  ->  length bound n + LP = {n + val:.4f}; CONST(n) = {CONST}; cuts {nc}, arcs {na}", flush=True)
