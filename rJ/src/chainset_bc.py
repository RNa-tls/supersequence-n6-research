#!/usr/bin/env python3
"""Round J -- certified branch-and-cut for the chain-ordering problem (model: chainset_model.py).

Goal: decide whether some route on the chain set has weight <= T-1 (then a shorter word exists), or
prove weight >= T for all routes.  Output: a certificate that chainset_check.py verifies with exact
rational arithmetic, independently of the LP solver.

Bound used everywhere (weak duality, all variables binary):  for any y with y_cut >= 0,
    w.x >= y.b + sum_j r_j x_j >= y.b + sum_{j free} min(0, r_j) + sum_{j fixed 1} r_j,
    r = w - A^T y,  over the node's constraints (degree rows, pool cuts, fixings).
Root reduced-cost fixing: x_j = 0 whenever LB_root + r_j > T - 1 (then no solution of weight
<= T-1 uses arc j).  Cuts are subtour cuts x(delta^+(S)) >= 1, D not in S, S contains a chain;
every new cut is additionally tested against reference routes (any ordering is a valid route)."""
import sys, os, json, math, time, random
import numpy as np
import highspy
import networkx as nx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model, reference_orders

EPS = 1e-7

class BC:
    def __init__(self, M, T, refs, log=print):
        self.M, self.T, self.log = M, T, log
        A = len(M.arcs); self.A = A
        self.tail = np.array([a for a, _, _ in M.arcs]); self.head = np.array([b for _, b, _ in M.arcs])
        self.w = np.array([c for _, _, c in M.arcs], dtype=float)
        self.ref_t = [self.tail[np.array(M.route_arcs(o))] for o in refs]
        self.ref_h = [self.head[np.array(M.route_arcs(o))] for o in refs]
        self.pool = []; self.pool_keys = set()
        h = highspy.Highs(); h.setOptionValue("output_flag", False)
        h.setOptionValue("primal_feasibility_tolerance", 1e-9); h.setOptionValue("dual_feasibility_tolerance", 1e-9)
        lp = highspy.HighsLp(); lp.num_col_ = A; lp.col_cost_ = self.w
        lp.col_lower_ = np.zeros(A); lp.col_upper_ = np.ones(A)
        h.passModel(lp); self.h = h
        self.rows_b = []           # (lo) for each row; degree rows are equalities
        q, D, H = M.q, M.D, M.H
        self.deg_rows = 0
        for v in range(M.V):
            if v == H:
                idx = M.out_of[v] + M.in_of[v]; val = [1.0] * len(M.out_of[v]) + [-1.0] * len(M.in_of[v])
                h.addRow(0, 0, len(idx), np.array(idx, dtype=np.int32), np.array(val)); self.rows_b.append(("eq", 0.0, ("H",)))
            else:
                h.addRow(1, 1, len(M.out_of[v]), np.array(M.out_of[v], dtype=np.int32), np.ones(len(M.out_of[v]))); self.rows_b.append(("eq", 1.0, ("out", v)))
                h.addRow(1, 1, len(M.in_of[v]), np.array(M.in_of[v], dtype=np.int32), np.ones(len(M.in_of[v]))); self.rows_b.append(("eq", 1.0, ("in", v)))
        self.deg_rows = len(self.rows_b)
        self.ub = np.ones(A)

    def add_cut(self, S):
        key = frozenset(int(v) for v in S)
        if key in self.pool_keys: return False
        M = self.M
        assert Model.cut_structurally_valid(key, M.q)
        inS = np.zeros(M.V, dtype=bool); inS[list(key)] = True
        for t, hh in zip(self.ref_t, self.ref_h):
            if int(np.sum(inS[t] & ~inS[hh])) < 1:
                raise RuntimeError("INVALID CUT: violated by a reference route")
        idx = np.nonzero(inS[self.tail] & ~inS[self.head])[0]
        self.h.addRow(1, highspy.kHighsInf, len(idx), idx.astype(np.int32), np.ones(len(idx)))
        self.pool.append(sorted(key)); self.pool_keys.add(key); self.rows_b.append(("ge", 1.0, ("cut", len(self.pool) - 1)))
        return True

    def separate(self, x):
        """exact subtour separation with compiled max-flow (scipy): for every chain v, a minimum
        v -> D cut in the support graph (capacities x scaled to integers; any returned set S is a
        structurally valid cut, its violation is re-checked with the float x).
        Representatives: if x(v->u) = 1 then every S containing v but not D has x(delta+(S)) >= 1
        unless u is in S, in which case x(delta+(S)) >= maxflow(u -> D); hence
        maxflow(v -> D) >= min(1, maxflow(u -> D)) and only the end of each x=1 successor path
        (or one node of an x=1 cycle) needs a max-flow computation.  Exact."""
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import maximum_flow, breadth_first_order
        M = self.M; V = M.V; SCL = 10 ** 7
        sup = np.nonzero(x > 1e-9)[0]
        cap = {}
        for i in sup:
            a, b = int(self.tail[i]), int(self.head[i])
            cap[(a, b)] = cap.get((a, b), 0.0) + float(x[i])
        rows = np.array([a for a, b in cap], dtype=np.int32); cols = np.array([b for a, b in cap], dtype=np.int32)
        vals = np.array([max(1, int(math.floor(c * SCL))) for c in cap.values()], dtype=np.int32)
        G = csr_matrix((vals, (rows, cols)), shape=(V, V))
        xa = {k: v for k, v in cap.items()}
        new = 0; covered = set()
        succ1 = {}
        for i in np.nonzero(x > 1 - 1e-9)[0]:
            succ1.setdefault(int(self.tail[i]), int(self.head[i]))
        rep = {}
        for v0 in range(M.q):
            path = []; on = set(); v = v0
            while True:
                if v in rep: r_ = rep[v]; break
                if v == M.D: r_ = M.D; break
                if v in on: r_ = v; break                      # x=1 cycle: any node of it
                if v not in succ1: r_ = v; break
                path.append(v); on.add(v); v = succ1[v]
            for u in path: rep[u] = r_
            rep[v0] = r_
        sources = sorted(set(r_ for r_ in rep.values() if r_ != M.D))
        for v in sources:
            if v in covered: continue
            res = maximum_flow(G, v, M.D)
            if res.flow_value >= SCL - 10: continue
            # residual reachability from v
            F = res.flow.tocsr()
            Rm = (G - F).tocsr(); Rm.data = np.where(Rm.data > 0, Rm.data, 0); Rm.eliminate_zeros()
            back = (-F).tocsr(); back.data = np.where(back.data > 0, back.data, 0); back.eliminate_zeros()
            reach = breadth_first_order(Rm + back, v, directed=True, return_predecessors=False)
            S = set(int(u) for u in reach); S.discard(M.D)
            val = sum(c for (a, b), c in xa.items() if a in S and b not in S)
            if val < 1 - 1e-6 and Model.cut_structurally_valid(S, M.q) and self.add_cut(S): new += 1
            covered |= S
        return new

    def solve_node(self, fix0, fix1, max_rounds=200, prune_above=None):
        """LP with cut rounds.  If prune_above is given, stop as soon as the exact bound from the
        current duals exceeds it (cuts only raise the LP value, so the node is pruned anyway)."""
        ub = self.ub.copy(); lb = np.zeros(self.A)
        for j in fix0: ub[j] = 0.0
        for j in fix1: lb[j] = 1.0
        self.h.changeColsBounds(self.A, np.arange(self.A, dtype=np.int32), lb, ub)
        for rnd in range(max_rounds):
            self.h.run()
            st = self.h.getModelStatus()
            if st != highspy.HighsModelStatus.kOptimal:
                return dict(status=self.h.modelStatusToString(st))
            sol = self.h.getSolution(); x = np.array(sol.col_value)
            if prune_above is not None:
                lbv, _, _ = self.node_bound(np.array(sol.row_dual), fix0, fix1)
                if lbv > prune_above:
                    return dict(status="Optimal", obj=self.h.getInfo().objective_function_value, x=x,
                                y=np.array(sol.row_dual), r=np.array(sol.col_dual), early=True)
            if self.separate(x) == 0:
                return dict(status="Optimal", obj=self.h.getInfo().objective_function_value, x=x,
                            y=np.array(sol.row_dual), r=np.array(sol.col_dual))
        return dict(status="SepLimit")

    SCALE = 2 ** 24

    def row_arcs(self, k):
        """(arc indices, coefficient) of row k."""
        kind, b, tag = self.rows_b[k]; M = self.M
        if tag[0] == "H":
            return [(np.array(M.out_of[M.H]), 1), (np.array(M.in_of[M.H]), -1)]
        if tag[0] == "out": return [(np.array(M.out_of[tag[1]]), 1)]
        if tag[0] == "in": return [(np.array(M.in_of[tag[1]]), 1)]
        S = self.pool[tag[1]]; inS = np.zeros(M.V, dtype=bool); inS[S] = True
        return [(np.nonzero(inS[self.tail] & ~inS[self.head])[0], 1)]

    def node_bound(self, y, fix0, fix1):
        """EXACT integer bound with dyadic duals y_int / SCALE (ge-row duals clipped at 0):
           LB*SCALE = sum_k y_k b_k + sum_{free} min(0, r_j) + sum_{fixed 1} r_j,  r = w*SCALE - A^T y."""
        SC = self.SCALE
        yi = np.round(np.asarray(y, dtype=float) * SC).astype(np.int64)
        for k, (kind, b, _) in enumerate(self.rows_b):
            if kind == "ge" and yi[k] < 0: yi[k] = 0
        aty = np.zeros(self.A, dtype=np.int64)
        for k in np.nonzero(yi)[0]:
            for idx, coef in self.row_arcs(int(k)):
                aty[idx] += coef * yi[k]
        r = self.w.astype(np.int64) * SC - aty
        yb = int(sum(int(yi[k]) * int(round(self.rows_b[k][1])) for k in np.nonzero(yi)[0]))
        free = np.ones(self.A, dtype=bool)
        if fix0: free[list(fix0)] = False
        if fix1: free[list(fix1)] = False
        lb = yb + int(np.sum(np.minimum(0, r[free]))) + (int(np.sum(r[list(fix1)])) if fix1 else 0)
        return lb, r, yi            # lb is an integer = SCALE * bound

