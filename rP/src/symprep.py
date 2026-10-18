#!/usr/bin/env python3
"""Round P -- symmetry-reduced tables for the exact-A-count phi DP (phidp_sym.c).
Checks that every connector table is invariant under the order-12 option-level group, finds the
version-swap element kappa (trivial on trails), reduces each phi trail's 84 options to 42 kappa-orbits,
and writes:  orbit reps, the 6 trail-level group elements with their orbit maps, the reduced
connector matrices R[a][t][u][i][j] = min(K_a[rep_t(i)][rep_u(j)], K_a[kappa rep_t(i)][rep_u(j)])
(a = 0: direct link, 1: one A, 2: two distinct A, 3: >= 3 A lower bound PRE+SUF), and start/end
orbit vectors per A-count class.
usage: symprep.py DIR GROUP.npz"""
import sys, json
import numpy as np

D = sys.argv[1]; G = np.load(sys.argv[2])
operm, tperm = G["operm"], G["tperm"]
trail = np.fromfile(f"{D}/trail.bin", np.int32); cut = np.fromfile(f"{D}/cut.bin", np.int32)
Aset = {1, 8, 15, 22, 28, 29}
phi = np.array([o for o in range(len(trail)) if trail[o] not in Aset]); P = len(phi); NO = 84
pos = -np.ones(len(trail), np.int64); pos[phi] = np.arange(P)
phit = sorted(set(trail[phi].tolist())); tid = {t: i for i, t in enumerate(phit)}
assert all(np.all(trail[phi[i * NO:(i + 1) * NO]] == phit[i]) for i in range(24))
ld = lambda n: np.fromfile(f"{D}/{n}", np.uint8).astype(np.int64)
Ed = ld("Ed.bin").reshape(P, P); K1 = ld("K1.bin").reshape(P, P); K2 = ld("K2.bin").reshape(P, P)
vec = {n: ld(n + ".bin") for n in ("PRE", "SUF", "S1", "S2", "S3", "Q1")}
st0 = (cut[phi] == 2).astype(np.int64)
# option-level group restricted to phi options
og = []
for g in operm:
    m = pos[g[phi]]; assert np.all(m >= 0); og.append(m)
