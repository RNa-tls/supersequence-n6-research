#!/usr/bin/env python3
"""Round L -- break attempt / repair-demand measurement for the S4^10 12-packings of rK.

For each 12-packing (rK/certs/s4_packing.json, class masks over the sorted class list):
  * R = complement (1080 classes);
  * per world a: histogram of |O cap R| over world-a orbits O;
  * min number of chains (segments of world orbits lying in R, any special) partitioning R,
    exact (HiGHS MIP); gives E_R = q_R - |R|/7 >= ... and the saving needed.
A 46186 route through this packing needs  sum_{T in R}(k_T+1) + lambda <= 210 (see report).
usage: complement_s4.py"""
import sys, os, json, time
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from worlds import World
import highspy, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W = World(8)
d = json.load(open(os.path.join(HERE, "..", "..", "rK", "certs", "s4_packing.json")))
out = []
for pk, pack in enumerate(d["packings"]):
    used = 0
    for m in pack: used |= int(m, 16)
    R = [i for i in range(W.M) if not (used >> i) & 1]
    Rs = set(R)
    hist = {}
    segs = []                              # (world, classes) segments inside R
    for a in range(8):
        h = Counter()
        for D in W.orb_members[a]:
            cyc = W.orbit_cycle(a, D)
            inR = [c in Rs for c in cyc]
            h[sum(inR)] += 1
            m = len(cyc)
            if all(inR):
                for s in range(m):
                    for l in range(1, m + 1):
                        segs.append((a, tuple(cyc[(s + t) % m] for t in range(l))))
            else:
                for s in range(m):
                    if not inR[s] or inR[(s - 1) % m]: continue      # maximal-run starts
                    run = []
                    t = s
                    while inR[t % m] and len(run) < m: run.append(cyc[t % m]); t += 1
                    for u in range(len(run)):
                        for v in range(u + 1, len(run) + 1):
                            segs.append((a, tuple(run[u:v])))
        hist[a] = dict(sorted(h.items()))
    segs = list(set(segs))
    # exact min chain cover of R
    idx = {c: k for k, c in enumerate(R)}
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("time_limit", 600.0)
    ncol = len(segs)
    lp = highspy.HighsLp()
    lp.num_col_ = ncol; lp.num_row_ = len(R)
    lp.col_cost_ = np.ones(ncol); lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.ones(ncol)
    lp.row_lower_ = np.ones(len(R)); lp.row_upper_ = np.ones(len(R))
    starts = [0]; index = []; vals = []
    for a, cl in segs:
        for c in cl: index.append(idx[c]); vals.append(1.0)
        starts.append(len(index))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(starts, dtype=np.int32); lp.a_matrix_.index_ = np.array(index, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(vals)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * ncol
    h.passModel(lp); t0 = time.time(); h.run()
    info = h.getInfo()
    res = dict(packing=pk, R=len(R), segments=ncol, orbit_hist_by_world=hist,
               min_chains=info.objective_function_value, mip_bound=info.mip_dual_bound,
               status=h.modelStatusToString(h.getModelStatus()), sec=round(time.time() - t0, 1))
    res["E_R_lower"] = res["mip_bound"] - len(R) / 7
    print(json.dumps(res), flush=True)
    out.append(res)
json.dump(out, open(os.path.join(HERE, "..", "certs", "complement_s4.json"), "w"), indent=1)
