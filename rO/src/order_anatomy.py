#!/usr/bin/env python3
"""Round O (sections 8, 14) -- cost anatomy of individual orders: exact F(pi) with its optimal
options, split by link type (A-related, cross-component phi-phi, component-internal, phi0/phi14).
Applied to the 87 orders of the 16.111 hull decomposition and to the 46185 order.
usage: order_anatomy.py FAMILY.json E.npy HULL.json AUDIT.json OUT.json"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixed_order as FA
AT = {1, 8, 15, 22, 28, 29}; C1 = {2, 3, 4, 5, 6, 7, 23, 24, 25, 26, 27}; C2 = {9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21}
def comp(t): return "A" if t in AT else "C1" if t in C1 else "C2" if t in C2 else "p%d" % t
def kind(a, b):
    ca, cb = comp(a), comp(b)
    if "A" in (ca, cb): return "A"
    if ca.startswith("p") or cb.startswith("p"): return "p0p14"
    return "internal" if ca == cb else "cross"
def anatomy(fo, order):
    v, ch = fo.F(order, True)
    br = {"A": 0, "cross": 0, "internal": 0, "p0p14": 0, "start": int(fo.cut[ch[0]] == 2)}
    cnt = {"A": 0, "cross": 0, "internal": 0, "p0p14": 0}
    for (a, b), (o, o2) in zip(zip(order, order[1:]), zip(ch, ch[1:])):
        k = kind(a, b); br[k] += int(fo.E[o, o2]); cnt[k] += 1
    nA_adj = sum(1 for a, b in zip(order, order[1:]) if a in AT and b in AT)
    return dict(F=v, cost=br, links=cnt, AA_links=nA_adj)
def main():
    fam, E_p, hull_p, audit_p, out = sys.argv[1:6]
    fo = FA.FixedOrder(fam, E_p)
    dec = json.load(open(hull_p))["decomposition"]
    base = [r["trail"] for r in json.load(open(audit_p))["table"]]
    rows = [dict(lam=d["lam"], **anatomy(fo, d["order"])) for d in dec]
    agg = {k: sum(r["lam"] * r["cost"][k] for r in rows) for k in ("A", "cross", "internal", "p0p14", "start")}
    lk = {k: sum(r["lam"] * r["links"][k] for r in rows) for k in ("A", "cross", "internal", "p0p14")}
    res = dict(base_46185=anatomy(fo, base), hull_lam_weighted_cost=agg, hull_lam_weighted_links=lk,
               hull_lam_weighted_F=sum(r["lam"] * r["F"] for r in rows), hull_AA_links=sum(r["lam"] * r["AA_links"] for r in rows), orders=rows)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "orders"}))
main()
