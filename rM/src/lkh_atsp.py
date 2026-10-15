#!/usr/bin/env python3
"""Round M -- LKH (the LKH-3.0.8 copy compiled into elkai) on the RUN-LEVEL ATSP of a fixed-start
r = 0 family.  Node 0 = depot (cost 0 both ways), nodes 1..5040 = runs (starts taken from WORD or
from FAMILY.json + a version vector).  The tour minus the depot is a Hamiltonian path of runs;
L = 35288 + path cost.  Every returned path is rebuilt as a word and measured from scratch.
usage: lkh_atsp.py WORD [--init INITWORD] [--runs R] [--trials T] [--seed S] [--time SEC]
                   [--cand K] [--nosub] [--period P] [--popmusic] [--tag TAG]"""
import sys, os, json, time, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("word"); ap.add_argument("--init"); ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--trials", type=int, default=0); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--time", type=float, default=0); ap.add_argument("--cand", type=int, default=5)
    ap.add_argument("--nosub", action="store_true"); ap.add_argument("--period", type=int, default=0)
    ap.add_argument("--popmusic", action="store_true"); ap.add_argument("--tag", default="")
    ap.add_argument("--move", type=int, default=5); ap.add_argument("--kicks", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs"))
    ap.add_argument("--scratch", default=".")
    a = ap.parse_args()
    from elkai import _elkai
    t0 = time.time()
    starts = RA.starts_of_word(RA.load_word(a.word))
    N = len(starts)
    W = RA.weight_matrix(starts)
    M = np.zeros((N + 1, N + 1), dtype=np.uint8); M[1:, 1:] = W
    # problem string: all entries are single digits
    body = (M + 48).astype(np.uint8)
    sp = np.full((N + 1, 2 * (N + 1)), 32, dtype=np.uint8); sp[:, 0::2] = body; sp[:, -1] = 10
    prob = ("TYPE : ATSP\nDIMENSION : %d\nEDGE_WEIGHT_TYPE : EXPLICIT\nEDGE_WEIGHT_FORMAT : FULL_MATRIX\n"
            "EDGE_WEIGHT_SECTION\n" % (N + 1)) + sp.tobytes().decode() + "EOF\n"
    params = ["PROBLEM_FILE = :stdin:", "RUNS = %d" % a.runs, "SEED = %d" % a.seed, "TRACE_LEVEL = 1",
              "MAX_CANDIDATES = %d" % a.cand, "MOVE_TYPE = %d" % a.move]
    if a.trials: params.append("MAX_TRIALS = %d" % a.trials)
    if a.time: params.append("TIME_LIMIT = %g" % a.time)
    if a.nosub: params.append("SUBGRADIENT = NO")
    if a.period: params.append("INITIAL_PERIOD = %d" % a.period)
    if a.popmusic: params.append("CANDIDATE_SET_TYPE = POPMUSIC")
    if a.kicks: params.append("KICKS = %d" % a.kicks)
    init_cost = None
    if a.init:
        ist = RA.starts_of_word(RA.load_word(a.init)); pos = {s: i for i, s in enumerate(starts)}
        order0 = [pos[s] for s in ist]; init_cost = RA.path_cost(W, order0)
        tf = os.path.join(a.scratch, "init_%s_%d.tour" % (a.tag, os.getpid()))
        open(tf, "w").write("TYPE : TOUR\nDIMENSION : %d\nTOUR_SECTION\n1\n" % (N + 1) +
                            "\n".join(str(i + 2) for i in order0) + "\n-1\nEOF\n")
        params.append("INITIAL_TOUR_FILE = %s" % tf)
    print(json.dumps(dict(N=N, init_cost=init_cost, params=params, build_sec=round(time.time() - t0, 1))), flush=True)
    tour = _elkai.solve_problem("\n".join(params) + "\n", prob)
    tour = [x - 1 for x in tour]
    k = tour.index(0); tour = tour[k + 1:] + tour[:k]
    order = [x - 1 for x in tour]
    assert sorted(order) == list(range(N))
    c = RA.path_cost(W, order)
    res = dict(tag=a.tag, cost=c, L=35288 + c, J=c - 10797, init_cost=init_cost, sec=round(time.time() - t0, 1), seed=a.seed)
    w = RA.word_of(starts, order)
    res["measured"] = len(w)
    if len(w) < 46185:
        p = os.path.join(a.out, "lkh_%d_%s_s%d.txt" % (len(w), a.tag, a.seed)); RA.write_word(w, p); res["file"] = p
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
