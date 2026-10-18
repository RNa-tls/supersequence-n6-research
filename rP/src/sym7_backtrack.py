#!/usr/bin/env python3
"""Round P -- backtrack an optimal path of the symmetric exact-A-count phi DP from the dumped layers,
then re-evaluate it independently with full 84-option vectors (fixed phi-order DP with the given gap
A-counts) and report which A trails realise each connector.
usage: sym_backtrack.py DIR"""
import sys, json
import numpy as np
D = sys.argv[1]; NP, NR, NC, RS = 24, 42, 7, 48; VS = NC * RS
R = np.fromfile(f"{D}/R7.bin", np.uint8).reshape(7, NP, NP, NR, NR).astype(np.int64)
stv = np.fromfile(f"{D}/stv7.bin", np.uint8).reshape(7, NP, NR).astype(np.int64)
env = np.fromfile(f"{D}/env7.bin", np.uint8).reshape(7, NP, NR).astype(np.int64)
tg = np.fromfile(f"{D}/tg6.bin", np.int32).reshape(6, NP); omap = np.fromfile(f"{D}/omap.bin", np.int32).reshape(6, NP, NR)
sp = json.load(open(f"{D}/symprep.json")); rep = np.array(sp["rep"]); phit = sp["phit"]
binom = [[0] * 26 for _ in range(25)]
for n in range(25):
    for k in range(26): binom[n][k] = 1 if k == 0 else (0 if n == 0 else binom[n - 1][k - 1] + binom[n - 1][k])
def rank(m):
    r = 0; i = 0
    while m:
        b = (m & -m).bit_length() - 1; r += binom[b][i + 1]; i += 1; m &= m - 1
    return r
def pm(g, m): return sum(1 << int(tg[g][b]) for b in range(NP) if m >> b & 1)
layers = {}
def layer(k):
    if k not in layers:
        keys = np.fromfile(f"{D}/layers/k{k:02d}_keys.bin", np.uint64)
        vec = np.memmap(f"{D}/layers/k{k:02d}_vec.bin", np.uint8, "r").reshape(len(keys), NC, RS)
        layers[k] = (keys, vec)
    return layers[k]
def vec_of(m, t):
    k = bin(m).count("1"); keys, vec = layer(k)
    best = None
    for g in range(6):
        key = (rank(pm(g, m)) << 5) | int(tg[g][t])
        if best is None or key < best[0]: best = (key, g)
    key, g = best; idx = int(np.searchsorted(keys, np.uint64(key))); assert int(keys[idx]) == key
    cv = np.asarray(vec[idx], np.int64)
    return cv[:, omap[g][t]]          # [c][i] for the actual state
full = (1 << NP) - 1; keys, vec = layer(NP)
best = None
for x in range(len(keys)):
    u = int(keys[x]) & 31; cv = np.asarray(vec[x], np.int64)
    for c in range(NC):
        ty = 6 - c
        for j in range(NR):
            v = cv[c, j] + env[ty][u][j]
            if best is None or v < best[0]: best = (v, u, c, j)
total, u, c, j = best
print("optimum", total, "last trail", phit[u], "A count before end", c)
path = [(u, c, j)]; v = total - env[6 - c][u][j]; m = full
gaps = []
for k in range(NP, 1, -1):
    M = m & ~(1 << u); found = None
    for t in range(NP):
        if not (M >> t & 1): continue
        Dv = vec_of(M, t)
        for a in range(7):
            cs = [c - a]
            for c0 in cs:
                if c0 < 0: continue
                cand = Dv[c0] + R[a, t, u, :, j]
                hit = np.nonzero(cand == v)[0]
                if len(hit): found = (t, c0, int(hit[0]), a, c - c0); break
            if found: break
        if found: break
    assert found, ("no predecessor", k)
    t, c0, i, a, used = found
    gaps.append(used); v = int(vec_of(M, t)[c0, i]); m = M; u, c, j = t, c0, i; path.append((u, c, j))
assert v == stv[c][u][j], (v, stv[c][u][j])
start_A = c
path = path[::-1]; gaps = gaps[::-1]
order = [phit[p[0]] for p in path]
print(json.dumps(dict(order=order, start_A=start_A, gap_A=gaps, end_A=6 - path[-1][1] if False else None)))
json.dump(dict(value=int(total), phi_order=order, start_A=int(start_A), gap_A=[int(g) for g in gaps], end_A=int(6 - sum(gaps) - start_A)), open(f"{D}/sym7_opt_path.json", "w"), indent=1)
