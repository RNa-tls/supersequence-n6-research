#!/usr/bin/env python3
"""Round P -- identity-aware search restricted to the 'relevant' states of the relaxed DP (see report §P).

Relaxed DP (phidp_sym7.c): phi options exact; the A trails between consecutive phi trails form chains
priced by K_a (min over consecutive-distinct A sequences and options); exactly 6 A uses; the identity of
the A trails in different gaps is free.  f / h = forward / reversed values (canonical records written by
phidp_sym7 in comparison mode at threshold THR).
Every word pi with F(pi) <= THR has f + h <= F_relaxed(pi) <= F(pi) <= THR at every layer of its
phi-sequence, so it only visits relevant (S, t, c, o).

Here the six A trails are tracked individually (A-mask).  Chains of 1 or 2 A trails are priced EXACTLY for
their actual trails (T1, T2, S1x, S2x, Q1x, Q2x from prep_t12.c); chains of >= 3 A trails use K_a / S_a / Q_a
and may use any subset of the unused A trails of that size (still <= the true cost).  Options with
exact-so-far + h > THR are discarded.  The minimum found is therefore <= the true F of every word with
F <= THR and >= ... it is the exact optimum when no chain of >= 3 A trails is used.
usage: exact_relevant.py PDPDIR RELDIR THR OUT.json"""
import sys, os, json, itertools, time
import numpy as np
D, RD, THR, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
NP, NR, NC, NO, P = 24, 42, 7, 84, 2016; INF = 10**4
trail = np.fromfile(f"{D}/trail.bin", np.int32); cut = np.fromfile(f"{D}/cut.bin", np.int32); Nopt = len(trail)
Aid = [1, 8, 15, 22, 28, 29]
sp = json.load(open(f"{D}/symprep.json")); phit = sp["phit"]; rep = np.array(sp["rep"])
topts = [np.nonzero(trail == t)[0] for t in phit]
mm = lambda n, shape: np.memmap(f"{D}/{n}", np.uint8, "r", shape=shape)
Ed = mm("Ed.bin", (P, P)); T1 = mm("T1.bin", (6, P, P)); T2 = mm("T2.bin", (36, P, P)); Ka = mm("Ka.bin", (6, P, P))
S1x = np.fromfile(f"{D}/S1x.bin", np.uint8).reshape(6, P).astype(np.int16); S2x = np.fromfile(f"{D}/S2x.bin", np.uint8).reshape(36, P).astype(np.int16)
Q1x = np.fromfile(f"{D}/Q1x.bin", np.uint8).reshape(6, P).astype(np.int16); Q2x = np.fromfile(f"{D}/Q2x.bin", np.uint8).reshape(36, P).astype(np.int16)
Sa = np.fromfile(f"{D}/Sa.bin", np.uint8).reshape(6, P).astype(np.int16); Qa = np.fromfile(f"{D}/Qa.bin", np.uint8).reshape(6, P).astype(np.int16)
tg = np.fromfile(f"{D}/tg6.bin", np.int32).reshape(6, NP); omap = np.fromfile(f"{D}/omap.bin", np.int32).reshape(6, NP, NR)
G = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rO", "certs", "group_options.npz"))
operm, tperm = G["operm"], G["tperm"]
kap = operm[[k for k in range(len(operm)) if np.all(tperm[k] == np.arange(30)) and not np.all(operm[k] == np.arange(Nopt))][0]]
orb = np.full((NP, NO), -1, np.int64)
for t in range(NP):
    for i in range(NR): orb[t, rep[t, i] - t * NO] = i
for t in range(NP):
    for o in range(NO):
        if orb[t, o] < 0: orb[t, o] = orb[t, int(np.nonzero(topts[t] == kap[topts[t][o]])[0][0])]
binom = [[0] * 26 for _ in range(25)]
for n in range(25):
    for k in range(26): binom[n][k] = 1 if k == 0 else (0 if n == 0 else binom[n - 1][k - 1] + binom[n - 1][k])
