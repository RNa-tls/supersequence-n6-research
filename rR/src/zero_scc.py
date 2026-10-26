#!/usr/bin/env python3
"""Round R, sections 17-19 -- the zero-reduced-cost subgraph and its strongly connected components.
Charge theorem: G + 29 = sum_v chi(v), chi >= 0, so p = 0 is a feasible potential for the visit graph and the tight
(zero) transitions are exactly
  * cross-trail boundaries with e(x -> y) = 0 between consecutive single-piece visits (options x, y of distinct trails);
  * zero-charge visits (rotational, chi = 0), which act as macro nodes with entry C_a and exit C_{a-1} (complete
    rotation) -- their ports are those of the standard option S(C_a), so in the option graph they add no new arcs
    beyond the option C_a itself (the rotation is entered by an e = 0 arc into C_a and left like S(C_a)).
This program builds the option graph Z (nodes: the 10080 options; arcs: e = 0, distinct trails), computes its SCCs
(iterative Tarjan), the SCC size histogram, the number of zero cycles through each trail pair, and the longest path in
the condensation (a bound on how many zero transitions a tight route segment can chain without repeating an SCC).
usage: zero_scc.py RUNS.bin OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs)
    W = runs_io.weight_matrix(runs).astype(np.int16)
    T = np.array([x[0] for x in tv])
    pred = np.zeros(N, np.int64)
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]; m = mlen[t]
            for k in range(m): pred[o0 + k] = o0 + (k - 1) % m
    cut = W[pred, np.arange(N)]
    E = W[pred][:, :] - cut[None, :] - 1          # e(x -> y) = w(exit x, entry y) - cut(y) - 1
    cross = T[:, None] != T[None, :]
    Z = (E == 0) & cross
    assert ((E >= 0) | ~cross).all()
    adj = [np.nonzero(Z[i])[0].tolist() for i in range(N)]
    narcs = int(Z.sum())
    # iterative Tarjan
    index = [-1] * N; low = [0] * N; onst = [False] * N; st = []; comp = [-1] * N; idx = 0; nc = 0
    for s in range(N):
        if index[s] >= 0: continue
        stack = [(s, 0)]; index[s] = low[s] = idx; idx += 1; st.append(s); onst[s] = True
        while stack:
            v, i = stack[-1]
            if i < len(adj[v]):
                stack[-1] = (v, i + 1); w = adj[v][i]
                if index[w] < 0:
                    index[w] = low[w] = idx; idx += 1; st.append(w); onst[w] = True; stack.append((w, 0))
                elif onst[w]: low[v] = min(low[v], index[w])
            else:
                stack.pop()
                if stack: u = stack[-1][0]; low[u] = min(low[u], low[v])
                if low[v] == index[v]:
                    while True:
                        w = st.pop(); onst[w] = False; comp[w] = nc
                        if w == v: break
                    nc += 1
    comp = np.array(comp); sizes = np.bincount(comp)
    hist = {}
    for sz in sizes: hist[int(sz)] = hist.get(int(sz), 0) + 1
    # trails inside nontrivial SCCs
    nontriv = [c for c in range(nc) if sizes[c] > 1]
    trails_in = sorted({int(T[i]) for i in range(N) if sizes[comp[i]] > 1})
    max_trails = max((len({int(T[i]) for i in np.nonzero(comp == c)[0]}) for c in nontriv), default=0)
    # condensation DAG longest path (number of SCCs on a path of zero arcs)
    order = list(range(nc))        # Tarjan numbers SCCs in reverse topological order: arcs go from higher to lower comp ids
    dag = [set() for _ in range(nc)]
    for i in range(N):
        for j in adj[i]:
            if comp[i] != comp[j]: dag[comp[i]].add(comp[j])
    longest = [1] * nc
    for c in range(nc):              # comp ids increase along reverse topological order -> successors have smaller ids
        for d in dag[c]: longest[c] = max(longest[c], 1 + longest[d])
    out = dict(options=N, zero_arcs=narcs, sccs=nc, scc_size_hist=hist, nontrivial_sccs=len(nontriv), options_in_nontrivial=int(sum(sizes[c] for c in nontriv)),
               trails_in_nontrivial=trails_in, max_trails_in_one_scc=max_trails, longest_zero_path_in_condensation_sccs=int(max(longest)))
    print(json.dumps(out)); open(sys.argv[2], "w").write(json.dumps(out) + "\n")

main()
