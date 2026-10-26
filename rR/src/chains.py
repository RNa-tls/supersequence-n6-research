#!/usr/bin/env python3
"""Round R -- chain structure of every trail version.  A chain is a maximal w2 segment of the version cycle; it is
FULL when its 7 runs close into a w2 7-cycle (the wrap C_6 -> C_0 has weight 2) and a PATH chain otherwise.
For every option o (global index tofs[t] + v * m_t + k) returns chain id, position, chain length, full flag, and
cut weight c(o) = W[pred(o), o] (2 inside a chain, 3 at a chain start)."""
import numpy as np

def chain_info(W, tofs, mlen):
    N = W.shape[0]
    cid = np.full(N, -1, np.int64); pos = np.zeros(N, np.int64); clen = np.zeros(N, np.int64); full = np.zeros(N, bool)
    cut = np.zeros(N, np.int64); chains = []
    for t in range(30):
        m = mlen[t]
        for v in range(2):
            o0 = tofs[t] + v * m
            c = [int(W[o0 + (k - 1) % m, o0 + k]) for k in range(m)]
            assert set(c) <= {2, 3}, (t, v, set(c))
            for k in range(m): cut[o0 + k] = c[k]
            starts = [k for k in range(m) if c[k] == 3]
            for i, s in enumerate(starts):
                e = starts[(i + 1) % len(starts)]; L = (e - s) % m or m
                runs = [o0 + (s + j) % m for j in range(L)]
                isfull = L == 7 and W[runs[-1], runs[0]] == 2
                for j, r in enumerate(runs): cid[r] = len(chains); pos[r] = j; clen[r] = L; full[r] = isfull
                chains.append(dict(t=t, v=v, start=s, runs=runs, full=bool(isfull)))
    return dict(cid=cid, pos=pos, clen=clen, full=full, cut=cut, chains=chains)