def unrank(r, k):
    m = 0
    for i in range(k, 0, -1):
        b = i - 1
        while b + 1 <= 23 and binom[b + 1][i] <= r: b += 1
        r -= binom[b][i]; m |= 1 << b
    return m
def pm(g, m):
    out = 0
    while m:
        b = (m & -m).bit_length() - 1; out |= 1 << int(tg[g][b]); m &= m - 1
    return out
# expand canonical relevant records to all actual states: H[(S, t)] = (f[7][84], h[7][84])
H = {}
for k in range(1, NP + 1):
    fn = f"{RD}/relevant_k{k:02d}.bin"
    if not os.path.exists(fn): continue
    raw = np.fromfile(fn, np.uint8).reshape(-1, 8 + 2 * NC * NR)
    for r in raw:
        key = int(np.frombuffer(r[:8].tobytes(), np.uint64)[0]); tc = key & 31; Sc = unrank(key >> 5, k)
        f = r[8:8 + NC * NR].reshape(NC, NR).astype(np.int16); h = r[8 + NC * NR:].reshape(NC, NR).astype(np.int16)
        for g in range(6):
            S = pm(g, Sc); t = int(tg[g][tc])
            if (S, t) in H: continue
            fo = np.empty((NC, NR), np.int16); ho = np.empty((NC, NR), np.int16)
            fo[:, omap[g][tc]] = f; ho[:, omap[g][tc]] = h
            H[(S, t)] = (fo[:, orb[t]], ho[:, orb[t]])
print("relevant actual states:", len(H), flush=True)
FULL = (1 << NP) - 1
def hv(S, t, c):
    if S == FULL:              # last phi trail: the suffix is the end chain of the remaining 6 - c A trails
        a = 6 - c; rows = slice(t * NO, (t + 1) * NO)
        return np.zeros(NO, np.int16) if a == 0 else Qa[a - 1, rows]
    x = H.get((S, t))
    if x is None: return None
    f, h = x
    if (f[c] + h[6 - c]).min() > THR: return None
    return h[6 - c]
def blk(M, a, t, u): return M[a][t * NO:(t + 1) * NO, u * NO:(u + 1) * NO]
EDC = {}
def edir(t, u):
    k = (t, u)
    if k not in EDC: EDC[k] = np.asarray(Ed[t * NO:(t + 1) * NO, u * NO:(u + 1) * NO], np.int16)
    return EDC[k]
TC = {}
def tmat(kind, t, u, dat):
    k = (kind, t, u, dat)
    if k not in TC:
        if kind == 1: M = blk(T1, dat, t, u)
        elif kind == 2: M = blk(T2, dat[0] * 6 + dat[1], t, u)
        else: M = blk(Ka, dat - 1, t, u)
        TC[k] = np.asarray(M, np.int16)
    return TC[k]
ALL = frozenset(range(6))
def moves(avail, a):
    if a == 0: return [(frozenset(), 0, None)]
    if a == 1: return [(frozenset([x]), 1, x) for x in sorted(avail)]
    if a == 2: return [(frozenset([x, y]), 2, (x, y)) for x in sorted(avail) for y in sorted(avail) if x != y]
    return [(frozenset(c), 3, a) for c in itertools.combinations(sorted(avail), a)]
t0 = time.time()
states = {}; BP = {}; LAYERS = []
for t in range(NP):
    rows = slice(t * NO, (t + 1) * NO)
    for a in range(7):
        h = hv(1 << t, t, a)
        if h is None: continue
        for Aset, kind, dat in moves(ALL, a):
            if kind == 0: v = (cut[topts[t]] == 2).astype(np.int16)
            elif kind == 1: v = S1x[dat, rows]
            elif kind == 2: v = S2x[dat[0] * 6 + dat[1], rows]
            else: v = Sa[a - 1, rows]
            v = np.where(v + h <= THR, v, INF).astype(np.int16)
            if v.min() >= INF: continue
            key = (1 << t, t, Aset); old = states.get(key)
            if old is None: states[key] = v; BP[key] = [(None, -1, kind, dat, a)] * NO
            else:
                imp = np.nonzero(v < old)[0]; states[key] = np.minimum(old, v)
                for o in imp: BP[key][o] = (None, -1, kind, dat, a)
