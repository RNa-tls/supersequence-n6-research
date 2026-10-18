#!/usr/bin/env python3
"""Round P -- mutation test of a backward-table entry (checker B layout, see ckB.c).
Locates the entry H(S_k, t_k, c_k)[orbit(o_k)] used by a record word at its k-th phi trail (S_k = first k phi
trails, t_k = k-th phi trail, o_k its option, c_k = A trails still to come), and writes a copy of the H layer
directory in which that ONE entry is replaced by VALUE (all other layers are symlinks).
usage: hcorrupt.py CKBDIR HDIR DESCRIPTION.json K VALUE OUTDIR"""
import sys, os, json, struct
import numpy as np
NTR, NPH, NOP, NOR, NCN = 30, 24, 84, 42, 7
ckdir, hdir, desc_p, K, VAL, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
b = open(f"{ckdir}/runs.bin", "rb").read(); p = 0; mrun = []
for t in range(NTR):
    ms = []
    for v in range(2):
        m = struct.unpack("<i", b[p:p + 4])[0]; p += 4 + 8 * m; ms.append(m)
    mrun.append(ms)
tcnt = [m[0] + m[1] for m in mrun]; tofs = np.concatenate([[0], np.cumsum(tcnt)[:-1]]).astype(int)
isA = [m[0] > 100 for m in mrun]
g = np.fromfile(f"{ckdir}/group.bin", np.int32); G = g[0]; tp = g[1:1 + G * NTR].reshape(G, NTR); op = g[1 + G * NTR:].reshape(G, -1)
sel = []
for e in range(G):
    if not any(np.array_equal(tp[s], tp[e]) for s in sel): sel.append(e)
meta = np.fromfile(f"{hdir}/meta.bin", np.int32); q = 0
phl = meta[q:q + NPH]; q += NPH; ptr = meta[q:q + 6 * NPH].reshape(6, NPH); q += 6 * NPH; q += NPH * NOR
oorb = meta[q:q + NPH * NOP].reshape(NPH, NOP)
phidx = {int(t): i for i, t in enumerate(phl)}
for s in range(6):
    for i in range(NPH): assert phidx[int(tp[sel[s]][phl[i]])] == ptr[s][i]
bn = [[0] * 26 for _ in range(25)]
for n in range(25):
    for k in range(26): bn[n][k] = 1 if k == 0 else (0 if n == 0 else bn[n - 1][k - 1] + bn[n - 1][k])
def rk(m):
    r = 0; i = 0
    for bb in range(NPH):
        if m >> bb & 1: i += 1; r += bn[bb][i]
    return r
d = json.load(open(desc_p))["description"]
phis = []; A_before = []; nA = 0
for (t, v, k, m) in d:
    if isA[t]: nA += 1; continue
    phis.append((phidx[t], int(tofs[t] + (mrun[t][0] if v else 0) + k))); A_before.append(nA)
S = 0
for i in range(K): S |= 1 << phis[i][0]
t, o = phis[K - 1]; c = 6 - A_before[K - 1]
best = None
for s in range(6):
    Sm = 0
    for bb in range(NPH):
        if S >> bb & 1: Sm |= 1 << int(ptr[s][bb])
    key = (rk(Sm) << 5) | int(ptr[s][t])
    if best is None or key > best[0]: best = (key, s)
key, s = best; t2 = int(ptr[s][t]); o2 = int(op[sel[s]][o]); orbit = int(oorb[t2][o2 - tofs[phl[t2]]])
keys = np.fromfile(f"{hdir}/H{K:02d}.key", np.uint64); idx = int(np.searchsorted(keys, np.uint64(key))); assert keys[idx] == key
os.makedirs(out, exist_ok=True)
for fn in os.listdir(hdir):
    dst = os.path.join(out, fn)
    if os.path.lexists(dst): os.remove(dst)
    if fn != f"H{K:02d}.val": os.symlink(os.path.join(os.path.abspath(hdir), fn), dst)
val = np.fromfile(f"{hdir}/H{K:02d}.val", np.uint8); off = idx * NCN * NOR + c * NOR + orbit; old = int(val[off]); val[off] = VAL
val.tofile(os.path.join(out, f"H{K:02d}.val"))
print(json.dumps(dict(layer=K, phi_trail=int(phl[t]), remaining_A=c, canonical_key=int(key), index=idx, orbit=orbit, old=old, new=VAL)))
