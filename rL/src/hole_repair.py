#!/usr/bin/env python3
"""Round L (sections 9, 14) -- hole anatomy and exact local repair cost of a closed syllable trail.

For the closed trail T of a syllable word (rI bundle_scan_lib, start = identity):
  * worlds, chain lengths, holes H(T) = classes outside T in the world-orbits of T's non-full chains;
  * for every hole h: partner structure, and ell(h) = longest chain through h that avoids T
    (world a = T's world: only inside the same orbit; other worlds: a segment of O(b, h-b));
  * exact minimum repair fragmentation: min sum (7-l)/7 over sets of pairwise disjoint T-avoiding
    chains covering every hole (HiGHS MIP over all T-avoiding segments meeting H(T)).
    Any r = 0 route containing T as a trail has E >= E_T + this minimum  (the covering chains are
    chains of the route, disjoint from T and from each other).
  * phi-set incidence: number of phi-sets (all 28 pairs) fully inside T / meeting T.
usage: hole_repair.py 'WORD' [...]"""
import sys, os, json, time
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from worlds import World, canon_cyc
from bundle_scan_lib import closed_letters
import highspy, numpy as np

n = 8
W = World(n)

def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))

def trail_chains(word):
    letters, Fp, T = closed_letters(n, word)
    P = tuple(range(n)); out = []
    for l, s in letters:
        a = P[n - 1]
        cl = [W.cid[canon_cyc(list(comp(P, Fp[j])))] for j in range(l)]
        D = canon_cyc([x for x in P if x != a])
        out.append(dict(a=a, D=D, l=l, classes=cl))
        P = comp(P, comp(Fp[l - 1], T(s)))
    return out

def analyse(word):
    t0 = time.time()
    ch = trail_chains(word)
    TS = set(x for c in ch for x in c["classes"]); assert len(TS) == sum(c["l"] for c in ch)
    k = len(ch); size = len(TS)
    worlds = Counter(c["a"] for c in ch)
    holes = set(); hole_owner = {}
    for c in ch:
        if c["l"] < 7:
            for x in W.orb_members[c["a"]][c["D"]]:
                if x not in TS: holes.add(x); hole_owner.setdefault(x, []).append((c["a"], c["D"]))
    # T-avoiding segments through holes (world-orbit segments not meeting T)
    segs = set()
    for a in range(n):
        seen_orbits = set()
        for h in holes:
            D = W.orb[a][h]
            if (a, D) in seen_orbits: continue
            seen_orbits.add((a, D))
            cyc = W.orbit_cycle(a, D); m = len(cyc)
            free = [x not in TS for x in cyc]
            if all(free):
                for s in range(m):
                    for l in range(1, m + 1): segs.add((a, tuple(cyc[(s + t) % m] for t in range(l))))
            else:
                for s in range(m):
                    if not free[s] or free[(s - 1) % m]: continue
                    run = []; t = s
                    while free[t % m] and len(run) < m: run.append(cyc[t % m]); t += 1
                    for u in range(len(run)):
                        for v in range(u + 1, len(run) + 1): segs.add((a, tuple(run[u:v])))
    segs = [s for s in segs if any(x in holes for x in s[1])]
    ell = {h: max(len(s[1]) for s in segs if h in s[1]) for h in holes}
    # exact min repair fragmentation: cover holes exactly once, other classes at most once
    cls = sorted({x for s in segs for x in s[1]}); idx = {c: i for i, c in enumerate(cls)}
    hh = highspy.Highs(); hh.setOptionValue("output_flag", False); hh.setOptionValue("time_limit", 900.0)
    lp = highspy.HighsLp(); nc = len(segs)
    lp.num_col_ = nc; lp.num_row_ = len(cls)
    lp.col_cost_ = np.array([(7 - len(s[1])) / 7 for s in segs]); lp.col_lower_ = np.zeros(nc); lp.col_upper_ = np.ones(nc)
    lp.row_lower_ = np.array([1.0 if c in holes else 0.0 for c in cls]); lp.row_upper_ = np.ones(len(cls))
    st = [0]; ix = []; vv = []
    for s in segs:
        for x in s[1]: ix.append(idx[x]); vv.append(1.0)
        st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(st, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32); lp.a_matrix_.value_ = np.array(vv)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * nc
    hh.passModel(lp); hh.run(); info = hh.getInfo()
    # phi-set incidence
    inside = 0; meet = 0
    import itertools
    for a, b in itertools.combinations(range(n), 2):
        for key, mem in W.phi_sets(a, b).items():
            c = sum(1 for x in mem if x in TS)
            if c == 42: inside += 1
            if c: meet += 1
    E_T = sum(7 - c["l"] for c in ch) / 7
    return dict(word=word, classes=size, chains=k, saving=round(size / 6 - (k + 1), 4), E_T=round(E_T, 4),
                worlds=dict(worlds), chain_lengths=dict(Counter(c["l"] for c in ch)),
                holes=len(holes), ell_hist=dict(sorted(Counter(ell.values()).items())),
                repair_min_E=round(info.objective_function_value, 4), repair_bound=round(info.mip_dual_bound, 4),
                repair_status=hh.modelStatusToString(hh.getModelStatus()),
                phi_inside=inside, phi_meet=meet, sec=round(time.time() - t0, 1))

if __name__ == "__main__":
    out = []
    for w in sys.argv[1:]:
        r = analyse(w); print(json.dumps(r), flush=True); out.append(r)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "hole_repair.json"), "w"), indent=1)