og = np.array(og)
same = (np.arange(P)[:, None] // NO) == (np.arange(P)[None, :] // NO)
for k, m in enumerate(og):
    for name, M in (("Ed", Ed), ("K1", K1), ("K2", K2)):
        A = M.copy(); A[same] = 0; B = M[np.ix_(m, m)].copy(); B[same] = 0
        assert np.array_equal(A, B), (name, k)
    for name, v in vec.items(): assert np.array_equal(v[m], v), (name, k)
    assert np.array_equal(st0[m], st0)
print("invariance of Ed, K1, K2, PRE, SUF, S1, S2, S3, Q1, start: OK for all", len(og), "elements")
# trail action on the 24 phi trails
tg = np.array([[tid[int(tperm[k][phit[i]])] for i in range(24)] for k in range(len(og))])
kap = [k for k in range(len(og)) if np.all(tg[k] == np.arange(24)) and not np.all(og[k] == np.arange(P))]
assert len(kap) == 1; kap = og[kap[0]]
assert np.all(kap[kap] == np.arange(P)) and np.all(kap != np.arange(P))
# kappa orbits per trail: rep = smaller local index of each pair
rep = np.zeros((24, 42), np.int64); orb = np.zeros(P, np.int64)
for t in range(24):
    seen = set(); j = 0
    for o in range(t * NO, t * NO + NO):
        if o in seen: continue
        q = int(kap[o]); assert q // NO == t
        seen.update({o, q}); rep[t, j] = o; orb[o] = j; orb[q] = j; j += 1
    assert j == 42
# 6 distinct trail permutations, one option permutation each
elems = []; seen = set()
for k in range(len(og)):
    key = tuple(tg[k])
    if key in seen: continue
    seen.add(key); elems.append(k)
assert len(elems) == 6
# orbit maps: omap[g][t][i] = orbit index (in trail tg[g][t]) of og[g][rep[t][i]]
omap = np.zeros((6, 24, 42), np.int32)
for gi, k in enumerate(elems):
    for t in range(24):
        for i in range(42):
            o2 = og[k][rep[t, i]]; assert o2 // NO == tg[k][t]
            omap[gi, t, i] = orb[o2]
L3 = vec["PRE"][:, None] + vec["SUF"][None, :]
mats = [Ed, K1, K2, L3]
R = np.full((4, 24, 24, 42, 42), 250, np.int64)
for a, M in enumerate(mats):
    for t in range(24):
        for u in range(24):
            if t == u: continue
            r1 = M[np.ix_(rep[t], rep[u])]; r2 = M[np.ix_(kap[rep[t]], rep[u])]
            R[a, t, u] = np.minimum(r1, r2)
# kappa-invariance consequence: value at rep_u(j) equals value at kappa rep_u(j)
for a, M in enumerate(mats):
    for t in range(3):
        for u in range(3, 6):
            x = M[np.ix_(np.arange(t * NO, t * NO + NO), rep[u])].min(0); y = M[np.ix_(np.arange(t * NO, t * NO + NO), kap[rep[u]])].min(0)
            assert np.array_equal(x, y)
stv = np.zeros((4, 24, 42), np.int64); env = np.zeros((4, 24, 42), np.int64)
starts = [st0, vec["S1"], vec["S2"], vec["S3"]]; ends = [np.zeros(P, np.int64), vec["Q1"], vec["PRE"], vec["PRE"]]
for a in range(4):
    for t in range(24):
        stv[a, t] = starts[a][rep[t]]; env[a, t] = ends[a][rep[t]]
        assert np.array_equal(starts[a][rep[t]], starts[a][kap[rep[t]]]) and np.array_equal(ends[a][rep[t]], ends[a][kap[rep[t]]])
R.astype(np.uint8).tofile(f"{D}/R.bin"); stv.astype(np.uint8).tofile(f"{D}/stv.bin"); env.astype(np.uint8).tofile(f"{D}/env.bin")
tg[elems].astype(np.int32).tofile(f"{D}/tg6.bin"); omap.tofile(f"{D}/omap.bin")
json.dump(dict(phit=phit, elems=elems, rep=rep.tolist()), open(f"{D}/symprep.json", "w"))
print("wrote R.bin", R.shape, "stv/env", stv.shape, "tg6", tg[elems].tolist())
# exact A-chain tables (prep_chain.c): types a = 0 (direct) .. 6 (chain of 6 A trails)
Ka = np.fromfile(f"{D}/Ka.bin", np.uint8).reshape(6, P, P).astype(np.int64)
Sa = np.fromfile(f"{D}/Sa.bin", np.uint8).reshape(6, P).astype(np.int64); Qa = np.fromfile(f"{D}/Qa.bin", np.uint8).reshape(6, P).astype(np.int64)
for k, m in enumerate(og):
    for a in range(6):
        A_ = Ka[a].copy(); A_[same] = 0; B_ = Ka[a][np.ix_(m, m)].copy(); B_[same] = 0
        assert np.array_equal(A_, B_), ("Ka", a, k)
        assert np.array_equal(Sa[a][m], Sa[a]) and np.array_equal(Qa[a][m], Qa[a]), ("Sa/Qa", a, k)
print("invariance of K_a, S_a, Q_a (a = 1..6): OK")
mats7 = [Ed] + [Ka[a] for a in range(6)]
R7 = np.full((7, 24, 24, 42, 42), 250, np.int64)
for a, M in enumerate(mats7):
    for t in range(24):
        for u in range(24):
            if t == u: continue
            R7[a, t, u] = np.minimum(M[np.ix_(rep[t], rep[u])], M[np.ix_(kap[rep[t]], rep[u])])
st7 = np.zeros((7, 24, 42), np.int64); en7 = np.zeros((7, 24, 42), np.int64)
starts7 = [st0] + [Sa[a] for a in range(6)]; ends7 = [np.zeros(P, np.int64)] + [Qa[a] for a in range(6)]
for a in range(7):
    for t in range(24):
        st7[a, t] = starts7[a][rep[t]]; en7[a, t] = ends7[a][rep[t]]
        assert np.array_equal(starts7[a][rep[t]], starts7[a][kap[rep[t]]]) and np.array_equal(ends7[a][rep[t]], ends7[a][kap[rep[t]]])
R7.astype(np.uint8).tofile(f"{D}/R7.bin"); st7.astype(np.uint8).tofile(f"{D}/stv7.bin"); en7.astype(np.uint8).tofile(f"{D}/env7.bin")
print("wrote R7.bin", R7.shape)
