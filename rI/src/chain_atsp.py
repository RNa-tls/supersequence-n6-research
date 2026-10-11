#!/usr/bin/env python3
"""Chain-level ATSP for a fixed r = 0 chain set (sec. 31B/32 record attempt).
Nodes: the q chains of a given r = 0 word (start t_c, run end e_c), plus a depot (path ends).
Any Hamiltonian path through all chains is an r = 0 route on the same chain set; its length is
   L = n + (n-1)*HEX + 2*(HEX - q) + sum_{links} c        (q - 1 links, c = cost(e_a, t_b) >= 2)
     = CONST - ORB + q + sum_links (c - 3).
(A link of cost 2 merges two chains; the identity stays exact because it is just the join sum.)
Solved heuristically with LKH-3 (elkai) on the full (q+1) x (q+1) matrix with weights c - 2 >= 0;
every tour found is turned into a word and must pass the independent verifiers A and B."""
import sys, os, json, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost

def chains_of(info, n):
    S = info["S"]; Rinv = lambda s: s[-1:] + s[:-1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    out = []
    for ch in info["chains"]:
        out.append((S[ch[0]], Rinv(S[ch[-1]]), len(ch)))
    return out

def word_from_order(chs, order, n):
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1]); R = lambda s: s[1:] + s[:1]
    perms = []
    for a in order:
        s, _, l = chs[a]
        for _ in range(l):
            p = s
            for _ in range(n): perms.append(p); p = R(p)
            s = F(s)
    word = list(perms[0])
    for x, y in zip(perms, perms[1:]):
        c = cost(x, y, n); word.extend(y[n - c:])
    return word

if __name__ == "__main__":
    import elkai
    path, runs, seeds = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    w, n = load(path); out, info = analyse(w, n)
    chs = chains_of(info, n); q = len(chs)
    HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    N = q + 1; D = q
    M = [[0] * N for _ in range(N)]
    for a in range(q):
        e = chs[a][1]
        for b in range(q):
            M[a][b] = 0 if a == b else cost(e, chs[b][0], n) - 2
    # depot row/col = 0
    base = CONST - ORB + q
    best = None
    for sd in range(seeds):
        t0 = time.time()
        tour = elkai.DistanceMatrix(M).solve_tsp(runs=runs)
        # rotate so the depot is first; path = rest
        if tour[-1] == tour[0]: tour = tour[:-1]
        k = tour.index(D); order = tour[k + 1:] + tour[:k]
        tot = sum(M[a][b] for a, b in zip(order, order[1:]))      # sum (c - 2)
        L = base + tot - (q - 1)                                  # sum (c-3) = sum (c-2) - (q-1)
        print(json.dumps(dict(seed=sd, predicted_length=L, sec=round(time.time() - t0, 1))), flush=True)
        if best is None or L < best[0]: best = (L, order)
    L, order = best
    word = word_from_order(chs, order, n)
    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"chain_atsp_n{n}_{len(word)}.txt")
    open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
    print("wrote", outp, "length", len(word), "predicted", L)
