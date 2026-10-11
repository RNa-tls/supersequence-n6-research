#!/usr/bin/env python3
"""Pure phi-cycle r = 0 routes in the {0, n-1}-system: (n-3)! phi-cycles P({0,n-1},C), each traversed
with special 0 or n-1 (2 orientations).  For every orientation vector (exhaustive if 2^(n-3)! small,
else random sample) solve the chain-level ATSP with LKH; L = f(n) + linking loss."""
import sys, os, json, math, itertools, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import cost
from chain_atsp import word_from_order
import elkai
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
n, samples, runs = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
F = tuple(list(range(1, n - 1)) + [0, n - 1]); phi = tuple(list(range(1, n - 2)) + [0, n - 2, n - 1])
Rinv = lambda s: s[-1:] + s[:-1]
Cs = sorted({cyc_canon(list(p)) for p in itertools.permutations(range(1, n - 1))})
def chains(bits):
    out = []
    for C, b in zip(Cs, bits):
        s = tuple(C) + ((0, n - 1) if b else (n - 1, 0))
        for _ in range(n - 2):
            last = s
            for _ in range(n - 2): last = comp(last, F)
            out.append((s, Rinv(last), n - 1)); s = comp(s, phi)
    return out
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
f = CONST + math.factorial(n - 3) - 1
nc = len(Cs)
space = list(itertools.product((0, 1), repeat=nc)) if 2 ** nc <= samples else [tuple(random.Random(i).randint(0, 1) for _ in range(nc)) for i in range(samples)]
best = None; hist = {}
for bits in space:
    chs = chains(bits); q = len(chs)
    M = [[0] * (q + 1) for _ in range(q + 1)]
    for a in range(q):
        for b in range(q):
            if a != b: M[a][b] = cost(chs[a][1], chs[b][0], n) - 2
    tour = elkai.DistanceMatrix(M).solve_tsp(runs=runs)
    if tour[-1] == tour[0]: tour = tour[:-1]
    i = tour.index(q); order = tour[i + 1:] + tour[:i]
    L = CONST - ORB + q + sum(M[a][b] for a, b in zip(order, order[1:])) - (q - 1)
    hist[L] = hist.get(L, 0) + 1
    if best is None or L < best[0]: best = (L, bits, order, chs)
print(json.dumps(dict(n=n, f=f, evaluated=len(space), best=best[0], hist=dict(sorted(hist.items())))))
word = word_from_order(best[3], best[2], n)
outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"phi_only_n{n}_{len(word)}.txt")
open(outp, "w").write("".join(str(c + 1) for c in word) + "\n"); print("wrote", outp)
