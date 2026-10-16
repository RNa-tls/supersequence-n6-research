#!/usr/bin/env python3
"""Round N (sections 4, 5) -- exact quotient tables of the single-piece opening options.

phi quotient: option -> (trail orbit, version, cut type), cut type = 'L' (link) or 'F<j>' (F-step after
position j of its chain); entry/exit chain positions, world, and its EXTERNAL PROFILE: numbers of
partner options (other trails) at excess e = 0, 1, 2 for in-joins and out-joins, split by partner kind
(phi same component / phi other component / A).  The profile is checked to be constant on each
symmetry class (group of order 12 acting on trails x versions, and the order-6 chain rotation).
A-gadget table: for every A option: cut weight, chain kind/position of entry and exit, and
IN = min_{phi exits x} e(x -> entry), OUT = min_{phi entries y} e(exit -> y); the cut-charge lemma
IN + OUT >= 1 is checked on all 8064 A options, and the Pareto frontier of (IN, OUT, cut) is listed.
usage: quotients.py FAMILY.json E.npy GROUP.json OUT.json"""
import sys, os, json
from collections import Counter, defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP
from famstruct import Fam

C1 = {2, 3, 4, 5, 6, 7, 23, 24, 25, 26, 27}; C2 = {9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21}
def comp(t, isA):
    if isA: return "A"
    return "C1" if t in C1 else ("C2" if t in C2 else "p%d" % t)

def main():
    fam, opts = OP.load(sys.argv[1]); E = np.load(sys.argv[2]); G = json.load(open(sys.argv[3]))
    T = len(fam["trails"])
    isA = {o["t"]: o["m"] == 672 for o in opts}
    tr = np.array([o["t"] for o in opts]); cut = np.array([o["cut"] for o in opts])
    kind = np.array([comp(o["t"], isA[o["t"]]) for o in opts])
    orbit_of = {}
    for k, orb in enumerate(G["trail_orbits"]):
        for t in orb: orbit_of[t] = k
    # chain positions per (trail, version)
    fams = {v: Fam(sys.argv[1], [v] * T) for v in (0, 1)}
    def pos_info(o):
        fm = fams[o["v"]]; lst = fm.trail_runs[o["t"]]; m = len(lst)
        en = lst[o["k"]]; ex = lst[(o["k"] - 1) % m]
        ce, cx = fm.chains[fm.chain_of[en]], fm.chains[fm.chain_of[ex]]
        return (("F" if ce["full"] else "S%d" % len(ce["runs"])) + "p%d" % fm.pos[en],
                ("F" if cx["full"] else "S%d" % len(cx["runs"])) + "p%d" % fm.pos[ex])
    phi_rows = defaultdict(list); a_rows = []
    phi_idx = np.nonzero(~np.array([isA[t] for t in tr]))[0]; a_idx = np.nonzero(np.array([isA[t] for t in tr]))[0]
    for i, o in enumerate(opts):
        others = tr != o["t"]
        prof = {}
        for side, vec in (("in", E[:, i]), ("out", E[i, :])):
            for kd in ("same", "other", "A"):
                if kd == "A": sel = others & (kind == "A")
                elif kd == "same": sel = others & (kind == kind[i]) & (kind != "A")
                else: sel = others & (kind != kind[i]) & (kind != "A")
                v = vec[sel]
                prof["%s_%s" % (side, kd)] = [int((v == e).sum()) for e in (0, 1, 2)]
        pe, px = pos_info(o)
        if not isA[o["t"]]:
            ctype = "L" if o["cut"] == 3 else "F%d" % int(px[px.index("p") + 1:])
            phi_rows[(orbit_of[o["t"]], ctype)].append(dict(t=o["t"], v=o["v"], k=o["k"], entry=pe, exit=px, world=o["entry"][7], **prof))
        else:
            phi_ex = E[np.ix_(phi_idx, [i])].ravel(); phi_en = E[i, phi_idx]
            a_rows.append(dict(t=o["t"], v=o["v"], k=o["k"], cut=int(o["cut"]), entry=pe, exit=px,
                               IN=int(phi_ex.min()), OUT=int(phi_en.min()),
                               IN_phi0=int((phi_ex == 0).sum()), OUT_phi0=int((phi_en == 0).sum())))
    phi_table = []
    for (ob, ctype), rows in sorted(phi_rows.items()):
        keys = [k for k in rows[0] if k.startswith("in_") or k.startswith("out_")]
        profs = {tuple(tuple(r[k]) for k in keys) for r in rows}
        phi_table.append(dict(trail_orbit=G["trail_orbits"][ob], cut_type=ctype, members=len(rows), distinct_profiles=len(profs),
                              entry=sorted({r["entry"] for r in rows}), exit=sorted({r["exit"] for r in rows}),
                              worlds=sorted({r["world"] for r in rows}),
                              profile_example={k: rows[0][k] for k in keys}))
    charge_ok = all(r["IN"] + r["OUT"] >= 1 for r in a_rows)
    pareto = Counter((r["cut"], r["IN"], r["OUT"]) for r in a_rows)
    res = dict(phi_types=len(phi_table), phi_table=phi_table, A_options=len(a_rows), cut_charge_IN_plus_OUT_ge_1=charge_ok,
               A_IN_OUT_hist={"%d|%d|%d" % k: v for k, v in sorted(pareto.items())},
               A_entry_exit_kinds={"%s>%s|c%d" % k: v for k, v in Counter((r["entry"], r["exit"], r["cut"]) for r in a_rows).most_common(12)})
    json.dump(res, open(sys.argv[4], "w"), indent=1)
    print(json.dumps(dict(phi_types=len(phi_table), max_distinct_profiles=max(x["distinct_profiles"] for x in phi_table),
                          A_options=len(a_rows), cut_charge=charge_ok, A_IN_OUT_hist=res["A_IN_OUT_hist"])))

if __name__ == "__main__":
    main()