print("layer 1 states", len(states), round(time.time() - t0, 1), flush=True)
stats = []; used_long = 0
for k in range(1, NP):
    nxt = {}; nbp = {}; ntr = 0
    LAYERS.append((states, BP))
    for (S, t, Am), v in states.items():
        c = len(Am); avail = ALL - Am; live = np.nonzero(v < INF)[0]; vl = v[live][:, None]
        for u in range(NP):
            if S >> u & 1: continue
            S2_ = S | 1 << u
            for a in range(0, 7 - c):
                h = hv(S2_, u, c + a)
                if h is None: continue
                M0 = edir(t, u) if a == 0 else tmat(3, t, u, a)
                if ((vl + M0[live]).min(0) + h).min() > THR: continue
                for Aset, kind, dat in moves(avail, a):
                    M = M0 if kind in (0, 3) else tmat(kind, t, u, dat)
                    w = (vl + M[live]).min(0); ntr += 1
                    if (w + h).min() > THR: continue
                    w = np.where(w + h <= THR, w, INF).astype(np.int16)
                    if kind == 3: used_long += 1
                    key = (S2_, u, Am | Aset); old = nxt.get(key)
                    am = (vl + M[live]).argmin(0)
                    if old is None:
                        nxt[key] = w; nbp[key] = [((S, t, Am), int(live[am[o]]), kind, dat, a) for o in range(NO)]
                    else:
                        imp = np.nonzero(w < old)[0]; nxt[key] = np.minimum(old, w)
                        for o in imp: nbp[key][o] = ((S, t, Am), int(live[am[o]]), kind, dat, a)
    states = nxt; BP = nbp
    stats.append(dict(layer=k + 1, states=len(states), transitions=ntr))
    print("layer", k + 1, "states", len(states), "transitions", ntr, round(time.time() - t0, 1), flush=True)
best = None; sols = []
for (S, u, Am), v in states.items():
    rest = sorted(ALL - Am); a = len(rest); rows = slice(u * NO, (u + 1) * NO)
    if a == 0: ends = [((), np.zeros(NO, np.int16), "exact")]
    elif a == 1: ends = [((rest[0],), Q1x[rest[0], rows], "exact")]
    elif a == 2: ends = [((x, y), Q2x[x * 6 + y, rows], "exact") for x in rest for y in rest if x != y]
    else: ends = [(tuple(rest), Qa[a - 1, rows], "bound")]
    for seq, ev, kind in ends:
        m = int((v.astype(np.int32) + ev).min())
        if best is None or m < best: best = m
        if m <= THR:
            o = int((v.astype(np.int32) + ev).argmin()); path = []; key = (S, u, Am); bp = BP
            li = len(LAYERS)
            while key is not None:
                pk, po, kd, dt, aa = bp[key][o]
                path.append(dict(phi=phit[key[1]], opt=int(topts[key[1]][o]), gap_kind=kd, gap=(dt if kd != 1 else Aid[dt]) if kd != 2 else [Aid[dt[0]], Aid[dt[1]]], gap_len=aa, Aset=sorted(Aid[i] for i in key[2])))
                key = pk; o = po
                if key is not None: li -= 1; bp = LAYERS[li][1]
            sols.append(dict(last=phit[u], end_chain=[Aid[i] for i in seq], end_kind=kind, value=m, path=path[::-1]))
res = dict(THR=THR, minimum=best, n_final_states=len(states), long_chain_transitions_kept=used_long, layers=stats,
           solutions_le_thr=sorted(sols, key=lambda d: d["value"])[:200], n_solutions=len(sols), sec=round(time.time() - t0, 1))
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(dict(THR=THR, minimum=best, n_final_states=len(states), n_solutions=len(sols), long_kept=used_long)), flush=True)
