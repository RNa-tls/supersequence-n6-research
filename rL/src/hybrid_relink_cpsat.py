#!/usr/bin/env python3
"""Round L -- CP-SAT version of the hybrid relinking GTSP (see hybrid_relink.py for the model).

Cluster level: AddCircuit over the closed trails + a depot (a Hamiltonian path of clusters).
Node level: exactly one cut edge (node) per cluster; a used cluster arc T -> T' must be realised by
exactly one node-level boundary arc from the chosen node of T to the chosen node of T'.
Objective: sum boundary weights - sum cut weights;  L = const + objective (exact).
usage: hybrid_relink_cpsat.py WORD [EXC] [timelimit] [workers] [--both]"""
import sys, os, json, time, itertools
from collections import defaultdict
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hybrid_relink as H

def main():
    path = sys.argv[1]; EXC = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    tl = float(sys.argv[3]) if len(sys.argv) > 3 else 3600; workers = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    BOTH = "--both" in sys.argv
    t0 = time.time()
    seqs, L0, K, alt = H.closed_trails(path)
    T = len(seqs)
    const = 8 + sum(9 * (len(s) // 8) for s in seqs) + K
    nodes = []; nid = {}; versions = []
    for ti, s in enumerate(seqs):
        vs = [s] + ([alt[ti]] if BOTH and alt[ti] is not None else [])
        for s_ in vs:
            vi = len(versions); versions.append((ti, s_))
            for i in range(len(s_)):
                nid.setdefault(s_[i], []).append(len(nodes))
                nodes.append((ti, s_[i], s_[i - 1], H.wt(s_[i - 1], s_[i]), vi, i))
    arcs = []
    for a, (ta, entry, exitp, ca, va, ia) in enumerate(nodes):
        u = exitp
        for w_ in range(2, 5 + EXC):
            for perm in itertools.permutations(u[:w_]):
                v = u[w_:] + perm
                if H.wt(u, v) != w_: continue
                for b in nid.get(v, []):
                    if nodes[b][0] == ta: continue
                    if w_ - nodes[b][3] - 1 <= EXC: arcs.append((a, b, w_))
    # nodes without any arc can still be first (no in-arc) or last (no out-arc); keep all
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in nodes]
    by_cl = defaultdict(list)
    for j, nd in enumerate(nodes): by_cl[nd[0]].append(j)
    for ti in range(T): m.AddExactlyOne([y[j] for j in by_cl[ti]])
    x = [m.NewBoolVar("") for _ in arcs]
    outs = defaultdict(list); ins = defaultdict(list); pair = defaultdict(list)
    for i, (a, b, w_) in enumerate(arcs):
        outs[a].append(i); ins[b].append(i); pair[(nodes[a][0], nodes[b][0])].append(i)
    for j in range(len(nodes)):
        if outs[j]: m.Add(sum(x[i] for i in outs[j]) <= y[j])
        if ins[j]: m.Add(sum(x[i] for i in ins[j]) <= y[j])
    D = T
    circ = []
    z = {}
    for (ta, tb), lst in pair.items():
        z[(ta, tb)] = m.NewBoolVar("")
        m.Add(sum(x[i] for i in lst) == z[(ta, tb)])
        circ.append((ta, tb, z[(ta, tb)]))
    for ti in range(T):
        s_ = m.NewBoolVar(""); e_ = m.NewBoolVar("")
        circ.append((D, ti, s_)); circ.append((ti, D, e_))
    m.AddCircuit(circ)
    m.Minimize(sum(w_ * x[i] for i, (a, b, w_) in enumerate(arcs)) - sum(nodes[j][3] * y[j] for j in range(len(nodes))))
    print(json.dumps(dict(clusters=T, nodes=len(nodes), arcs=len(arcs), cluster_pairs=len(pair), const=const,
                          both=BOTH, build_sec=round(time.time() - t0, 1))), flush=True)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(s): super().__init__()
        def on_solution_callback(s):
            print(json.dumps(dict(sol=const + s.ObjectiveValue(), bound=const + s.BestObjectiveBound(),
                                  sec=round(time.time() - t0, 1))), flush=True)
    st = sv.Solve(m, CB())
    res = dict(status=sv.StatusName(st), best=(const + sv.ObjectiveValue()) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
               bound=const + sv.BestObjectiveBound(), exc=EXC, both=BOTH, sec=round(time.time() - t0, 1))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {}
        for i, (a, b, w_) in enumerate(arcs):
            if sv.Value(x[i]): succ[a] = b
        chosen = [j for j in range(len(nodes)) if sv.Value(y[j])]
        has_in = {b for b in succ.values()}
        start = [j for j in chosen if j not in has_in][0]
        order = [start]
        while order[-1] in succ: order.append(succ[order[-1]])
        assert len(order) == T
        route = []
        for j in order:
            ti, entry, exitp, c, vi, i0 = nodes[j]
            s_ = versions[vi][1]; route += s_[i0:] + s_[:i0]
        assert len(route) == 40320 and len(set(route)) == 40320
        Lm = 8 + sum(H.wt(route[i], route[i + 1]) for i in range(len(route) - 1))
        res["measured"] = Lm
        res["cut_weights"] = {str(k): sum(1 for j in order if nodes[j][3] == k) for k in (1, 2, 3)}
        word = list(route[0])
        for p_, q_ in zip(route, route[1:]):
            c = H.wt(p_, q_); word += list(q_[8 - c:])
        assert len(word) == Lm
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"hybrid_cpsat_{Lm}{'_both' if BOTH else ''}.txt")
        open(out, "w").write("".join(str(c + 1) for c in word) + "\n"); res["file"] = out
    print(json.dumps(res), flush=True)
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"hybrid_cpsat_exc{EXC}{'_both' if BOTH else ''}.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
