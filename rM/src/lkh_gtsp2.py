#!/usr/bin/env python3
"""Round M (sections 11, 14) -- WORLD / VERSION CHOICE as a decision variable: the run-level GTSP
of a family where every class may start at any start it has in ANY version of its trail (1 or 2
choices; mixing versions inside a trail is allowed -- every choice is a valid r = 0 word).
Solved heuristically with LKH (elkai's LKH-3.0.8) after the Noon-Bean transformation:
cluster nodes on a zero-cost cycle a_1 -> a_2 -> ... -> a_1; the original arc (a_i -> y) becomes
(a_{i-1} -> y) with cost + M.  Depot = singleton cluster.  The decoded tour is rebuilt as a word and
measured from scratch.
With --worlds a,b,... the FAMILY argument is ignored and every class may start at its rotation
ending in any listed special symbol (e.g. --worlds 0,7: the full TWO-WORLD r = 0 problem, which
contains every version mix of the 46187 family).
usage: lkh_gtsp2.py FAMILY.json INITWORD [--M 200] [--runs R] [--trials T] [--seed S] [--period P]
                    [--cand K] [--only phi|A|all] [--worlds 0,7] [--tag TAG] [--scratch DIR]"""
import sys, os, json, time, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("family"); ap.add_argument("init")
    ap.add_argument("--M", type=int, default=200); ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--trials", type=int, default=1000); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--period", type=int, default=100); ap.add_argument("--cand", type=int, default=8)
    ap.add_argument("--only", default="all"); ap.add_argument("--tag", default="g2")
    ap.add_argument("--time", type=float, default=0); ap.add_argument("--worlds", default="")
    ap.add_argument("--scratch", default="."); ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs"))
    a = ap.parse_args()
    from elkai import _elkai
    t0 = time.time()
    canon = lambda p: min(p[j:] + p[:j] for j in range(8))
    init = RA.starts_of_word(RA.load_word(a.init))
    opts = {}                                    # class -> list of starts (init start first)
    if a.worlds:
        ws = [int(x) for x in a.worlds.split(",")]
        for s0 in init:
            c = canon(s0); opts[c] = []
            for j in range(8):
                r = s0[j:] + s0[:j]
                if r[7] in ws: opts[c].append(r)
    F = [] if a.worlds else RA.family_versions(a.family)
    for vers in F:
        kind = "phi" if len(vers[0]) == 42 else "A"
        allow = a.only == "all" or a.only == kind
        for v, st in enumerate(vers):
            if v > 0 and not allow: continue
            for s in st: opts.setdefault(canon(s), [])
            for s in st:
                if s not in opts[canon(s)]: opts[canon(s)].append(s)
    for s in init:
        L = opts[canon(s)]
        if s not in L: L.insert(0, s)
        else: L.remove(s); L.insert(0, s)
    cls_order = [canon(s) for s in init]          # initial tour order
    nodes = [None]; cl = [-1]; members = []
    for ci, c in enumerate(cls_order):
        mem = []
        for s in opts[c]: mem.append(len(nodes)); nodes.append(s); cl.append(ci)
        members.append(mem)
    V = len(nodes); N = V - 1
    print(json.dumps(dict(clusters=len(members), nodes=V, two=sum(1 for m in members if len(m) == 2))), flush=True)
    W = RA.weight_matrix(nodes[1:]).astype(np.int16)        # N x N, run i -> run j
    C = np.empty((V, V), dtype=np.int16)
    C[0, :] = a.M; C[:, 0] = a.M; C[0, 0] = 0
    # Noon-Bean: row of node a_i (cluster cycle a_1..a_k) = original row of a_{i+1}, + M
    src = np.arange(1, V)
    for mem in members:
        k = len(mem)
        for i in range(k): src[mem[i] - 1] = mem[(i + 1) % k]
    C[1:, 1:] = W[src - 1, :] + a.M
    for mem in members:
        k = len(mem)
        for x in mem:
            for y in mem: C[x, y] = 10 * a.M        # forbid intra-cluster arcs except the cycle
        for i in range(k):
            C[mem[i], mem[(i + 1) % k]] = 0
    assert C.max() < 10000
    # text: 4 digits + space per entry
    body = np.empty((V, 5 * V), dtype=np.uint8)
    for d, div in enumerate((1000, 100, 10, 1)):
        body[:, d::5] = (C // div % 10 + 48).astype(np.uint8)
    body[:, 4::5] = 32; body[:, -1] = 10
    prob = ("TYPE : ATSP\nDIMENSION : %d\nEDGE_WEIGHT_TYPE : EXPLICIT\nEDGE_WEIGHT_FORMAT : FULL_MATRIX\n"
            "EDGE_WEIGHT_SECTION\n" % V) + body.tobytes().decode() + "EOF\n"
    del body
    tour0 = [0] + [x for mem in members for x in mem]
    tf = os.path.join(a.scratch, "g2init_%s_%d.tour" % (a.tag, os.getpid()))
    open(tf, "w").write("TYPE : TOUR\nDIMENSION : %d\nTOUR_SECTION\n" % V + "\n".join(str(x + 1) for x in tour0) + "\n-1\nEOF\n")
    params = ["PROBLEM_FILE = :stdin:", "RUNS = %d" % a.runs, "SEED = %d" % a.seed, "TRACE_LEVEL = 1",
              "MAX_CANDIDATES = %d" % a.cand, "MAX_TRIALS = %d" % a.trials, "INITIAL_PERIOD = %d" % a.period,
              "INITIAL_TOUR_FILE = %s" % tf]
    if a.time: params.append("TIME_LIMIT = %g" % a.time)
    print(json.dumps(dict(build_sec=round(time.time() - t0, 1), params=params)), flush=True)
    tour = _elkai.solve_problem("\n".join(params) + "\n", prob)
    del prob
    tour = [x - 1 for x in tour]; k = tour.index(0); seq = tour[k + 1:] + tour[:k]
    # decode: clusters must be contiguous; selected start = entry node of each cluster
    starts = []; i = 0; proper = True
    while i < len(seq):
        c = cl[seq[i]]; mem = members[c]
        if sorted(seq[i:i + len(mem)]) != sorted(mem): proper = False; break
        starts.append(nodes[seq[i]]); i += len(mem)
    res = dict(tag=a.tag, seed=a.seed, proper=proper, sec=round(time.time() - t0, 1))
    if proper:
        cost = sum(RA.wt(RA.last(x), y) for x, y in zip(starts, starts[1:]))
        res.update(cost=cost, L=35288 + cost, J=cost - 10797)
        route = []
        for s in starts: route += [s[j:] + s[:j] for j in range(8)]
        w = list(route[0])
        for x, y in zip(route, route[1:]): kk = RA.wt(x, y); w += list(y[8 - kk:])
        res["measured"] = len(w)
        res["mixed_versions"] = sum(1 for s in starts if s not in set(init))
        if len(w) < 46185:
            p = os.path.join(a.out, "lkh_gtsp2_%d_%s_s%d.txt" % (len(w), a.tag, a.seed)); RA.write_word(w, p); res["file"] = p
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
