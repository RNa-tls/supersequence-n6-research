#!/usr/bin/env python3
"""Round P -- cross-check of the two backward tables.
Checker A's reversed DP value h (relevant_kXX.bin, canonical min-key records, orbits from symprep.json) and
checker B's backward value H (ckB.c, canonical max-key layers) must agree option by option on every
relevant actual state (S, t): both are the exact relaxed cost of completing the word after phi trail t.
Step 1 (this script, mode 'queries'): expand A's records to actual states, write QUERY (uint32 S, t) and
A's option-level values.  Step 2: ckB_search answers the queries (env CKB_QUERY / CKB_QOUT).
Step 3 (mode 'compare'): compare entry by entry (A stores values above its cap as the cap).
usage: cmpAB_h.py queries PDPDIR RELDIR WORKDIR  |  cmpAB_h.py compare WORKDIR"""
import sys, os, json
import numpy as np
NP, NR, NC, NO = 24, 42, 7, 84

def queries(D, RD, W):
    trail = np.fromfile(f"{D}/trail.bin", np.int32); Nopt = len(trail)
    sp = json.load(open(f"{RD}/symprep.json")); phit = sp["phit"]; rep = np.array(sp["rep"])
    topts = [np.nonzero(trail == t)[0] for t in phit]
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
    seen = {}; Q = []; V = []
    for k in range(1, NP + 1):
        fn = f"{RD}/relevant_k{k:02d}.bin"
        if not os.path.exists(fn): continue
        raw = np.fromfile(fn, np.uint8).reshape(-1, 8 + 2 * NC * NR)
        for r in raw:
            key = int(np.frombuffer(r[:8].tobytes(), np.uint64)[0]); tc = key & 31; Sc = unrank(key >> 5, k)
            h = r[8 + NC * NR:].reshape(NC, NR)
            for g in range(6):
                S = pm(g, Sc); t = int(tg[g][tc])
                if (S, t) in seen: continue
                ho = np.empty((NC, NR), np.uint8); ho[:, omap[g][tc]] = h
                seen[(S, t)] = 1; Q.append((S, t)); V.append(ho[:, orb[t]])
    os.makedirs(W, exist_ok=True)
    np.array(Q, np.uint32).tofile(f"{W}/query.bin"); np.array(V, np.uint8).tofile(f"{W}/hA.bin")
    print(json.dumps(dict(actual_states=len(Q))))

def compare(W):
    A = np.fromfile(f"{W}/hA.bin", np.uint8).reshape(-1, NC, NO).astype(np.int32)
    B = np.fromfile(f"{W}/hB.bin", np.uint8).reshape(-1, NC, NO).astype(np.int32)
    assert A.shape == B.shape
    capA = int(A.max())
    both = (A < capA) & (B < capA)
    mism = int(((A != B) & both).sum())
    onlyA = int(((A < capA) & (B >= capA)).sum()); onlyB = int(((B < capA) & (A >= capA)).sum())
    low = (np.minimum(A, B) <= 23)
    mism_low = int(((A != B) & low).sum())
    print(json.dumps(dict(states=int(A.shape[0]), entries=int(A.size), A_cap=capA, compared_entries=int(both.sum()), mismatches=mism,
                          A_finite_B_capped=onlyA, B_finite_A_capped=onlyB, mismatches_with_min_le_23=mism_low,
                          min_value=int(np.minimum(A, B).min()))))

if __name__ == "__main__":
    if sys.argv[1] == "queries": queries(*sys.argv[2:5])
    else: compare(sys.argv[2])
