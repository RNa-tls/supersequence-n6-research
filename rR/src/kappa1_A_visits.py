#!/usr/bin/env python3
"""Round R, section 12 -- every A single visit with kappa <= 1, exactly (Theorem R7 at the chain level).
kappa(H) = (#w2 segments - #chains) + sum_{non-w2 joins} (w - 3).  kappa = 1 means exactly one defect:
  (a) every chain is one block and exactly one join between consecutive blocks has weight 4 (all others weight 3);
  (b) exactly one chain is traversed as two w2 segments (a split; a full chain = two complementary arcs of its 7-cycle,
      a path chain = two intervals), every other chain is one block, every join has weight 3.
The visits are Hamiltonian paths over the blocks; all are enumerated by depth-first search.  The (entry, exit) pairs
are written as a kappa table for rQ/csrc/dominance.c (kappa = 0 pairs from kappa0_A_visits.py are the standard
options; here every non-standard pair of kappa <= 1 gets its least kappa).
usage: kappa1_A_visits.py RUNS.bin TRAIL VERSION OUT.json"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); T0 = int(sys.argv[2]); V0 = int(sys.argv[3])
    W = runs_io.weight_matrix(runs); ci = chains.chain_info(W, tofs, mlen)
    m = mlen[T0]; o0 = tofs[T0] + V0 * m
    chs = sorted([c for c in ci["chains"] if c["t"] == T0 and c["v"] == V0], key=lambda c: c["start"]); nC = len(chs)
    whole = []                                   # (chain, entry run, exit run)
    for i, c in enumerate(chs):
        rr = c["runs"]
        if c["full"]:
            for a in range(7): whole.append((i, rr[a], rr[(a - 1) % 7]))
        else: whole.append((i, rr[0], rr[-1]))
    def arcs_from(blocks, wset):
        ent = np.array([b[1] for b in blocks]); out = []
        for (i, en, ex) in blocks:
            row = W[ex, ent]; out.append([q for q in np.nonzero(np.isin(row, list(wset)))[0].tolist() if blocks[q][0] != i or True])
        return out
    best = {}                                    # (y, x) -> least kappa found (1)
    t0 = time.time(); paths = {"w4": 0, "split": 0}; nodes = [0]
    sys.setrecursionlimit(20000)
    # (a): whole blocks, one weight-4 join
    nb = len(whole); ent = np.array([b[1] for b in whole])
    a3 = [[q for q in np.nonzero(W[ex, ent] == 3)[0].tolist() if whole[q][0] != i] for (i, en, ex) in whole]
    a4 = [[q for q in np.nonzero(W[ex, ent] == 4)[0].tolist() if whole[q][0] != i] for (i, en, ex) in whole]
    used = [False] * nC
    def dfs_a(p, depth, start, d):
        nodes[0] += 1
        if depth == nC:
            if d == 1:
                k = (whole[start][1], whole[p][2]); best[k] = min(best.get(k, 9), 1); paths["w4"] += 1
            return
        for q in a3[p]:
            j = whole[q][0]
            if not used[j]: used[j] = True; dfs_a(q, depth + 1, start, d); used[j] = False
        if d == 0:
            for q in a4[p]:
                j = whole[q][0]
                if not used[j]: used[j] = True; dfs_a(q, depth + 1, start, 1); used[j] = False
    for s in range(nb):
        i = whole[s][0]; used[i] = True; dfs_a(s, 1, s, 0); used[i] = False
    na_nodes = nodes[0]
    # (b): one chain split into two segments
    for ci_, c in enumerate(chs):
        rr = c["runs"]; L = len(rr)
        splits = []
        if c["full"]:
            for i1 in range(7):
                for i2 in range(i1 + 1, 7):          # segments rr[i1..i2-1] and rr[i2..i1-1] (cyclic)
                    s1 = [rr[(i1 + k) % 7] for k in range((i2 - i1) % 7)]; s2 = [rr[(i2 + k) % 7] for k in range((i1 - i2) % 7)]
                    splits.append((s1, s2))
        else:
            for j in range(1, L): splits.append((rr[:j], rr[j:]))
        others = [b for b in whole if b[0] != ci_]
        for (s1, s2) in splits:
            blocks = others + [(ci_, s1[0], s1[-1]), (ci_ + 1000, s2[0], s2[-1])]      # the two halves count as two "chains"
            ent2 = np.array([b[1] for b in blocks])
            arc = [[q for q in np.nonzero(W[ex, ent2] == 3)[0].tolist() if blocks[q][0] != i] for (i, en, ex) in blocks]
            keys = sorted({b[0] for b in blocks}); kid = {k: n for n, k in enumerate(keys)}; nk = len(keys)
            used2 = [False] * nk
            def dfs_b(p, depth, start):
                nodes[0] += 1
                if depth == nk:
                    k = (blocks[start][1], blocks[p][2]); best[k] = min(best.get(k, 9), 1); paths["split"] += 1; return
                for q in arc[p]:
                    j = kid[blocks[q][0]]
                    if not used2[j]: used2[j] = True; dfs_b(q, depth + 1, start); used2[j] = False
            for s in range(len(blocks)):
                j = kid[blocks[s][0]]; used2[j] = True; dfs_b(s, 1, s); used2[j] = False
    K = np.full((m, m), 99, np.int8); loc = {o0 + k: k for k in range(m)}
    for k in range(m): K[k, k] = -1; K[k, (k - 1) % m] = 3 - int(W[o0 + (k - 1) % m, o0 + k])
    nonstd = 0
    for (y, x), kap in best.items():
        ky, kx = loc[y], loc[x]
        if kx == (ky - 1) % m or kx == ky: continue
        if kap < K[ky, kx] or K[ky, kx] == 99: K[ky, kx] = kap; nonstd += 1
    K.tofile(sys.argv[4] + ".kappa.bin")
    out = dict(trail=T0, version=V0, chains=nC, kappa1_paths=paths, kappa1_pairs=len(best), nonstandard_pairs_kappa1=nonstd,
               dfs_nodes_w4=na_nodes, dfs_nodes_total=nodes[0], sec=round(time.time() - t0, 1), kappa_table=sys.argv[4] + ".kappa.bin")
    print(json.dumps(out)); json.dump(out, open(sys.argv[4], "w"), indent=1)

main()
