#!/usr/bin/env python3
"""Round M (section 17) -- EXHAUSTIVE exact local neighbourhoods of an r = 0 word at the RUN level.

The word is a Hamiltonian path of runs (fixed starts); cost = sum of inter-run weights.  Checked
exhaustively (every move evaluated exactly, no candidate lists):
  OR(l):   move any segment of l consecutive runs (1 <= l <= LMAX) to any other position
           (no reversal: the instance is asymmetric);
  SWAP(l1,l2): exchange two ADJACENT segments of lengths l1, l2 <= SMAX (A B C D -> A C B D);
  START:   re-choose the start rotation of every class for the fixed class order (cluster_opt)
           is checked separately by cluster_opt.py.
The path is closed through a depot with zero-cost arcs, so moves at the ends are included.
Prints the best (most negative) cost change of every family of moves; a value >= 0 certifies that
the word is a local optimum of that neighbourhood.
usage: local_exact.py WORD [LMAX] [SMAX]"""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def main():
    word = sys.argv[1]; LMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    SMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    t0 = time.time()
    st = RA.starts_of_word(RA.load_word(word)); N = len(st)
    W = RA.weight_matrix(st).astype(np.int64)
    # cyclic tour with depot (index N): positions 0..N, tour[pos]
    Wd = np.zeros((N + 1, N + 1), np.int64); Wd[:N, :N] = W
    tour = np.arange(N + 1)                   # tour = runs 0..N-1 in order, then the depot
    M = N + 1
    nxt = np.roll(tour, -1)
    arc = Wd[tour, nxt]                       # arc[p] = cost of tour[p] -> tour[p+1]
    base = int(arc.sum())
    best_or = (0, None); cnt = 0
    for l in range(1, LMAX + 1):
        for i in range(M):
            # segment = positions i .. i+l-1 (cyclic), must not contain all but 1 node
            j = (i + l - 1) % M
            p = (i - 1) % M; q = (j + 1) % M
            Bf, Bl = tour[i], tour[j]; P, Q = tour[p], tour[q]
            rem = Wd[P, Bf] + Wd[Bl, Q] - Wd[P, Q]
            # insertion between positions k, k+1 for k outside [p .. j] (k = p is the identity)
            ks = (np.arange(q, q + M - l - 1) % M)          # k = q .. p-1 (cyclic)
            a_, b_ = tour[ks], tour[(ks + 1) % M]
            delta = Wd[a_, Bf] + Wd[Bl, b_] - Wd[a_, b_] - rem
            cnt += len(ks)
            k = int(np.argmin(delta)); d = int(delta[k])
            if d < best_or[0]: best_or = (d, dict(l=l, i=int(i), k=int(ks[k])))
    best_sw = (0, None); cnt2 = 0
    for l1 in range(1, SMAX + 1):
        for l2 in range(1, SMAX + 1):
            # A B C D -> A C B D with B = [i, i+l1), C = [i+l1, i+l1+l2), cyclic positions
            i = np.arange(M)
            pa = (i - 1) % M; b0 = i; b1 = (i + l1 - 1) % M; c0 = (i + l1) % M; c1 = (i + l1 + l2 - 1) % M; d0 = (i + l1 + l2) % M
            if l1 + l2 >= M - 1: continue
            A_, B0, B1, C0, C1, D0 = tour[pa], tour[b0], tour[b1], tour[c0], tour[c1], tour[d0]
            delta = (Wd[A_, C0] + Wd[C1, B0] + Wd[B1, D0]) - (Wd[A_, B0] + Wd[B1, C0] + Wd[C1, D0])
            cnt2 += M
            k = int(np.argmin(delta)); d = int(delta[k])
            if d < best_sw[0]: best_sw = (d, dict(l1=l1, l2=l2, i=k))
    res = dict(word=word, cost=base, L=35288 + base, or_lmax=LMAX, or_moves=cnt, or_best=best_or[0], or_arg=best_or[1],
               swap_max=SMAX, swap_moves=cnt2, swap_best=best_sw[0], swap_arg=best_sw[1], sec=round(time.time() - t0, 1))
    print(json.dumps(res))

if __name__ == "__main__":
    main()
