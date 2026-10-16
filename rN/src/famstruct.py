#!/usr/bin/env python3
"""Round N -- run / chain structure of a closed-trail family for a given VERSION VECTOR.

Run = start perm s (its 8 left rotations).  last(s) = s7 s0..s6.  w(s -> t) = w(last(s), t).
F-successor of a run: F(s) = s1..s6 s0 s7 (the unique t != rotation with w = 2).
A family chain is a maximal sequence of trail edges of weight 2; a chain is FULL when it has 7 runs
and the F-successor of its last run is its first run (closed F-cycle), otherwise SHORT.
Positions: chain c of trail T, position 1 = the run entered by the trail link (w = 3 edge).
Self-contained (reads only the family JSON)."""
import json, itertools
from collections import defaultdict

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
def F(s): return s[1:7] + (s[0], s[7])

class Fam:
    def __init__(self, path, vers=None):
        fam = json.load(open(path))
        self.T = len(fam["trails"])
        self.vers = [0] * self.T if vers is None else list(vers)
        self.runs = []          # run index -> start tuple
        self.info = []          # run index -> (trail, idx in trail cycle)
        self.trail_runs = []    # trail -> list of run indices (cyclic order)
        self.idx = {}           # start tuple -> run index
        for t, tr in enumerate(fam["trails"]):
            s = tr["versions"][self.vers[t]]
            st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            lst = []
            for k, p in enumerate(st):
                r = len(self.runs); self.runs.append(p); self.info.append((t, k)); self.idx[p] = r; lst.append(r)
            self.trail_runs.append(lst)
        self.N = len(self.runs)
        # chains
        self.chain_of = [None] * self.N; self.pos = [None] * self.N
        self.chains = []        # chain id -> dict(trail, runs, full)
        self.trail_chains = []
        for t, lst in enumerate(self.trail_runs):
            m = len(lst)
            ew = [wt(last(self.runs[lst[k - 1]]), self.runs[lst[k]]) for k in range(m)]   # weight of edge (k-1 -> k)
            assert all(w in (2, 3) for w in ew), "trail edge weight not 2/3"
            heads = [k for k in range(m) if ew[k] == 3]
            tc = []
            for h_i, h in enumerate(heads):
                nxt = heads[(h_i + 1) % len(heads)]
                ks = [(h + j) % m for j in range((nxt - h) % m or m)]
                rr = [lst[k] for k in ks]
                full = len(rr) == 7 and F(self.runs[rr[-1]]) == self.runs[rr[0]]
                cid = len(self.chains)
                self.chains.append(dict(trail=t, runs=rr, full=full, ord=h_i))
                for j, r in enumerate(rr): self.chain_of[r] = cid; self.pos[r] = j + 1
                tc.append(cid)
            self.trail_chains.append(tc)
    def fsucc(self, r):
        return self.idx.get(F(self.runs[r]))
    def succ_w(self, r, w):
        """run indices t with w(last(runs[r]), runs[t]) == w exactly"""
        x = last(self.runs[r]); out = []
        for perm in itertools.permutations(x[:w]):
            y = x[w:] + perm
            if wt(x, y) != w: continue
            j = self.idx.get(y)
            if j is not None: out.append(j)
        return out
    def W(self, a, b): return wt(last(self.runs[a]), self.runs[b])