def main():
    path, T = sys.argv[1], int(sys.argv[2]); out = sys.argv[3]; tlimit = float(sys.argv[4]) if len(sys.argv) > 4 else 36000
    w, n = load_word(path); ch = chains_from_word(w, n); M = Model(ch, n)
    word_order = list(range(M.q))
    refs = reference_orders(M, word_order)
    logf = open(out + ".log", "w")
    def log(*a):
        s = " ".join(str(x) for x in a); print(s, flush=True); logf.write(s + "\n"); logf.flush()
    bc = BC(M, T, refs, log)
    t0 = time.time()
    if os.environ.get("INIT_POOL"):
        for S in json.load(open(os.environ["INIT_POOL"]))["pool"]: bc.add_cut(S)
    init = json.loads(os.environ.get("INIT_FIX", "[]"))          # [[arc, 0/1], ...] fixings of this subtree's root
    if0 = [int(a) for a, v in init if v == 0]; if1 = [int(a) for a, v in init if v == 1]
    if os.environ.get("GLOBAL_FIX0"):                            # global root fixings validated by the top certificate
        gf = json.load(open(os.environ["GLOBAL_FIX0"]))["root"]["fixed0"]
    else: gf = None
    root = bc.solve_node([], [])
    lb_root, r_root, y_root = bc.node_bound(root["y"], [], [])
    SC = bc.SCALE; THR = (T - 1) * SC
    log(json.dumps(dict(stage="root", lp=root["obj"], lb_exact=lb_root / SC, cuts=len(bc.pool), sec=round(time.time() - t0, 1))))
    fixed0 = [int(j) for j in range(bc.A) if r_root[j] > 0 and lb_root + int(r_root[j]) > THR]
    if gf is not None: fixed0 = [int(j) for j in gf]
    log(json.dumps(dict(stage="rc_fixing", fixed_to_zero=len(fixed0), remaining=bc.A - len(fixed0))))
    rootcert = dict(y=[(int(k), int(v)) for k, v in enumerate(y_root) if v != 0], ncuts=len(bc.pool), fixed0=fixed0, lb_scaled=int(lb_root))
    if os.environ.get("ROOT_ONLY") == "1":
        json.dump(dict(word=os.path.basename(path), n=n, T=T, BASE=M.BASE, SCALE=SC, arcs=[(int(a), int(b), int(c)) for a, b, c in M.arcs],
                       root=rootcert, pool=bc.pool, rows=[(kind, b, list(tag)) for kind, b, tag in bc.rows_b], nodes=[], complete=False, incumbent=None),
                  open(out, "w"))
        log(json.dumps(dict(stage="root_only_written", file=out))); return
    # depth-first B&B on the reduced problem
    nodes = []          # records: dict(id, parent, var, val, kind, ncuts, y (sparse) , lb)
    stack = [(0, None, None, None, if0, if1)]; nid = 0; best = None
    FRONTIER = int(os.environ.get("FRONTIER", "0")); frontier = []
    NODE_LIMIT = int(os.environ.get("NODE_LIMIT", "1000000000"))     # testing aid: behave as on a time limit after this many nodes
    gfix0 = set(fixed0)
    while stack:
        if time.time() - t0 > tlimit or len(nodes) >= NODE_LIMIT:
            log("TIME LIMIT")
            if os.environ.get("DELEGATE_ON_TIMEOUT", "1") == "1":
                # keep the work done so far: every open node becomes a delegated leaf (closed later by its own certificate)
                for (my_, parent_, var_, val_, f0_, f1_) in stack:
                    nodes.append(dict(id=my_, parent=parent_, var=var_, val=val_, kind="delegated", fix=[[a, 0] for a in f0_] + [[a, 1] for a in f1_]))
                    frontier.append(dict(id=my_, fix=[[a, 0] for a in f0_] + [[a, 1] for a in f1_]))
                stack = []
            break
        if FRONTIER and len(stack) >= FRONTIER:
            # breadth-first top tree: delegate all open nodes as subtrees
            for (my_, parent_, var_, val_, f0_, f1_) in stack:
                nodes.append(dict(id=my_, parent=parent_, var=var_, val=val_, kind="delegated", fix=[[a, 0] for a in f0_] + [[a, 1] for a in f1_]))
                frontier.append(dict(id=my_, fix=[[a, 0] for a in f0_] + [[a, 1] for a in f1_]))
            stack = []; break
        my, parent, var, val, f0, f1 = (stack.pop(0) if FRONTIER else stack.pop())
        res = bc.solve_node(sorted(gfix0 | set(f0)), f1, prune_above=THR)
        rec = dict(id=my, parent=parent, var=var, val=val, ncuts=len(bc.pool))
        if res["status"] != "Optimal":
            # infeasible LP: use a scaled dual ray as the certificate (handled by the same bound formula)
            rec.update(kind="infeasible_lp", status=res["status"])
            ray_ok, ray = bc.h.getDualRay()
            done_ = False
            if ray_ok:
                ray = np.array(ray); ray = ray / max(1e-12, np.max(np.abs(ray)))
                for sgn in (1, -1):
                    for tsc in (1e2, 1e3, 1e4):
                        lbv, _, ycl = bc.node_bound(sgn * tsc * ray, sorted(gfix0 | set(f0)), f1)
                        if lbv > THR:
                            rec.update(lb_scaled=int(lbv), y=[(int(k), int(v)) for k, v in enumerate(ycl) if v != 0]); done_ = True; break
                    if done_: break
            if not done_:
                raise RuntimeError("infeasible node without a usable Farkas certificate")
            nodes.append(rec)
            log(json.dumps(dict(node=my, status=res["status"], lb=rec.get("lb"), depth=len(f0) + len(f1))))
            continue
        lbv, r, ycl = bc.node_bound(res["y"], sorted(gfix0 | set(f0)), f1)
        x = res["x"]
        frac = [j for j in np.nonzero((x > 1e-6) & (x < 1 - 1e-6))[0]]
        if lbv > THR:
            rec.update(kind="pruned", lb_scaled=int(lbv), y=[(int(k), int(v)) for k, v in enumerate(ycl) if v != 0])
            nodes.append(rec)
            log(json.dumps(dict(node=my, pruned=True, lp=round(res["obj"], 6), lb=round(lbv / SC, 6), depth=len(f0) + len(f1), open=len(stack), cuts=len(bc.pool), sec=round(time.time() - t0))))
            continue
        if not frac:
            # integral and cut-feasible: a genuine route of weight res["obj"] <= T-1 !
            rec.update(kind="INCUMBENT", obj=res["obj"]); nodes.append(rec)
            sel = [int(j) for j in np.nonzero(x > 0.5)[0]]
            best = (res["obj"], sel)
            log(json.dumps(dict(node=my, INCUMBENT=res["obj"])))
            break
        j = max(frac, key=lambda j: (0.5 - abs(x[j] - 0.5)))
        rec.update(kind="branch", branch_var=int(j), lp=res["obj"]); nodes.append(rec)
        nid += 1; c0 = nid; nid += 1; c1 = nid
        stack.append((c0, my, int(j), 0, f0 + [int(j)], f1))
        stack.append((c1, my, int(j), 1, f0, f1 + [int(j)]))
        log(json.dumps(dict(node=my, branch=int(j), x=round(float(x[j]), 4), lp=round(res["obj"], 6), depth=len(f0) + len(f1), open=len(stack), cuts=len(bc.pool), sec=round(time.time() - t0))))
    complete = (not stack) and best is None and not frontier
    if frontier:
        json.dump(dict(frontier=frontier), open(out + ".frontier.json", "w"))
    cert = dict(init_fix=init, frontier=[f["id"] for f in frontier], word=os.path.basename(path), n=n, T=T, BASE=M.BASE, SCALE=SC, arcs=[(int(a), int(b), int(c)) for a, b, c in M.arcs], root=rootcert, pool=bc.pool,
                rows=[(kind, b, list(tag)) for kind, b, tag in bc.rows_b], nodes=nodes, complete=complete,
                incumbent=best)
    json.dump(cert, open(out, "w"))
    log(json.dumps(dict(stage="done", complete=complete, nodes=len(nodes), cuts=len(bc.pool), incumbent=None if best is None else best[0],
                        claim=("all routes on this chain set have weight >= %d, length >= %d" % (T, M.BASE + T)) if complete else "UNDECIDED",
                        sec=round(time.time() - t0, 1))))

if __name__ == "__main__":
    main()
