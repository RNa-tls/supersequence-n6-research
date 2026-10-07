#!/usr/bin/env python3
"""Independent verifier B: works on word positions only (no route reconstruction, no cost function).
Gap g_k = (position of k-th new permutation window) - (position of previous one).  A class is
identified by rotating its cyclic word so that symbol 0 comes first.  Runs, chains and trails are
recognized from the gap sequence (1 = same class, 2 = chain step, 3 = trail step, >=4 = break)
and the chain step is re-checked as the explicit position map F = (1 2 ... n-1) on the start windows."""
import sys, json, math
from collections import Counter
w = "".join(ch for ch in open(sys.argv[1]).read() if not ch.isspace())
al = sorted(set(w)); n = len(al); w = [al.index(c) for c in w]
N = math.factorial(n); HEX = N // n; ORB = HEX // (n - 1)
pos = []; got = set()
for i in range(len(w) - n + 1):
    t = tuple(w[i:i + n])
    if len(set(t)) == n and t not in got: got.add(t); pos.append(i)
assert len(got) == N
gaps = [b - a for a, b in zip(pos, pos[1:])]
assert pos[0] == 0 and pos[-1] == len(w) - n          # tight at both ends
def canon(t):
    k = t.index(0); return t[k:] + t[:k]
# group into classes by consecutive gap-1 runs
groups = [[0]]
for k, g in enumerate(gaps):
    if g == 1: groups[-1].append(k + 1)
    else: groups.append([k + 1])
assert all(len(G) == n for G in groups) and len(groups) == HEX
assert len({canon(tuple(w[pos[G[0]]:pos[G[0]] + n])) for G in groups}) == HEX
J = [gaps[G[-1]] for G in groups[:-1]]
Fpos = list(range(1, n - 1)) + [0, n - 1]                # F(s)[i] = s[Fpos[i]]
for k, g in enumerate(J):
    if g == 2:
        s = w[pos[groups[k][0]]:pos[groups[k][0]] + n]; t = w[pos[groups[k + 1][0]]:pos[groups[k + 1][0]] + n]
        assert [s[Fpos[i]] for i in range(n)] == t
# trails as maximal gap<=3 segments of the class sequence; chain count per trail = 1 + #(gap 3)
trails = []; cur = dict(classes=1, chains=1)
for g in J:
    if g == 2: cur["classes"] += 1
    elif g == 3: cur["classes"] += 1; cur["chains"] += 1
    else: trails.append(cur); cur = dict(classes=1, chains=1)
trails.append(cur)
# trail score = sum over chains (l - (n-2)) = classes - (n-2) * chains
v = [t["classes"] - (n - 2) * t["chains"] for t in trails]
q = sum(t["chains"] for t in trails); eta = sum(g >= 4 for g in J); E5 = sum(max(0, g - 4) for g in J)
CONST = N + HEX + ORB + n - 3; f = CONST + math.factorial(n - 3) - 1
W = sum(x - (n - 2) for x in v) - (n - 2) * E5
print(json.dumps(dict(n=n, length=len(w), q=q, eta=eta, E5=E5, D=q - ORB + eta, trails=len(trails),
                      score_sum=sum(v), trail_scores=v, rows=[t["chains"] for t in trails], W=W,
                      L_check=(CONST - ORB + q + eta + E5 == len(w) == f - W // (n - 2)))))
