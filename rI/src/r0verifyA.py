#!/usr/bin/env python3
"""Independent verifier A (route-based, no shared code with r178/rH) for r = 0 superpermutations.
Model (first principles, see ROUND_I_REPORT.md sec. 1):
  route  = permutations in order of first occurrence; cost(x,y) = n - max overlap.
  r = 0  <=> every cyclic class is traversed as ONE run of n permutations joined by cost-1 edges.
  run start s of a class; between consecutive classes the join cost is c = cost(R^-1 s, s').
  chain  = maximal sequence of classes joined by cost-2 joins (then s' = F(s), F = rotate first n-1).
  trail  = maximal sequence of chains joined by cost-3 joins.
  chain length l (number of classes), chain score l-(n-2); trail score v = sum over its chains.
Length identity checked:  L = CONST - ORB + q + eta + E5,  q = #chains, eta = #joins of cost >= 4,
E5 = sum (c-4)^+;  equivalently  L = f(n) - W/(n-2),  W = sum_trails (v_i - (n-2)) - (n-2)*E5."""
import sys, json, math
from collections import Counter

def load(path):
    w = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(w)); mp = {c: i for i, c in enumerate(al)}
    return [mp[c] for c in w], len(al)

def cost(x, y, n):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n

def analyse(w, n):
    N = math.factorial(n); HEX = math.factorial(n - 1); ORB = math.factorial(n - 2)
    CONST = N + HEX + ORB + n - 3; f = CONST + math.factorial(n - 3) - 1
    seen = {}; route = []
    for i in range(len(w) - n + 1):
        t = tuple(w[i:i + n])
        if len(set(t)) == n and t not in seen: seen[t] = i; route.append(t)
    assert len(route) == N, "not all permutations"
    c = [cost(route[i], route[i + 1], n) for i in range(N - 1)]
    assert len(w) == n + sum(c), "word is not the tight overlap of its route"
    R = lambda s: s[1:] + s[:1]
    # runs
    starts = [0] + [i + 1 for i in range(N - 1) if c[i] != 1]
    runs = [(starts[j], (starts[j + 1] if j + 1 < len(starts) else N)) for j in range(len(starts))]
    cls = lambda p: min(tuple(p[i:] + p[:i]) for i in range(n))
    r0 = all(b - a == n for a, b in runs) and len({cls(route[a]) for a, _ in runs}) == HEX
    assert r0, "not an r = 0 route"
    S = [route[a] for a, _ in runs]
    J = [c[b - 1] for a, b in runs[:-1]]          # join costs between consecutive classes
    assert all(x >= 2 for x in J)
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    for i, x in enumerate(J):
        if x == 2: assert S[i + 1] == F(S[i])
    # chains and trails
    chains = [[0]]
    for i, x in enumerate(J):
        if x == 2: chains[-1].append(i + 1)
        else: chains.append([i + 1])
    cj = [J[ch[-1]] for ch in chains[:-1]]        # join after each chain (cost >= 3)
    trails = [[chains[0]]]
    for k, x in enumerate(cj):
        if x == 3: trails[-1].append(chains[k + 1])
        else: trails.append([chains[k + 1]])
    q = len(chains); eta = sum(x >= 4 for x in J); E5 = sum(max(0, x - 4) for x in J)
    v = [sum(len(ch) - (n - 2) for ch in t) for t in trails]
    W = sum(x - (n - 2) for x in v) - (n - 2) * E5
    L1 = CONST - ORB + q + eta + E5
    assert (f * (n - 2) - W) % (n - 2) == 0
    L2 = f - W // (n - 2)
    blocks_full = sum(len(ch) == n - 1 for ch in chains)
    # exact partition: each class in exactly one chain (automatic since one run per class)
    part = Counter(cls(S[i]) for ch in chains for i in ch)
    return dict(n=n, length=len(w), f=f, CONST=CONST, all_perms=True, r0=True, classes=len(part),
                exact_partition=all(x == 1 for x in part.values()) and len(part) == HEX,
                q=q, eta=eta, E5=E5, trails=len(trails), join_hist=dict(sorted(Counter(J).items())),
                chain_len_hist=dict(sorted(Counter(len(ch) for ch in chains).items())),
                full_chains=blocks_full, D=q - ORB + eta, m_equiv=q - ORB,
                trail_scores=v, score_sum=sum(v), trail_rows=[len(t) for t in trails],
                W=W, L_formula1=L1, L_formula2=L2, ok=L1 == len(w) == L2), dict(route=route, S=S, J=J, chains=chains, trails=trails)

if __name__ == "__main__":
    w, n = load(sys.argv[1])
    out, _ = analyse(w, n)
    print(json.dumps(out))
