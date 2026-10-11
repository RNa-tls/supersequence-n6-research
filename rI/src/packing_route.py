#!/usr/bin/env python3
"""Route a {0,7}-bundle packing: bundles = 46188 long trail 0 relabelled by g; free arrangements C ->
phi-cycle started at (C, 7, 0) [special 0] (or (C, 0, 7) [special 7] if FREE7=1).  Chain-level ATSP
solved by LKH (elkai); the best order is written as a word and must pass verifier B."""
import sys, os, json, math, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
from chain_atsp import word_from_order
import elkai
src, orbfile, k, runs, seeds = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
w, n = load(src); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
F = tuple(list(range(1, n - 1)) + [0, n - 1]); phi = tuple(list(range(1, n - 2)) + [0, n - 2, n - 1])
Rinv = lambda s: s[-1:] + s[:-1]
def cyc_canon(seq):
    k_ = seq.index(min(seq)); return tuple(seq[k_:] + seq[:k_])
def Cof(p):
    k_ = p.index(0); w_ = list(p[k_:] + p[:k_]); return cyc_canon([x for x in w_ if x not in (0, n - 1)])
tmpl = [t for t in trails if len(t) == 104][0]
tch = [(S[ch[0]], len(ch)) for ch in tmpl]
rep = json.load(open(orbfile))["reps"][k]
chains = []; covered = set()
for g in rep:
    for s, l in tch:
        s2 = tuple(g[x] for x in s); chains.append(s2)
        x = s2
        for _ in range(l): covered.add(Cof(x)); x = comp(x, F)
chs = []
for g in rep:
    for s, l in tch:
        s2 = tuple(g[x] for x in s); last = s2
        for _ in range(l - 1): last = comp(last, F)
        chs.append((s2, Rinv(last), l))
others = list(range(1, n - 1))
allC = sorted({cyc_canon(list(p)) for p in itertools.permutations(others)})
free = [C for C in allC if C not in covered]
free7 = os.environ.get("FREE7") == "1"
for C in free:
    s = tuple(C) + ((0, n - 1) if free7 else (n - 1, 0))
    for _ in range(n - 2):
        last = s
        for _ in range(n - 2): last = comp(last, F)
        chs.append((s, Rinv(last), n - 1)); s = comp(s, phi)
q = len(chs)
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
N = q + 1; D = q
M = [[0] * N for _ in range(N)]
for a in range(q):
    e = chs[a][1]
    for b in range(q):
        if a != b: M[a][b] = cost(e, chs[b][0], n) - 2
base = CONST - ORB + q; best = None
for sd in range(seeds):
    tour = elkai.DistanceMatrix(M).solve_tsp(runs=runs)
    if tour[-1] == tour[0]: tour = tour[:-1]
    i = tour.index(D); order = tour[i + 1:] + tour[:i]
    L = base + sum(M[a][b] for a, b in zip(order, order[1:])) - (q - 1)
    print(json.dumps(dict(orbit=k, free7=free7, seed=sd, q=q, free=len(free), predicted_length=L)), flush=True)
    if best is None or L < best[0]: best = (L, order)
word = word_from_order(chs, best[1], n)
outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"packing_route_orbit{k}{'_f7' if free7 else ''}_{len(word)}.txt")
open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
print("wrote", outp, "length", len(word))
