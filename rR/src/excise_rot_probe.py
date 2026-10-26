#!/usr/bin/env python3
"""Round R, sections 4/9/20 -- adversarial probe for the zero-charge mechanism on a given word:
EXCISE k consecutive full chains (7-run w2 cycles) of one trail from the route (the route then jumps P_end -> N_0 inside
the trail), and RE-INSERT every excised chain, rotated (entered at C_a, left at C_{a-1}, a = 0..6, six internal w2
links), at its own best position of the remaining route (any of the ~5040 run links, i.e. between two visits or inside
another trail's piece).  This is the move behind the charge bound  dG >= E'(skip) - (number of inserted rotations)
(L1 per inserted rotation), the case the local compression lemma cannot exclude.
Works purely on runs (length = 8 + 7 N + sum of link weights, exact).  Insertions are chosen greedily (best first,
distinct links, the new skip link excluded), and for k >= 2 also with one pair of chains placed consecutively at one link
(both rotations, both orders; dL is then a bound only and the move is reported); every greedy candidate with dL <= 0 is rebuilt
and its length recomputed from scratch (all 40320 permutations checked when it improves).
usage: excise_rot_probe.py WORD FAMILY.json KMAX [OUT.json]"""
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
def wmat(st):
    N = len(st); S = np.array(st, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)
    W = np.full((N, N), 8, np.int64)
    from collections import defaultdict
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1).tolist(); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1).tolist()
        d = defaultdict(list)
        for j, key in enumerate(b): d[key].append(j)
        for i, key in enumerate(a):
            for j in d.get(key, ()): W[i, j] = k
    return W
def build(st, W, seq):
    w = list(st[seq[0]])
    for k, r in enumerate(seq):
        if k > 0: kk = int(W[seq[k - 1], r]); w += list(st[r][8 - kk:])
        w += list(st[r][:7])
    return w
def length(W, seq): return 8 + 7 * len(seq) + int(W[np.array(seq[:-1]), np.array(seq[1:])].sum())

