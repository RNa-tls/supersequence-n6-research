#!/usr/bin/env python3
"""Round R -- probe: dissolve one trail of a word into its full chains (7-run w2 cycles) and re-insert every chain,
rotated, at the best place of the remaining route (greedy, then repeated best-improvement re-insertion of single
chains).  Works purely on runs: the word's route is a Hamiltonian path of its 5040 runs, length = 8 + 7 N + sum w.
A chain entered at run c_j is traversed c_j .. c_6, c_0 .. c_{j-1} (6 internal w2 links, the wrap included).
Non-full chains of the dissolved trail (A trails) stay in one block in the remainder (version order) placed greedily.
Prints the exact length of the resulting word (rebuilt and checked for all 40320 permutations when it improves).
usage: dissolve_probe.py WORD TRAIL_ID|all FAMILY.json [OUT.txt]"""
import sys, json
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
def canon(p): return min(p[i:] + p[:i] for i in range(n))

def build(st, W, seq):
    w = list(st[seq[0]])
    for k, r in enumerate(seq):
        if k > 0: kk = int(W[seq[k - 1], r]); w += list(st[r][8 - kk:])
        w += list(st[r][:7])
    return w

def main():
    st = starts(load_word(sys.argv[1])); N = len(st); fam = json.load(open(sys.argv[3]))
    cls_trail = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            for k in range(len(s) // 8): cls_trail[canon(tuple(int(c) for c in s[8 * k:8 * k + 8]))] = t
    trail = np.array([cls_trail[canon(s)] for s in st])
    S = np.array(st, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)
    W = np.full((N, N), 8, np.int64)
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
        W[a[:, None] == b[None, :]] = k
    np.fill_diagonal(W, 8)
    def L(seq): return 8 + 7 * len(seq) + int(W[np.array(seq[:-1]), np.array(seq[1:])].sum())
    base = list(range(N)); L0 = L(base)
    targets = range(30) if sys.argv[2] == "all" else [int(sys.argv[2])]
    results = []; best_overall = (L0, None)
    for T in targets:
        runsT = [r for r in base if trail[r] == T]; setT = set(runsT)
        # w2 successor among T's runs
        succ = {}
        for r in runsT:
            s = [q for q in runsT if W[r, q] == 2]
            if len(s) == 1: succ[r] = s[0]
        chains = []; seen = set()
        for r in runsT:
            if r in seen: continue
            c = [r]; q = succ.get(r)
            while q is not None and q != r and q not in seen and len(c) < 8: c.append(q); q = succ.get(q)
            if q == r and len(c) == 7: chains.append(c); seen.update(c)
        rest = [r for r in runsT if r not in seen]          # runs of non-full chains, in word order
        path = [r for r in base if r not in setT]
        def ins_cost(path, seg_in, seg_out, pos):
            if pos == 0: return int(W[seg_out, path[0]])
            if pos == len(path): return int(W[path[-1], seg_in])
            return int(W[path[pos - 1], seg_in] + W[seg_out, path[pos]] - W[path[pos - 1], path[pos]])
        def best_insert(path, cyc):
            best = None
            P = np.array(path)
            for j in range(7):
                seg = cyc[j:] + cyc[:j]
                c = np.empty(len(path) + 1, np.int64)
                c[1:-1] = W[P[:-1], seg[0]] + W[seg[-1], P[1:]] - W[P[:-1], P[1:]]
                c[0] = W[seg[-1], P[0]]; c[-1] = W[P[-1], seg[0]]
                k = int(np.argmin(c))
                if best is None or c[k] < best[0]: best = (int(c[k]), k, seg)
            return best
        # remainder block (non-full chains), kept in word order, inserted greedily as one segment
        if rest:
            Pn = np.array(path); c = np.empty(len(path) + 1, np.int64)
            c[1:-1] = W[Pn[:-1], rest[0]] + W[rest[-1], Pn[1:]] - W[Pn[:-1], Pn[1:]]; c[0] = W[rest[-1], Pn[0]]; c[-1] = W[Pn[-1], rest[0]]
            k = int(np.argmin(c)); path = path[:k] + rest + path[k:]
        order = sorted(chains, key=lambda cyc: best_insert(path, cyc)[0])
        for cyc in order:
            d, k, seg = best_insert(path, cyc); path = path[:k] + seg + path[k:]
        # improvement: remove and re-insert single chains while it helps
        improved = True; rounds = 0
        while improved and rounds < 50:
            improved = False; rounds += 1
            for cyc in chains:
                cs = set(cyc); idx = [i for i, r in enumerate(path) if r in cs]
                i0 = idx[0]; seg = path[i0:i0 + 7]
                if sorted(seg) != sorted(cyc): continue          # chain was split by another insertion
                p2 = path[:i0] + path[i0 + 7:]
                cur = L(path); d, k, sg = best_insert(p2, cyc); cand = p2[:k] + sg + p2[k:]
                if L(cand) < cur: path = cand; improved = True
        assert sorted(path) == list(range(N))
        Lt = L(path); results.append(dict(trail=T, full_chains=len(chains), rest_runs=len(rest), length=Lt, G=Lt - 46162))
        print(json.dumps(results[-1])); sys.stdout.flush()
        if Lt < best_overall[0]: best_overall = (Lt, path)
    print(json.dumps(dict(word=sys.argv[1], base_length=L0, best_length=best_overall[0])))
    if len(sys.argv) > 4 and best_overall[1] is not None:
        w = build(st, W, best_overall[1]); ok = len({tuple(w[i:i + 8]) for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8}) == 40320
        open(sys.argv[4], "w").write("".join(str(c + 1) for c in w) + "\n"); print(json.dumps(dict(written=sys.argv[4], length=len(w), all_perms=ok)))

main()
