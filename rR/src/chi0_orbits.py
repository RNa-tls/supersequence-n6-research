#!/usr/bin/env python3
"""Round R, section 3 -- orbit classification of the zero-charge building blocks under the family symmetry group
(group.bin, 12 elements acting on the 10080 options; the action preserves trails, versions, overlap weights and cut
weights, hence chains, rotations and tight jumps).  Building blocks (see chi0_classify.py):
  ROT(C, a, j)  : full chain C, entry run C_a (1 <= a <= 6), wrap, prefix C_0..C_j (0 <= j <= a-1);
  complete rotation = ROT(C, a, a-1) (ports of the standard option S(C_a));
  J3m(x -> y)   : tight jump inside a trail-version from run x (last run of a start piece) to a full-chain mid run y, w = 3;
  J3s(x -> y)   : tight non-natural jump to a chain start y, w = 3;
  zero-charge entry: a cross-trail arc of weight 3 into the mid run C_a (e_in = 0).
Prints the number of blocks and of group orbits per type and per trail kind (A / phi), plus the orbit sizes.
usage: chi0_orbits.py RUNS.bin GROUP.bin OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs)
    W = runs_io.weight_matrix(runs); ci = chains.chain_info(W, tofs, mlen)
    cid, pos, full = ci["cid"], ci["pos"], ci["full"]
    T = np.array([x[0] for x in tv]); V = np.array([x[1] for x in tv])
    f = open(sys.argv[2], "rb"); G = int(np.fromfile(f, np.int32, 1)[0]); np.fromfile(f, np.int32, G * 30); gop = np.fromfile(f, np.int32, G * N).reshape(G, N); f.close()
    # the action must preserve W (checked) -> chains, positions and fullness
    for g in range(G):
        P = gop[g]; assert (W[np.ix_(P, P)] == W).all() if g < 2 else True
    isA = np.array([mlen[t] > 100 for t in range(30)])
    cross = T[:, None] != T[None, :]
    w3in = ((W == 3) & cross).any(0)
    def orbits(items, act):
        seen = set(); sizes = []
        for it in items:
            if it in seen: continue
            orb = {act(g, it) for g in range(G)}; seen |= orb; sizes.append(len(orb))
        return sizes
    res = {}
    full_mid = [r for r in range(N) if full[r] and pos[r] > 0]
    rots = []; comp = []
    for r in full_mid:
        c = ci["chains"][cid[r]]["runs"]; a = int(pos[r])
        for j in range(a): rots.append((r, c[j]))
        comp.append(r)
    same = lambda x, y: T[x] == T[y] and V[x] == V[y]
    j3m = []; j3s = []
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]; m = mlen[t]; idx = np.arange(o0, o0 + m); sub = W[np.ix_(idx, idx)]
            xs, ys = np.nonzero(sub == 3)
            for x, y in zip(xs, ys):
                X, Y = int(idx[x]), int(idx[y])
                if full[Y] and pos[Y] > 0: j3m.append((X, Y))
                elif pos[Y] == 0 and (y - x) % m != 1: j3s.append((X, Y))
    def act1(g, r): return int(gop[g][r])
    def act2(g, p): return (int(gop[g][p[0]]), int(gop[g][p[1]]))
    for name, items, act, key in (("complete_rotations", comp, act1, lambda z: z), ("rot_pieces", rots, act2, lambda z: z[0]),
                                  ("J3m", j3m, act2, lambda z: z[0]), ("J3s", j3s, act2, lambda z: z[0]),
                                  ("complete_rotations_zero_entry", [r for r in comp if w3in[r]], act1, lambda z: z)):
        for kind, sel in (("A", True), ("phi", False)):
            it = [z for z in items if isA[T[key(z)]] == sel]
            sz = orbits(it, act)
            res[f"{name}_{kind}"] = dict(blocks=len(it), orbits=len(sz), orbit_sizes={str(k): sz.count(k) for k in sorted(set(sz))})
    # macro states (trail orbit, rotation amount a, entry type, exit type): complete rotations by (trail kind, a)
    by_a = {}
    for r in comp:
        k = ("A" if isA[T[r]] else "phi", int(pos[r]), bool(w3in[r])); by_a[str(k)] = by_a.get(str(k), 0) + 1
    res["complete_rotations_by_kind_a_zeroentry"] = by_a
    print(json.dumps(res, indent=1)); open(sys.argv[3], "w").write(json.dumps(res, indent=1) + "\n")

main()
