#!/usr/bin/env python3
"""Round Q, section 22 -- compound "wrap excision" moves on a single-opening r = 0 word (exact, run level).

For a trail T (contiguous block in the word, single opening) and a FULL chain C of T (w2 cycle of 7 runs) and a
run a1 of C, replace T by two visits:
    V1 = C alone, entered at a1 and traversed a1 .. C_end, C_start .. a1-1 (uses the w2 wrap C_end -> C_start),
    V2 = R = T minus C, in version order N_start .. Prev_end  (one fragment),
and place V1, V2 at any two gaps of the remaining route (V1 at T's old place, V2 anywhere; V2 at T's old place,
V1 anywhere; or both elsewhere).  Also the plain 2-split with a1 = C_start (V1 = C unrotated).
Every evaluated move is a valid multi-opening word of the family; the cost change is computed exactly from the run
weights (L = 35288 + sum w).  Prints the best moves.
usage: excision_probe.py WORD FAMILY.json OUT.json [WITNESS_OUT.txt [phi|A]]   (writes the word of the first best move, optionally of a phi / A trail)"""
import sys, json, math
import numpy as np

n = 8
def load_word(p):
    t = "".join(ch for ch in open(p).read() if not ch.isspace()); al = sorted(set(t)); return [al.index(c) for c in t]
def starts(w):
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j]
    return st
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
def last(p): return p[-1:] + p[:-1]
def canon(p): return min(p[i:] + p[:i] for i in range(n))

def main():
    st = starts(load_word(sys.argv[1])); N = len(st)
    fam = json.load(open(sys.argv[2]))
    cls_trail = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            for k in range(len(s) // 8): cls_trail[canon(tuple(int(c) for c in s[8 * k:8 * k + 8]))] = t
    trail = np.array([cls_trail[canon(s)] for s in st])
    S = np.array(st, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)
    # weight matrix over runs of the word (route order index)
    W = np.full((N, N), 8, np.int64)
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
        W[a[:, None] == b[None, :]] = k
    np.fill_diagonal(W, 8)
    route = list(range(N)); base = int(sum(W[route[i], route[i + 1]] for i in range(N - 1)))
    res = dict(word=sys.argv[1], L=35288 + base, moves=0, best=[])
    best = []
    def gaps_cost(rest, s, e):
        # cost of inserting block (s ... e) into each gap of rest (incl. both ends); rest is a list of run ids
        r = np.array(rest); u = np.concatenate([[-1], r]); v = np.concatenate([r, [-1]])
        c = np.zeros(len(u), np.int64)
        m = (u >= 0) & (v >= 0); c[m] = W[u[m], s] + W[e, v[m]] - W[u[m], v[m]]
        m1 = (u < 0) & (v >= 0); c[m1] = W[e, v[m1]]
        m2 = (u >= 0) & (v < 0); c[m2] = W[u[m2], s]
        return c
    def pathcost(seq): return int(sum(W[seq[i], seq[i + 1]] for i in range(len(seq) - 1)))
    blocks = []; i = 0
    while i < N:
        j = i
        while j + 1 < N and trail[j + 1] == trail[i]: j += 1
        blocks.append((i, j)); i = j + 1
    assert len(blocks) == 30, len(blocks)
    for (i0, j0) in blocks:
        T = route[i0:j0 + 1]; m = len(T)
        # chains of T in route order (= version order from the opening); find full chains with the wrap
        cut = [k for k in range(1, m) if W[T[k - 1], T[k]] != 2]
        segs = []; prev = 0
        for k in cut + [m]: segs.append(T[prev:k]); prev = k
        # the first and last segments may be two halves of one chain (opening inside a chain)
        if W[T[-1], T[0]] == 2 and len(segs) > 1:
            segs = [segs[-1] + segs[0]] + segs[1:-1]; rot = True
        else: rot = False
        # version-cyclic order of chains: T read cyclically from its first full chain start
        cyc = []
        for sg in segs: cyc.append(sg)
        # rebuild version cycle as a run list starting at the first chain of cyc
        vc = [r for sg in cyc for r in sg]; mv = len(vc)
        pos = {r: k for k, r in enumerate(vc)}
        outside = route[:i0] + route[j0 + 1:]
        p_ = route[i0 - 1] if i0 > 0 else -1; n_ = route[j0 + 1] if j0 + 1 < N else -1
        old = pathcost(T) + (W[p_, T[0]] if p_ >= 0 else 0) + (W[T[-1], n_] if n_ >= 0 else 0) - (W[p_, n_] if p_ >= 0 and n_ >= 0 else 0)
        for ci, C in enumerate(cyc):
            if len(C) != 7 or W[C[-1], C[0]] != 2: continue          # full chains only
            k0 = pos[C[0]]; R = [vc[(k0 + 7 + t) % mv] for t in range(mv - 7)]
            costR = pathcost(R)
            for a in range(7):
                V1 = C[a:] + C[:a]; costV1 = pathcost(V1)
                # option A: V1 at T's place, R anywhere in (outside with V1 inserted)
                restA = route[:i0] + V1 + route[j0 + 1:]
                cA = gaps_cost(restA, R[0], R[-1]); kA = int(np.argmin(cA))
                dA = (costV1 + (W[p_, V1[0]] if p_ >= 0 else 0) + (W[V1[-1], n_] if n_ >= 0 else 0) - (W[p_, n_] if p_ >= 0 and n_ >= 0 else 0)) + costR + int(cA[kA]) - old
                # option B: R at T's place, V1 anywhere
                restB = route[:i0] + R + route[j0 + 1:]
                cB = gaps_cost(restB, V1[0], V1[-1]); kB = int(np.argmin(cB))
                dB = (costR + (W[p_, R[0]] if p_ >= 0 else 0) + (W[R[-1], n_] if n_ >= 0 else 0) - (W[p_, n_] if p_ >= 0 and n_ >= 0 else 0)) + costV1 + int(cB[kB]) - old
                res["moves"] += 2
                for d, kind, k, rest, blk in ((dA, "V1_in_place", kA, restA, R), (dB, "R_in_place", kB, restB, V1)):
                    best.append((int(d), dict(trail=int(trail[i0]), chain_index=ci, a=a, kind=kind, gap=k, R_len=len(R)), (rest, blk, k)))
    best.sort(key=lambda x: x[0])
    res["best"] = [dict(delta=d, **info) for d, info, _ in best[:20]]
    if len(sys.argv) > 4:
        want = sys.argv[5] if len(sys.argv) > 5 else None
        isA = lambda tr: len(fam["trails"][tr]["versions"][0]) // 8 > 100
        cand = [b for b in best if want is None or (want == "A") == isA(b[1]["trail"])]
        d0, info0, (rest, blk, k) = cand[0]
        newroute = rest[:k] + blk + rest[k:]
        assert sorted(newroute) == list(range(N))
        w = list(st[newroute[0]])
        for i, r in enumerate(newroute):
            if i > 0: kk = W[newroute[i - 1], r]; w += list(st[r][8 - kk:])
            w += list(st[r][:7])
        open(sys.argv[4], "w").write("".join(str(c + 1) for c in w) + "\n")
        res["witness"] = dict(delta=d0, length=len(w), file=sys.argv[4], **info0)
    res["best_delta"] = best[0][0]
    hist = {}
    for d, _, _ in best: hist[d] = hist.get(d, 0) + 1
    res["delta_hist"] = {str(k): hist[k] for k in sorted(hist)[:12]}
    json.dump(res, open(sys.argv[3], "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("word", "L", "moves", "best_delta", "delta_hist")}), res.get("witness"))
    print(res["best"][:5])

main()
