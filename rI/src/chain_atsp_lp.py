#!/usr/bin/env python3
"""LP lower bound (cutting planes) for the chain-level ATSP of a fixed r = 0 chain set.
Nodes: chains 0..q-1, depot D (path start/end), hub H (exact stand-in for no-overlap links).
Arcs: chain->chain with overlap >= 1, weight c - 3;  chain->H weight n - 3;  H->chain 0;  D->chain 0;
chain->D 0.  Constraints: out = in = 1 at chains and D; in = out at H; for every set S of nodes
not containing D:  x(delta^+(S)) >= 1   (every node must reach the path end).
Valid for every real route (see chain_atsp_exact.py for the hub argument), so LP value + base is a
rigorous lower bound on the length of any r = 0 route using exactly this chain set."""
import sys, os, json, math, time
import numpy as np
import highspy
import networkx as nx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
from chain_atsp import chains_of
path = sys.argv[1]; maxit = int(sys.argv[2]); STRIDE = int(sys.argv[3]) if len(sys.argv) > 3 else 7; MIP = len(sys.argv) > 4 and sys.argv[4] == 'mip'
w, n = load(path); out, info = analyse(w, n)
chs = chains_of(info, n); q = len(chs); D = q; H = q + 1; V = q + 2
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
byprefix = {}
for b, (t, _, _) in enumerate(chs):
    for j in range(1, n): byprefix.setdefault(t[:j], []).append(b)
arcs = []
for a, (_, e, _) in enumerate(chs):
    seen = set()
    for j in range(n - 1, 0, -1):
        for b in byprefix.get(e[n - j:], []):
            if b == a or b in seen: continue
            seen.add(b); arcs.append((a, b, cost(e, chs[b][0], n) - 3))
    arcs.append((a, H, n - 3)); arcs.append((a, D, 0))
for b in range(q): arcs.append((H, b, 0)); arcs.append((D, b, 0))
A = len(arcs)
# reference route (the input word's own chain order) as an arc-incidence vector, for cut validation
ref_arcs = set([(D, 0)] + [(a, a + 1) for a in range(q - 1)] + [(q - 1, D)])
tail = np.array([a for a, _, _ in arcs]); head = np.array([b for _, b, _ in arcs]); cst = np.array([c for _, _, c in arcs], float)
h = highspy.Highs(); h.setOptionValue("output_flag", False)
inf = highspy.kHighsInf
lp = highspy.HighsLp()
lp.num_col_ = A; lp.col_cost_ = cst; lp.col_lower_ = np.zeros(A); lp.col_upper_ = np.array([inf if (a == H or b == H) else 1.0 for a, b, _ in arcs])
h.passModel(lp)
out_of = [[] for _ in range(V)]; in_of = [[] for _ in range(V)]
for i, (a, b, _) in enumerate(arcs): out_of[a].append(i); in_of[b].append(i)
for v in range(V):
    if v == H:
        idx = out_of[v] + in_of[v]; val = [1.0] * len(out_of[v]) + [-1.0] * len(in_of[v])
        h.addRow(0, 0, len(idx), np.array(idx, dtype=np.int32), np.array(val))
    else:
        h.addRow(1, 1, len(out_of[v]), np.array(out_of[v], dtype=np.int32), np.ones(len(out_of[v])))
        h.addRow(1, 1, len(in_of[v]), np.array(in_of[v], dtype=np.int32), np.ones(len(in_of[v])))
cuts = 0; t0 = time.time(); val = None
for it in range(maxit):
    h.run(); sol = h.getSolution(); x = np.array(sol.col_value); val = h.getInfo().objective_function_value
    G = nx.DiGraph()
    G.add_nodes_from(range(V))
    for i in np.nonzero(x > 1e-9)[0]:
        a, b = int(tail[i]), int(head[i])
        G.add_edge(a, b, capacity=G[a][b]["capacity"] + x[i] if G.has_edge(a, b) else x[i])
    new = []
    # integral-style violations: nodes that cannot reach D at all
    R = nx.ancestors(G, D) | {D}
    unreached = set(range(V)) - R
    seen_sets = set()
    if unreached:
        for comp in nx.strongly_connected_components(G.subgraph(unreached)):
            S = set(comp)
            if not any(v < q for v in S): continue          # the hub alone need not reach the depot
            for v in list(S): S |= nx.descendants(G, v)
            S = frozenset(S - {D})
            if D not in S and S not in seen_sets: seen_sets.add(S); new.append(S)
    else:
        # fractional separation: min cut v -> D for a sample of nodes (one per weakly-connected piece)
        for v in range(0, q, STRIDE):
            cv, (Sset, _) = nx.minimum_cut(G, v, D)
            if cv < 1 - 1e-6:
                S = frozenset(Sset)
                if S not in seen_sets: seen_sets.add(S); new.append(S)
    if not new: break
    for S in new:
        idx = [i for i in range(A) if tail[i] in S and head[i] not in S]
        ref_out = sum(1 for (a, b) in ref_arcs if a in S and b not in S)
        if ref_out < 1: print(json.dumps(dict(INVALID_CUT=True, size=len(S), has_H=H in S, has_D=D in S, ref_out=ref_out)), flush=True)
        h.addRow(1, inf, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
        cuts += 1
    print(json.dumps(dict(it=it, lp=val, new_cuts=len(new), cuts=cuts, sec=round(time.time() - t0, 1))), flush=True)
base = CONST - ORB + q
print(json.dumps(dict(final_lp=val, cuts=cuts, length_lower_bound=base + math.ceil(val - 1e-6), base=base, sec=round(time.time() - t0, 1))), flush=True)
if MIP:
    # branch-and-cut by re-solving the MIP with all binary chain arcs and adding violated subtour cuts
    integ = [highspy.HighsVarType.kInteger] * A
    h.changeColsIntegrality(A, np.arange(A, dtype=np.int32), np.array(integ))
    h.setOptionValue("time_limit", float(os.environ.get("MIPTL", "1800")))
    h.setOptionValue("mip_rel_gap", 0.0)
    for rnd in range(50):
        h.run(); info_ = h.getInfo(); x = np.array(h.getSolution().col_value)
        st = h.modelStatusToString(h.getModelStatus())
        G = nx.DiGraph(); G.add_nodes_from(range(V))
        for i in np.nonzero(x > 0.5)[0]: G.add_edge(int(tail[i]), int(head[i]))
        R = nx.ancestors(G, D) | {D}; unreached = set(range(V)) - R
        if not any(v < q for v in unreached): unreached = set()
        print(json.dumps(dict(mip_round=rnd, status=st, obj=info_.objective_function_value, bound=info_.mip_dual_bound,
                              unreached=len(unreached), sec=round(time.time() - t0, 1))), flush=True)
        if not unreached or st != "Optimal": break
        for comp_ in nx.weakly_connected_components(G.subgraph(unreached)):
            S = set(comp_)
            if not any(v < q for v in S): continue
            idx = [i for i in range(A) if tail[i] in S and head[i] not in S]
            h.addRow(1, inf, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    print(json.dumps(dict(final_mip_obj=info_.objective_function_value, final_mip_bound=info_.mip_dual_bound,
                          length_lower_bound_mip=base + math.ceil(info_.mip_dual_bound - 1e-6), status=st)), flush=True)
