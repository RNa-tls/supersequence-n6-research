#!/usr/bin/env python3
"""Round L (section 25) -- permutation-level Or-opt neighbourhood of a superpermutation route (r >= 0).

A route is the list of the n! permutations in first-occurrence order; L = n + sum w(consecutive).
Move: cut a contiguous block route[p..q] (1 <= q-p+1 <= LMAX) and re-insert it between route[r] and
route[r+1] (r outside the block).  Exact delta:
   [w(route[p-1], route[q+1]) - w(route[p-1], route[p]) - w(route[q], route[q+1])]
 + [w(route[r], route[p]) + w(route[q], route[r+1]) - w(route[r], route[r+1])].
Candidate generation is exhaustive for insertion weights w(route[r], route[p]) <= MAXW (block starts
are the perms reachable from route[r] with weight <= MAXW), every block length <= LMAX.
Modes: 'scan' (histogram of deltas, all moves with delta <= 0), 'walk' (plateau walk: apply a random
delta <= 0 move not undoing a recent one, stop on delta < 0 and save the word).
Every word written is re-read and re-measured from scratch (independent of the delta formula).
usage: perm_oropt.py WORD scan|walk [MAXW] [LMAX] [steps] [seed]"""
import sys, os, json, math, time, random, itertools
from collections import Counter

def load(path):
    w = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(w)); mp = {c: i for i, c in enumerate(al)}
    return [mp[c] for c in w], len(al)

def make_wt(n):
    def wt(x, y):
        for j in range(n - 1, 0, -1):
            if x[n - j:] == y[:j]: return n - j
        return n
    return wt

def route_of(w, n):
    seen = set(); out = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); out.append(p)
    return out

def word_of(route, n, wt):
    out = list(route[0])
    for x, y in zip(route, route[1:]):
        c = wt(x, y); out.extend(y[n - c:])
    return out

def targets(x, n, wt, maxw):
    out = []
    for w_ in range(1, maxw + 1):
        for perm in itertools.permutations(x[:w_]):
            y = x[w_:] + perm
            if wt(x, y) == w_: out.append(y)
    return out

def scan(route, n, wt, MAXW, LMAX, want_all=False):
    N = len(route)
    pos = {p: i for i, p in enumerate(route)}
    W = [wt(route[i], route[i + 1]) for i in range(N - 1)]
    hist = Counter(); moves = []
    for r in range(N - 1):
        x = route[r]; y = route[r + 1]; c = W[r]
        for b0 in targets(x, n, wt, MAXW):
            p = pos.get(b0)
            if p is None or p == r + 1: continue
            w1 = wt(x, b0)
            for q in range(p, min(N, p + LMAX)):
                if p <= r <= q: break                      # insertion point inside the block
                if q == r: break
                ins = w1 + wt(route[q], y) - c
                if p == 0:
                    rem = -W[q] if q < N - 1 else 0
                elif q == N - 1:
                    rem = -W[p - 1]
                else:
                    if r == p - 1: continue                # same place
                    rem = wt(route[p - 1], route[q + 1]) - W[p - 1] - W[q]
                d = rem + ins
                hist[d] += 1
                if d <= 0: moves.append((d, p, q, r))
    return hist, moves, sum(W) + n

def apply(route, p, q, r):
    blk = route[p:q + 1]
    rest = route[:p] + route[q + 1:]
    rr = r if r < p else r - (q - p + 1)
    return rest[:rr + 1] + blk + rest[rr + 1:]

def main():
    path, mode = sys.argv[1], sys.argv[2]
    MAXW = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    LMAX = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    steps = int(sys.argv[5]) if len(sys.argv) > 5 else 50
    seed = int(sys.argv[6]) if len(sys.argv) > 6 else 0
    w, n = load(path); wt = make_wt(n)
    route = route_of(w, n); assert len(route) == math.factorial(n)
    L0 = n + sum(wt(route[i], route[i + 1]) for i in range(len(route) - 1)); assert L0 == len(w)
    t0 = time.time()
    if mode == "scan":
        hist, moves, L = scan(route, n, wt, MAXW, LMAX)
        print(json.dumps(dict(file=os.path.basename(path), L=L, maxw=MAXW, lmax=LMAX,
                              hist={str(k): v for k, v in sorted(hist.items()) if k <= 3},
                              nonpositive=len(moves), improving=[m for m in moves if m[0] < 0][:20],
                              sec=round(time.time() - t0, 1))), flush=True)
        return
    rng = random.Random(seed); tabu = []; L = L0
    for step in range(steps):
        hist, moves, L = scan(route, n, wt, MAXW, LMAX)
        imp = [m for m in moves if m[0] < 0]
        if imp:
            d, p, q, r = min(imp)
            route = apply(route, p, q, r)
            word = word_of(route, n, wt)
            out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"oropt_{len(word)}.txt")
            open(out, "w").write("".join(str(c + 1) for c in word) + "\n")
            chk = route_of(word, n)
            print(json.dumps(dict(step=step, improved=True, L=len(word), all_perms=len(chk) == math.factorial(n), file=out)), flush=True)
            return
        cand = [m for m in moves if (m[1], m[2], m[3]) not in tabu and route[m[1]] not in tabu]
        if not cand:
            print(json.dumps(dict(step=step, stuck=True))); return
        d, p, q, r = rng.choice(cand)
        tabu.append(route[p]); tabu = tabu[-200:]
        route = apply(route, p, q, r)
        Lc = n + sum(wt(route[i], route[i + 1]) for i in range(len(route) - 1))
        print(json.dumps(dict(step=step, L=Lc, neutral=len(moves), moved=[p, q, r], sec=round(time.time() - t0, 1))), flush=True)

if __name__ == "__main__":
    main()