def main():
    st0 = starts(load_word(sys.argv[1])); fam = json.load(open(sys.argv[2])); KMAX = int(sys.argv[3])
    # rotation classes of the word's runs: every run of the word is one class; the route is 0..N-1 in word order
    N = len(st0); W = wmat(st0); route = list(range(N)); L0 = length(W, route)
    cls_trail = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            for k in range(len(s) // 8): cls_trail[canon(tuple(int(c) for c in s[8 * k:8 * k + 8]))] = t
    trail = np.array([cls_trail[canon(s)] for s in st0])
    # full chains: maximal runs of consecutive route positions with w2 links, same trail, 7 runs, and a w2 wrap last -> first
    best = (10 ** 9, None); results = []; ncand = 0; best_k = {}
    i = 0; chains = []          # (start index, 7 run ids) in route order
    while i < N:
        j = i
        while j + 1 < N and W[route[j], route[j + 1]] == 2 and trail[route[j + 1]] == trail[route[i]]: j += 1
        blk = route[i:j + 1]
        # split the w2 block into 7-cycles: a full chain is 7 consecutive runs whose last links back to the first by w2
        k = 0
        while k + 7 <= len(blk):
            c = blk[k:k + 7]
            if W[c[6], c[0]] == 2: chains.append((i + k, c)); k += 7
            else: k += 1
        i = j + 1
    pos_of = {r: p for p, r in enumerate(route)}
    # contiguous groups of full chains of one trail (consecutive in the route, linked by the original links)
    for gi in range(len(chains)):
        for k in range(1, KMAX + 1):
            if gi + k > len(chains): break
            grp = chains[gi:gi + k]
            if any(grp[q + 1][0] != grp[q][0] + 7 for q in range(k - 1)): break
            t = trail[grp[0][1][0]]
            if any(trail[g[1][0]] != t for g in grp): break
            s0, s1 = grp[0][0], grp[-1][0] + 7          # excised route positions [s0, s1)
            if s0 == 0 or s1 >= N: continue              # keep the word ends (an excision at an end is a different move)
            prev, nxt = route[s0 - 1], route[s1]
            rem = route[:s0] + route[s1:]
            base = int(W[prev, nxt]) - sum(int(W[route[p], route[p + 1]]) for p in range(s0 - 1, s1)) - 7 * 7 * k
            # removing 7k runs: length changes by -7*7k (7 per run) - removed links + new link prev -> nxt
            R = np.array(rem); lw = W[R[:-1], R[1:]]                  # links of the remaining route
            used = set([rem.index(prev)])                             # the new skip link may not host an insertion
            tot = base; ins = []; ins_cost = []; joint = None
            for (_, c) in grp:
                bestc = None
                for a in range(7):
                    ent, ext = c[a], c[(a - 1) % 7]
                    cost = W[R[:-1], ent] + W[ext, R[1:]] - lw + 7 * 7 + 12   # 7 runs, 6 internal w2 links
                    for q in used: cost[q] = 10 ** 6
                    q = int(cost.argmin()); v = int(cost[q])
                    if bestc is None or v < bestc[0]: bestc = (v, a, q)
                tot += bestc[0]; ins.append((bestc[1], bestc[2], c)); used.add(bestc[2]); ins_cost.append(bestc[0])
            # joint option: two excised chains placed consecutively at ONE link (both rotations, both orders), the rest greedy
            if k >= 2:
                for x1 in range(k):
                    for x2 in range(k):
                        if x1 == x2: continue
                        c1, c2 = grp[x1][1], grp[x2][1]
                        for a1 in range(7):
                            for a2 in range(7):
                                cost = W[R[:-1], c1[a1]] + W[c1[(a1 - 1) % 7], c2[a2]] + W[c2[(a2 - 1) % 7], R[1:]] - lw + 2 * (49 + 12)
                                cost[rem.index(prev)] = 10 ** 6
                                q = int(cost.argmin()); v = int(cost[q])
                                rest = sum(ins_cost[z] for z in range(k) if z not in (x1, x2))
                                if base + v + rest < tot: tot = base + v + rest; joint = (x1, x2, a1, a2, q)
            ncand += 1
            rec = dict(trail=int(t), k=k, route_pos=s0, dL_greedy=tot)
            bk = best_k.get(k); 
            if bk is None or tot < bk: best_k[k] = tot
            if tot < best[0]: best = (tot, rec)
            if tot <= 0 and joint is None:
                # rebuild exactly: insert blocks at their links (process from the right so indices stay valid)
                seq = rem[:]
                for a, q, c in sorted(ins, key=lambda z: -z[1]):
                    blk = [c[(a + j) % 7] for j in range(7)]; seq = seq[:q + 1] + blk + seq[q + 1:]
                Lx = length(W, seq); rec["L_exact"] = Lx
                if Lx <= L0:     # improving or equality move: rebuild the word and check it from scratch
                    w = build(st0, W, seq); perms = {tuple(w[i:i + 8]) for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8}
                    rec["all_perms"] = len(perms) == 40320; rec["len_word"] = len(w)
                    if len(sys.argv) > 4 and rec["all_perms"]:
                        tag = "improving" if Lx < L0 else "equal"
                        open(f"{sys.argv[4]}.{tag}_t{int(t)}_p{s0}.word.txt", "w").write("".join(str(x + 1) for x in w) + "\n")
                results.append(rec)
    out = dict(word=sys.argv[1], L0=L0, full_chains_in_route=len(chains), candidates=ncand, best_dL_by_k={str(k): v for k, v in sorted(best_k.items())}, best_dL_greedy=best[0], best=best[1],
               nonpositive=results[:200], n_nonpositive=len(results), n_improving=sum(1 for r in results if r.get("L_exact", L0) < L0))
    s = json.dumps(out); print(s[:3000])
    if len(sys.argv) > 4: open(sys.argv[4], "w").write(s + "\n")

main()
