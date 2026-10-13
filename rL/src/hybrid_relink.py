#!/usr/bin/env python3
"""Round L (sections 19, 22-25) -- HYBRID RELINKING of a fixed family of closed trails, allowing r > 0.

Input: an r = 0 word whose chain set decomposes into closed trails (cycles of chains joined by cost-3
joins; for the 46187 word: 6 A-bundles + 24 phi-cycles).  Each closed trail T is a cyclic sequence of
8|T| permutations with edge weights 1 (inside runs), 2 (F-steps) and 3 (cost-3 joins).
A route visiting every closed trail in ONE piece cuts each cyclic sequence at one edge e_T and joins
the opened trails in some order:
        L = 8 + sum_T (9|T| + k_T) + sum_boundaries w_b - sum_T w(e_T)          (exact)
Cutting a weight-3 edge is the r = 0 opening; cutting a weight-2 edge breaks a chain; cutting a
weight-1 edge splits a run (r > 0, R_extra + 1).  The ideal 'r = 0 with perfect linking' value is
46162 for the 46187 family; the r = 0 route itself pays 25 more (two extra breaks + lambda = 23).
This script builds the generalized TSP (cluster = closed trail, node = cut edge, arc = boundary join
of weight <= WMAX[cut type]) and solves it EXACTLY with HiGHS + lazy cluster subtour elimination,
or reports the best found.  Any route found is rebuilt and measured from scratch.
With --both every phi-cycle cluster may also be traversed in its other world (same 42 classes).
usage: hybrid_relink.py WORD [EXC] [timelimit] [--both]   (EXC = allowed excess over ideal per arc)"""
import sys, os, json, time, itertools, math
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r0_decompose as RD

n = 8
def R(p, k=1):
    k %= n; return p[k:] + p[:k]
def wt(x, y):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n

def closed_trails(path):
    w = RD.load(path); starts = RD.runs_of(w)
    J, chains, cj, jt = RD.decompose(starts)
    trails = [[0]]
    for k, c in enumerate(cj):
        if c == 3: trails[-1].append(k + 1)
        else: trails.append([k + 1])
    def closes(seq):
        x = chains[seq[-1]]["lastp"]; t = chains[seq[0]]["first"]
        return any(x[2:7] + tuple(x[i] for i in s) == t for s in [(1,0,7),(0,1,7),(0,7,1),(1,7,0),(7,1,0)])
    closed = []; pending = []
    for t in trails:
        if closes(t): closed.append(t)
        else: pending.append(t)
    # glue pending pieces into cycles (pieces of one closed trail)
    while pending:
        cur = pending.pop(0); found = True
        while not closes(cur) and found:
            found = False
            for i, t in enumerate(pending):
                x = chains[cur[-1]]["lastp"]; s0 = chains[t[0]]["first"]
                if any(x[2:7] + tuple(x[i_] for i_ in s) == s0 for s in [(1,0,7),(0,1,7),(0,7,1),(1,7,0),(7,1,0)]):
                    cur = cur + t; pending.pop(i); found = True; break
        assert closes(cur), "could not close a trail"
        closed.append(cur)
    seqs = []; alt = []
    for t in closed:
        perms = []
        for k in t:
            p = chains[k]["first"]
            for c in range(chains[k]["l"]):
                q = p
                for _ in range(c): q = q[1:7] + q[:1] + q[7:]
                perms += [R(q, j) for j in range(n)]
        seqs.append(perms)
        alt.append(None)
        if len(t) == 6 and all(chains[k]["l"] == 7 for k in t):
            # the same phi-set traversed in the other world: special b = moving symbol, partner a
            p0 = chains[t[0]]["first"]; a, b = p0[7], p0[6]
            # a run start with special b and a immediately before b, inside the same phi-set
            cls0 = set(); 
            for q in perms: cls0.add(min(R(q, j) for j in range(n)))
            start = None
            for q in perms:
                if q[7] == b and q[6] == a: start = q; break
            if start is None:
                for q in perms:
                    for j in range(n):
                        r_ = R(q, j)
                        if r_[7] == b and r_[6] == a: start = r_; break
                    if start: break
            other = []; x = start
            for c in range(6):
                q = x
                for i in range(7):
                    other += [R(q, j) for j in range(n)]
                    if i < 6: q = q[1:7] + q[:1] + q[7:]
                x = q[2:7] + (q[1], q[0], q[7])
            assert x == start and len(set(other)) == 336 and set(other) == set(perms), "alt world phi-cycle"
            alt[-1] = other
    return seqs, len(w), sum(len(t) for t in closed), alt

