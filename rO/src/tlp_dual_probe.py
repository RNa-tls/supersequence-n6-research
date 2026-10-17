#!/usr/bin/env python3
"""Round O -- valid Lagrangian bounds from the duals of a restricted triple-consistent LP.
Builds the restricted master on a pool of orders, maps its duals to the full model (missing pairs:
the feasible half-split defaults, missing triples: implied values), optionally symmetrises over the
family group, blends with the default point and evaluates
    L = u_conv + min(0, QTSP*(U) - u_conv) + q-corrections + y/eout/ein corrections
with the exact DFJ QTSP (its proven dual bound is used).  Every L is a valid lower bound on min F.
usage: tlp_dual_probe.py FAMILY.json E.npy AUDIT.json POOL1.json [POOL2.json] OUT.json"""
import sys, os, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tlp_cg as TC

def orders_of(p):
    d = json.load(open(p))
    if "decomposition" in d: return [x["order"] for x in d["decomposition"]]
    if "orders" in d: return [x["order"] for x in d["orders"]]
    return d["pool"]

def main():
    fam, E_p, audit = sys.argv[1:4]; pools = sys.argv[4:-1]; out = sys.argv[-1]
    m = TC.TMaster(fam, E_p); m.load_group(os.path.join(HERE, "..", "certs", "group_options.npz"))
    base = [r["trail"] for r in json.load(open(audit))["table"]]
    allp = [base]
    for p in pools: allp += orders_of(p)
    m.add_orders(allp)
    t0 = time.time(); st, dt = m.solve(); print(json.dumps(dict(event="master", lp=m.obj, status=st, pool=len(m.pool), sec=round(dt, 1))), flush=True)
    Ur, D2r, D3r, D4r, uc = m.full_duals()
    Us, D2s, D3s, D4s = m.symmetrize(Ur, D2r, D3r, D4r)
    D2d, D3d, D4d = m.default_duals(); Ud = m.implied_U(D2d, D3d)
    res = []
    for name, (U0, D20, D30, D40) in (("raw", (Ur, D2r, D3r, D4r)), ("sym", (Us, D2s, D3s, D4s))):
        for a in (0.0, 0.5):
            U = (1 - a) * U0 + a * Ud; D2 = (1 - a) * D20 + a * D2d; D3 = (1 - a) * D30 + a * D3d; D4 = (1 - a) * D40 + a * D4d
            ucv = (1 - a) * uc + a * 10.0
            v, p, b, s = m.exact_qtsp_dfj(U, time_limit=900)
            L = ucv + min(0.0, b - ucv) + m.q_corrections(U, D2, D3) + m.other_corrections(D2, D3, D4)
            rec = dict(duals=name, blend_default=a, qtsp=v, qtsp_bound=b, status=s, u_conv=ucv, L=L); res.append(rec)
            print(json.dumps(rec), flush=True)
    json.dump(dict(master_lp=m.obj, pool=len(m.pool), probes=res), open(out, "w"), indent=1)

main()
