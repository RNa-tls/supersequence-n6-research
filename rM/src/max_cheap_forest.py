#!/usr/bin/env python3
"""Round M -- maximum number of CHEAP arcs in a consistent linear forest (MIP, exact).

Given a set of trails U (default: the 24 phi-cycles) and an excess threshold K, compute
    M_K(U) = max #arcs a = (o -> o') with e(a) <= K between trails of U
such that every trail of U uses ONE opening option, every option has at most one cheap in-arc and
one cheap out-arc and only if chosen, and the chosen arcs form vertex-disjoint PATHS at the trail
level (no cycles; lazy subtour elimination on integer solutions).
In every single-opening word the cheap arcs between trails of U form such a forest, so
    sum_{a in word, both ends in U, e(a) <= K} 1  <=  M_K(U)
is a valid inequality (used as an aggregate cut by single_opening_lp.py --cuts).
usage: max_cheap_forest.py FAMILY.json K [phi|all|A]"""
import sys, os, json, time, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import single_opening_lp as SL

def main():
    import highspy
    fam = json.load(open(sys.argv[1])); K = int(sys.argv[2]); which = sys.argv[3] if len(sys.argv) > 3 else "phi"
    t0 = time.time()
    layers, const, opts, trail_opts, arcs = SL.build(fam, max(K, 0))
    T = len(layers)
    big = {t for t in range(T) if len(layers[t]) > 100}
    U = [t for t in range(T) if (which == "all") or (which == "phi" and t not in big) or (which == "A" and t in big)]
    Us = set(U)
    sel = [i for i, (a, b, e) in enumerate(arcs) if e <= K and opts[a][0] in Us and opts[b][0] in Us]
    used_opts = sorted({arcs[i][0] for i in sel} | {arcs[i][1] for i in sel})
    oi = {o: j for j, o in enumerate(used_opts)}
    NO = len(used_opts); NA = len(sel)
    # columns: y (options used), z (arcs)
    ncol = NO + NA
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("mip_rel_gap", 0.0)
    inf = highspy.kHighsInf
    h.addVars(ncol, np.zeros(ncol), np.ones(ncol))
    h.changeColsCost(ncol, np.arange(ncol, dtype=np.int32), np.concatenate([np.zeros(NO), -np.ones(NA)]))
    h.changeColsIntegrality(ncol, np.arange(ncol, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * ncol))
    by_trail = defaultdict(list)
    for o in used_opts: by_trail[opts[o][0]].append(oi[o])
    for t, js in by_trail.items():
        h.addRow(0.0, 1.0, len(js), np.array(js, dtype=np.int32), np.ones(len(js)))
    outa = defaultdict(list); ina = defaultdict(list); tout = defaultdict(list); tin = defaultdict(list)
    for j, i in enumerate(sel):
        a, b, e = arcs[i]
        outa[oi[a]].append(NO + j); ina[oi[b]].append(NO + j)
        tout[opts[a][0]].append(NO + j); tin[opts[b][0]].append(NO + j)
    for o in range(NO):
        for lst in (outa[o], ina[o]):
            if lst:
                h.addRow(-inf, 0.0, len(lst) + 1, np.array(lst + [o], dtype=np.int32), np.array([1.0] * len(lst) + [-1.0]))
    for t in U:
        for lst in (tout[t], tin[t]):
            if lst: h.addRow(-inf, 1.0, len(lst), np.array(lst, dtype=np.int32), np.ones(len(lst)))
    pair = defaultdict(list)
    for j, i in enumerate(sel):
        a, b, e = arcs[i]; pair[frozenset((opts[a][0], opts[b][0]))].append(NO + j)
    for p, lst in pair.items():                                   # 2-cycles
        h.addRow(-inf, 1.0, len(lst), np.array(lst, dtype=np.int32), np.ones(len(lst)))
    it = 0
    while True:
        it += 1; h.run()
        sol = np.array(h.getSolution().col_value); val = -h.getInfo().objective_function_value
        succ = {}
        for j, i in enumerate(sel):
            if sol[NO + j] > 0.5:
                a, b, e = arcs[i]; succ[opts[a][0]] = opts[b][0]
        # find cycles
        cycles = []; seen = set()
        for s in succ:
            if s in seen: continue
            path = []; x = s; pos = {}
            while x in succ and x not in pos and x not in seen:
                pos[x] = len(path); path.append(x); x = succ[x]
            if x in pos: cycles.append(path[pos[x]:])
            seen |= set(path)
        if not cycles: break
        for cyc in cycles:
            S = set(cyc); lst = [NO + j for j, i in enumerate(sel) if opts[arcs[i][0]][0] in S and opts[arcs[i][1]][0] in S]
            h.addRow(-inf, len(S) - 1, len(lst), np.array(lst, dtype=np.int32), np.ones(len(lst)))
    res = dict(K=K, trails=len(U), which=which, options=NO, arcs=NA, max_arcs=int(round(val)), iterations=it,
               status=h.modelStatusToString(h.getModelStatus()), sec=round(time.time() - t0, 1))
    print(json.dumps(res))

if __name__ == "__main__":
    main()