def all_versions(seqs, cache=None):
    """for every closed trail, all distinct relabelled copies g.T (g in S_8) with the same class set
    (the stabiliser images); returns a list of lists of cyclic perm sequences (first = original).
    Cached in `cache` (pickle) when given."""
    import pickle
    if cache and os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    canon = lambda p: min(p[j:] + p[:j] for j in range(n))
    out = []
    for s in seqs:
        S = frozenset(canon(p) for p in s)
        starts0 = frozenset(s[i] for i in range(0, len(s), 8))
        vers = [s]; seen = {starts0}
        for g in itertools.permutations(range(n)):
            # quick reject: image of one class must be in S
            if canon(tuple(g[x] for x in s[0])) not in S: continue
            img = [tuple(g[x] for x in p) for p in s]
            if frozenset(canon(p) for p in img) != S: continue
            st = frozenset(img[i] for i in range(0, len(img), 8))
            if st in seen: continue
            seen.add(st); vers.append(img)
        out.append(vers)
    if cache: pickle.dump(out, open(cache, "wb"))
    return out

def main():
    import highspy
    path = sys.argv[1]; EXC = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    tl = float(sys.argv[3]) if len(sys.argv) > 3 else 3600
    t0 = time.time()
    seqs, L0, K, alt = closed_trails(path)
    BOTH = "--both" in sys.argv
    T = len(seqs)
    const = 8 + sum(9 * (len(s) // 8) for s in seqs) + K
    # options: (cluster, version, entry perm, exit perm, cut weight); entry perms index nodes per version
    nodes = []; nid = {}           # nid: perm -> list of node ids (one per version containing it)
    versions = []                  # (cluster, sequence)
    for ti, s in enumerate(seqs):
        vs = [s] + ([alt[ti]] if BOTH and alt[ti] is not None else [])
        for s_ in vs:
            vi = len(versions); versions.append((ti, s_))
            m = len(s_)
            for i in range(m):
                nid.setdefault(s_[i], []).append(len(nodes)); nodes.append((ti, s_[i], s_[i - 1], wt(s_[i - 1], s_[i]), vi, i))
    # arcs: exit perm u of node a -> entry perm v of node b (other cluster), weight w, kept if w - cut(b) - 1 <= EXC
    arcs = []
    for a, (ta, entry, exitp, ca, va, ia) in enumerate(nodes):
        u = exitp
        for w_ in range(2, 5 + EXC):
            for perm in itertools.permutations(u[:w_]):
                v = u[w_:] + perm
                if wt(u, v) != w_: continue
                for b in nid.get(v, []):
                    if nodes[b][0] == ta: continue
                    if w_ - nodes[b][3] - 1 <= EXC: arcs.append((a, b, w_))
    print(json.dumps(dict(closed_trails=T, sizes=sorted(len(s) // 8 for s in seqs), nodes=len(nodes), arcs=len(arcs),
                          const=const, ideal=const + (T - 1) - 3, build_sec=round(time.time() - t0, 1))), flush=True)
    # MIP: x arcs, y nodes, s/t start/end
    N = len(nodes); A = len(arcs)
    ncol = A + 3 * N
    # columns: x[0..A), y[A..A+N), s[A+N..A+2N), t[A+2N..A+3N)
    cost = np.zeros(ncol)
    for i, (a, b, w_) in enumerate(arcs): cost[i] = w_
    for j in range(N): cost[A + j] = -nodes[j][3]
    rows = []      # (indices, values, lo, hi)
    inc = defaultdict(list); out = defaultdict(list)
    for i, (a, b, w_) in enumerate(arcs): out[a].append(i); inc[b].append(i)
    for j in range(N):
        rows.append(([i for i in inc[j]] + [A + N + j, A + j], [1.0] * len(inc[j]) + [1.0, -1.0], 0.0, 0.0))
        rows.append(([i for i in out[j]] + [A + 2 * N + j, A + j], [1.0] * len(out[j]) + [1.0, -1.0], 0.0, 0.0))
    for ti in range(T):
        js = [j for j in range(N) if nodes[j][0] == ti]
        rows.append(([A + j for j in js], [1.0] * len(js), 1.0, 1.0))
    rows.append(([A + N + j for j in range(N)], [1.0] * N, 1.0, 1.0))
    rows.append(([A + 2 * N + j for j in range(N)], [1.0] * N, 1.0, 1.0))
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    h.setOptionValue("mip_rel_gap", 0.0)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows)
    lp.col_cost_ = cost; lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.ones(ncol)
    lp.row_lower_ = np.array([r[2] for r in rows]); lp.row_upper_ = np.array([r[3] for r in rows])
    # row-wise matrix
    starts = [0]; idx = []; val = []
    for r in rows:
        idx += r[0]; val += r[1]; starts.append(len(idx))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(starts, dtype=np.int32); lp.a_matrix_.index_ = np.array(idx, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(val)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * ncol
    h.passModel(lp)
    best = None; it = 0
    while True:
        it += 1
        h.setOptionValue("time_limit", max(10.0, tl - (time.time() - t0)))
        h.run()
        st = h.modelStatusToString(h.getModelStatus())
        sol = h.getSolution().col_value
        info = h.getInfo()
        if not len(sol): print(json.dumps(dict(iter=it, status=st))); break
        used = [i for i in range(A) if sol[i] > 0.5]
        ys = [j for j in range(N) if sol[A + j] > 0.5]
        succ = {arcs[i][0]: arcs[i][1] for i in used}
        start = [j for j in range(N) if sol[A + N + j] > 0.5][0]
        # follow the path from start; clusters not reached form subtours
        order = [start]; cur = start
        while cur in succ: cur = succ[cur]; order.append(cur)
        reached = {nodes[j][0] for j in order}
        obj = info.objective_function_value
        print(json.dumps(dict(iter=it, status=st, objective=obj, L_if_path=const + obj, path_clusters=len(reached),
                              bound=const + info.mip_dual_bound, sec=round(time.time() - t0, 1))), flush=True)
        if len(reached) == T:
            best = (obj, order); break
        # add SEC for every cycle among the remaining nodes
        rem = [j for j in ys if nodes[j][0] not in reached]
        seen = set(); added = 0
        for j in rem:
            if j in seen: continue
            cyc = []; cur = j
            while cur not in seen:
                seen.add(cur); cyc.append(cur); cur = succ.get(cur)
                if cur is None: break
            S = {nodes[c][0] for c in cyc}
            inside = [i for i, (a, b, w_) in enumerate(arcs) if nodes[a][0] in S and nodes[b][0] in S]
            h.addRow(-highspy.kHighsInf, float(len(S) - 1), len(inside), np.array(inside, dtype=np.int32), np.ones(len(inside)))
            added += 1
        if time.time() - t0 > tl or added == 0: break
    if best is None: return
    obj, order = best
    route = []
    for j in order:
        ti, entry, exitp, c, vi, i0 = nodes[j]
        s = versions[vi][1]
        route += s[i0:] + s[:i0]
    assert len(route) == 40320 and len(set(route)) == 40320
    Lm = n + sum(wt(route[i], route[i + 1]) for i in range(len(route) - 1))
    word = list(route[0])
    for x, y in zip(route, route[1:]):
        c = wt(x, y); word += list(y[n - c:])
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"hybrid_{Lm}.txt")
    open(out, "w").write("".join(str(c + 1) for c in word) + "\n")
    cuts = {}
    for j in order: cuts[nodes[j][3]] = cuts.get(nodes[j][3], 0) + 1
    print(json.dumps(dict(predicted=const + obj, measured=Lm, word_len=len(word), cut_weights=cuts, file=out)), flush=True)

if __name__ == "__main__":
    main()
