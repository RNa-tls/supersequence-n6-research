#!/usr/bin/env python3
"""Round L -- LEMMA D (mixed phi-set cost), exact by MIP.

Two-world setting (specials a, b): inside the phi-set P = P({a,b}, C) every class is covered by a
world-a column segment (segment of a world-a orbit of P) or a world-b row segment.  E_P = sum over the
segments of (7 - length)/7.  For every k = number of world-b classes (0..42) the script computes the
exact minimum of E_P (HiGHS MIP over all 2 * 6 * 7 * 7 segments).  Claim checked:
  min E_P = 0 iff k in {0, 42} (pure phi-set), and min E_P >= 1 for every mixed phi-set,
  with the minimum 1 attained (k = 7: one full world-b row, six single-segment columns).
usage: phi_mixed_min.py"""
import os, sys, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from worlds import World, canon_cyc
import highspy, numpy as np
from fractions import Fraction

W = World(8)
a, b = 7, 6
groups = W.phi_sets(a, b)
key = sorted(groups)[0]
P = sorted(groups[key]); Ps = set(P); idx = {c: i for i, c in enumerate(P)}
segs = []
for s_ in (a, b):
    for D, mem in W.orb_members[s_].items():
        if not set(mem) <= Ps: continue
        cyc = W.orbit_cycle(s_, D); m = len(cyc)
        for st in range(m):
            for l in range(1, m + 1):
                segs.append((s_, tuple(cyc[(st + t) % m] for t in range(l))))
segs = list({(s_, frozenset(c), len(c)): (s_, c) for s_, c in segs}.values())
assert len([1 for s_, c in segs if len(c) == 7]) == 12
res = {}
for k in range(0, 43):
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    nc = len(segs)
    lp = highspy.HighsLp(); lp.num_col_ = nc; lp.num_row_ = 43
    lp.col_cost_ = np.array([(7 - len(c)) / 7 for s_, c in segs]); lp.col_lower_ = np.zeros(nc); lp.col_upper_ = np.ones(nc)
    lo = [1.0] * 42 + [float(k)]; up = [1.0] * 42 + [float(k)]
    lp.row_lower_ = np.array(lo); lp.row_upper_ = np.array(up)
    st = [0]; ix = []; vv = []
    for s_, c in segs:
        for x in c: ix.append(idx[x]); vv.append(1.0)
        if s_ == b: ix.append(42); vv.append(float(len(c)))
        st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(st, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32); lp.a_matrix_.value_ = np.array(vv)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * nc
    h.passModel(lp); h.run()
    v = h.getInfo().objective_function_value
    res[k] = str(Fraction(v).limit_denominator(7))
ok = res[0] == "0" and res[42] == "0" and all(Fraction(res[k]) >= 1 for k in range(1, 42)) and Fraction(res[7]) == 1
out = dict(phi_set=[a, b, list(key[2])], segments=len(segs), min_E_by_worldb_classes=res, lemmaD_ok=ok)
print(json.dumps(out))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "phi_mixed_min.json"), "w"), indent=1)
