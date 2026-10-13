#!/usr/bin/env python3
"""Round L (section 25) -- exhaustive classification of SINGLE-SPLIT hole gadgets on an r = 0 word.

Move family G1: pick one class C (run i, start s), split its run into two cyclic arcs A, B
(B = R^k s .. R^(k+m-1) s, A = the rest), keep A in place (prev -> A -> next) and insert B into
one inter-run join x -> y elsewhere (x = last perm of some run, y = next run start).
Move family G2: both arcs moved to two different joins, prev -> next bridged directly.
Length change (exact, L = n + sum of edge weights):
  G1: Delta = [w(pe,A0) + w(A1,ns) - w_in - w_out] + [w(x,B0) + w(B1,y) - w(x,y)] - 1
  G2: Delta = [w(pe,ns) - w_in - w_out] + delta_A + delta_B - 1
(-1 = 6 internal weight-1 edges instead of 7).  Every candidate with Delta <= 0 is rebuilt as an
explicit permutation route, re-measured from scratch, and reported.  A word with Delta < 0 would be
a new record (verified separately).
usage: split_gadgets.py WORD"""
import sys, os, json, math, time
from collections import Counter, defaultdict
n = 8

def load(path):
    w = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(w)); mp = {c: i for i, c in enumerate(al)}
    return [mp[c] for c in w]

def wt(x, y):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n

def R(p, k=1):
    k %= n; return p[k:] + p[:k]

def runs_of(w):
    seen = set(); order = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); order.append(p)
    starts = [order[i] for i in range(0, len(order), n)]
    for i in range(0, len(order), n):
        for k in range(1, n): assert order[i + k] == R(order[i + k - 1])
    return starts

def route_len(route):
    return n + sum(wt(route[i], route[i + 1]) for i in range(len(route) - 1))

def low_weight_targets(x, maxw):
    """perms y != rotation-class of x with w(x, y) <= maxw: suffix x[w:] + permutation of x[:w]"""
    import itertools
    out = []
    cx = {R(x, k) for k in range(n)}
    for w_ in range(2, maxw + 1):
        for perm in itertools.permutations(x[:w_]):
            y = x[w_:] + perm
            if y not in cx and wt(x, y) == w_: out.append((y, w_))
    return out

def low_weight_sources(y, maxw):
    import itertools
    out = []
    cy = {R(y, k) for k in range(n)}
    for w_ in range(2, maxw + 1):
        for perm in itertools.permutations(y[n - w_:]):
            x = perm + y[:n - w_]
            if x not in cy and wt(x, y) == w_: out.append((x, w_))
    return out

def main():
    path = sys.argv[1]; MAXW = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    t0 = time.time()
    w = load(path); S = runs_of(w); M = len(S)
    L0 = len(w)
    E = [R(s, n - 1) for s in S]                         # last perm of each run
    J = [wt(E[i], S[i + 1]) for i in range(M - 1)]
    assert L0 == n + 7 * M + sum(J)
    pos = {}
    for i, s in enumerate(S):
        for k in range(n): pos[R(s, k)] = (i, k)          # perm -> (run index, rotation offset)
    # candidate arcs B with cheap insertion into join j: B0 in low targets of E[j], B1 in low sources of S[j+1]
    best = Counter(); found = []
    def arc(i, k, m):                                     # arc of run i from offset k, m perms
        return [R(S[i], k + t) for t in range(m)]
    # precompute insertion deltas: for each join j and each arc (i,k,m) with B0 cheap from E[j]
    ins = defaultdict(list)                               # (i,k,m) -> list of (delta, j)
    for j in range(M - 1):
        for b0, w1 in low_weight_targets(E[j], MAXW):
            i, k = pos[b0]
            if i in (j, j + 1): continue
            for m in range(1, n):
                b1 = R(S[i], k + m - 1)
                w2 = wt(b1, S[j + 1])
                d = w1 + w2 - J[j]
                if d <= 3: ins[(i, k, m)].append((d, j))
    nins = sum(len(v) for v in ins.values())
    # G1: keep the complementary arc A in place
    cnt = Counter()
    for (i, k, m), lst in ins.items():
        A0 = R(S[i], k + m); A1 = R(S[i], k - 1)
        win = J[i - 1] if i > 0 else 0; wout = J[i] if i < M - 1 else 0
        a_in = wt(E[i - 1], A0) if i > 0 else 0
        a_out = wt(A1, S[i + 1]) if i < M - 1 else 0
        dA = a_in + a_out - win - wout
        for d, j in lst:
            D = dA + d - 1
            cnt[("G1", D)] += 1
            if D <= 0: found.append(("G1", D, i, k, m, j))
    # G2: both arcs moved, bridge prev -> next
    for (i, k, m), lst in ins.items():
        if i == 0 or i == M - 1: continue
        bridge = wt(E[i - 1], S[i + 1]) - J[i - 1] - J[i]
        lstA = ins.get((i, (k + m) % n, n - m), [])
        if not lstA: continue
        for dB, jB in lst:
            for dA_, jA in lstA:
                if jA == jB or abs(jA - jB) <= 0: continue
                if jA in (i - 1, i) or jB in (i - 1, i): continue
                D = bridge + dA_ + dB - 1
                cnt[("G2", D)] += 1
                if D <= 0: found.append(("G2", D, i, k, m, jB, jA))
    # rebuild and re-measure every candidate with D <= 0
    verified = []
    for g in found:
        if g[0] == "G1":
            _, D, i, k, m, j = g
            B = arc(i, k, m); A = arc(i, k + m, n - m)
            runs = []
            for t in range(M):
                if t == i: runs.append(A)
                else: runs.append(arc(t, 0, n))
                if t == j: runs.append(B)
        else:
            _, D, i, k, m, jB, jA = g
            B = arc(i, k, m); A = arc(i, k + m, n - m)
            runs = []
            for t in range(M):
                if t != i: runs.append(arc(t, 0, n))
                if t == jB: runs.append(B)
                if t == jA: runs.append(A)
        route = [p for r in runs for p in r]
        assert len(route) == math.factorial(n) and len(set(route)) == len(route)
        Lnew = route_len(route)
        verified.append(dict(kind=g[0], predicted=L0 + D, measured=Lnew, gadget=list(g[2:])))
    res = dict(file=os.path.basename(path), L=L0, maxw=MAXW, insertions=nins,
               delta_hist={f"{a}:{b}": v for (a, b), v in sorted(cnt.items(), key=lambda z: (z[0][0], z[0][1]))},
               nonpositive=len(found), best=min([v["measured"] for v in verified], default=None),
               verified=verified[:50], sec=round(time.time() - t0, 1))
    print(json.dumps(res))

if __name__ == "__main__":
    main()
