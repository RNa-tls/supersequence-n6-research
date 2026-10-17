#!/usr/bin/env python3
"""Round O -- the 'half-split' triple potential bound, no LP needed.
Every link o -> o' (trails a -> b) has capped excess min(e, 3) >= rowmin_b(o)/2 + colmin_a(o')/2.
Hence for every single-opening word, cost >= sum over trails b (with neighbours a, c in the order) of
    U(a, b, c) = min_{o in b} [ [a = S][cut(o) = 2] + colmin_a(o)/2 + rowmin_c(o)/2 ]
(one half of each link charged to each endpoint; first trail pays the start cost).  The minimum over
all orders of sum U is an exact 30-node triple-cost ATSP-path (MIP) -- a valid lower bound on min F.
usage: triple_default_bound.py FAMILY.json E.npy AUDIT.json OUT.json"""
import sys, os, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tlp_cg as TC

def main():
    fam, E_p, audit, out = sys.argv[1:5]
    m = TC.TMaster(fam, E_p)
    D2, D3, D4 = m.default_duals()
    U = m.implied_U(D2, D3)
    base = [r["trail"] for r in json.load(open(audit))["table"]]
    t0 = time.time(); v, p, b, st = m.exact_qtsp(U, time_limit=1800)
    res = dict(U_on_46185=m.path_cost(base, U), qtsp_min=v, qtsp_bound=b, status=st, argmin=p, sec=round(time.time() - t0, 1),
               other_corr=m.other_corrections(D2, D3, D4), q_corr=m.q_corrections(U, D2, D3))
    json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))

if __name__ == "__main__":
    main()
