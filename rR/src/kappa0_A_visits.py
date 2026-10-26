#!/usr/bin/env python3
"""Round R, section 12 -- every A single visit with kappa = 0, exactly.
Theorem R7: kappa(H) = (#maximal w2 segments - #chains) + sum_{non-w2 joins} (w - 3).  kappa = 0 iff every chain is one
w2 block (a full chain in any rotation a = 0..6: entry C_a, exit C_{a-1}; a path chain in natural order) and every join
between consecutive blocks has weight 3.  So the kappa = 0 single visits of a trail-version are exactly the Hamiltonian
paths of the block graph (one block per chain, arcs of weight 3 from a block exit to a block entry of another chain).
This program enumerates them all by depth-first search (each chain once), records every (entry y, exit x) pair, and
writes the kappa table that rQ/csrc/dominance.c reads (DOM_BOTH=1: a visit (y, x, 0) is dominated iff slack <= 0 in
every neighbour context, start and end contexts included).
usage: kappa0_A_visits.py RUNS.bin TRAIL VERSION OUT.json"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs); T0 = int(sys.argv[2]); V0 = int(sys.argv[3])
    W = runs_io.weight_matrix(runs); ci = chains.chain_info(W, tofs, mlen)
    m = mlen[T0]; o0 = tofs[T0] + V0 * m
    chs = sorted([c for c in ci["chains"] if c["t"] == T0 and c["v"] == V0], key=lambda c: c["start"]); nC = len(chs)
    # blocks: (chain index, phase) -> (entry run, exit run)
    blocks = []
    for i, c in enumerate(chs):
        rr = c["runs"]
        if c["full"]:
            for a in range(7): blocks.append((i, a, rr[a], rr[(a - 1) % 7]))
        else: blocks.append((i, 0, rr[0], rr[-1]))
    nb = len(blocks); out_arcs = [[] for _ in range(nb)]
    for p, (i, a, en, ex) in enumerate(blocks):
        for q, (j, b, en2, ex2) in enumerate(blocks):
            if j != i and W[ex, en2] == 3: out_arcs[p].append(q)
    by_chain = [[p for p, b in enumerate(blocks) if b[0] == i] for i in range(nC)]
    # in-degree pruning: a chain with no in-arc into any of its blocks must be first; with no out-arc, last
    has_in = [False] * nC; has_out = [False] * nC
    for p in range(nb):
        for q in out_arcs[p]: has_in[blocks[q][0]] = True; has_out[blocks[p][0]] = True
    pairs = {}; npaths = 0; t0 = time.time(); nodes = 0
    sys.setrecursionlimit(10000)
    used = [False] * nC
    def dfs(p, depth, start):
        nonlocal npaths, nodes
        nodes += 1
        if depth == nC:
            key = (blocks[start][2], blocks[p][3]); pairs[key] = pairs.get(key, 0) + 1; npaths += 1; return
        for q in out_arcs[p]:
            j = blocks[q][0]
            if used[j]: continue
            used[j] = True; dfs(q, depth + 1, start); used[j] = False
    for s in range(nb):
        i = blocks[s][0]
        used[i] = True; dfs(s, 1, s); used[i] = False
    # kappa table for rQ/csrc/dominance.c: m x m int8, 99 = absent, -1 diagonal, single pieces (k, k-1) = 3 - c_k,
    # every kappa = 0 visit pair (y, x) = 0 (dominated iff slack(y, x) <= 0)
    K = np.full((m, m), 99, np.int8)
    for k in range(m): K[k, k] = -1; K[k, (k - 1) % m] = 3 - int(W[o0 + (k - 1) % m, o0 + k])
    loc = {o0 + k: k for k in range(m)}; nonstd = 0
    for (y, x) in pairs:
        ky, kx = loc[y], loc[x]
        if kx == (ky - 1) % m or kx == ky: continue
        K[ky, kx] = 0; nonstd += 1
    K.tofile(sys.argv[4] + ".kappa.bin")
    res = [dict(y=int(loc[y]), x=int(loc[x]), paths=int(c)) for (y, x), c in pairs.items()]
    out = dict(trail=T0, version=V0, runs=m, chains=nC, blocks=nb, block_arcs=int(sum(len(a) for a in out_arcs)),
               kappa0_paths=npaths, dfs_nodes=nodes, kappa0_pairs=len(pairs), nonstandard_pairs=nonstd, pairs=res[:200],
               sec=round(time.time() - t0, 1), kappa_table=sys.argv[4] + ".kappa.bin")
    print(json.dumps({k: v for k, v in out.items() if k != 'pairs'})); json.dump(out, open(sys.argv[4], "w"), indent=1)

main()
