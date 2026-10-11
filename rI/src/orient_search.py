#!/usr/bin/env python3
"""Orientation local search for a {0,7}-bundle packing (n = 8).  Every cycle (bundle or free
phi-cycle) can be traversed with its own special = 0 or with the (0 7)-relabelled version (special
7); both cover the same classes.  State = orientation bit per cycle.  Evaluation = LKH (elkai) on the
chain-level ATSP (few runs).  Accept improvements (and equal moves with prob 0.3); parallel workers.
Writes the best word found; every word must pass the verifiers."""
import sys, os, json, math, itertools, random, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
from chain_atsp import word_from_order
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def cyc_canon(seq):
    k_ = seq.index(min(seq)); return tuple(seq[k_:] + seq[:k_])
CTX = {}
def setup(src, orbfile, k):
    w, n = load(src); out, info = analyse(w, n)
    S, trails = info["S"], info["trails"]
    F = tuple(list(range(1, n - 1)) + [0, n - 1]); phi = tuple(list(range(1, n - 2)) + [0, n - 2, n - 1])
    def Cof(p):
        k_ = p.index(0); w_ = list(p[k_:] + p[:k_]); return cyc_canon([x for x in w_ if x not in (0, n - 1)])
    tmpl = [t for t in trails if len(t) == 104][0]
    tch = [(S[ch[0]], len(ch)) for ch in tmpl]
    rep = json.load(open(orbfile))["reps"][k]
    cycles = []; covered = set()
    for g in rep:
        cy = []
        for s, l in tch:
            s2 = tuple(g[x] for x in s); cy.append((s2, l)); x = s2
            for _ in range(l): covered.add(Cof(x)); x = comp(x, F)
        cycles.append(cy)
    others = list(range(1, n - 1))
    for C in sorted({cyc_canon(list(p)) for p in itertools.permutations(others)}):
        if C in covered: continue
        s = tuple(C) + (n - 1, 0); cy = []
        for _ in range(n - 2): cy.append((s, n - 1)); s = comp(s, phi)
        cycles.append(cy)
    return n, F, cycles
def chains_for(n, F, cycles, bits):
    Rinv = lambda s: s[-1:] + s[:-1]
    sw = {0: n - 1, n - 1: 0}
    chs = []
    for cy, b in zip(cycles, bits):
        for s, l in cy:
            if b: s = tuple(sw.get(x, x) for x in s)
            last = s
            for _ in range(l - 1): last = comp(last, F)
            chs.append((s, Rinv(last), l))
    return chs
def evaluate(args):
    bits, runs, seed = args
    import elkai
    n, F, cycles = CTX["n"], CTX["F"], CTX["cycles"]
    chs = chains_for(n, F, cycles, bits); q = len(chs)
    M = [[0] * (q + 1) for _ in range(q + 1)]
    for a in range(q):
        e = chs[a][1]
        for b in range(q):
            if a != b: M[a][b] = cost(e, chs[b][0], n) - 2
    random.seed(seed)
    tour = elkai.DistanceMatrix(M).solve_tsp(runs=runs)
    if tour[-1] == tour[0]: tour = tour[:-1]
    i = tour.index(q); order = tour[i + 1:] + tour[:i]
    HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    L = CONST - ORB + q + sum(M[a][b] for a, b in zip(order, order[1:])) - (q - 1)
    return L, bits, order
def init(src, orbfile, k):
    n, F, cycles = setup(src, orbfile, k); CTX.update(n=n, F=F, cycles=cycles)
if __name__ == "__main__":
    src, orbfile, k, minutes, workers, runs = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
    init(src, orbfile, k)
    nc = len(CTX["cycles"]); rng = random.Random(k)
    cur = tuple([0] * nc)
    with Pool(workers, initializer=init, initargs=(src, orbfile, k)) as pool:
        best = pool.map(evaluate, [(cur, runs, 0)])[0]
        print(json.dumps(dict(start=best[0])), flush=True)
        t0 = time.time(); it = 0
        while time.time() - t0 < minutes * 60:
            props = []
            for j in range(workers):
                b = list(best[1])
                for _ in range(rng.choice([1, 1, 2, 3])):
                    i = rng.randrange(nc); b[i] ^= 1
                props.append((tuple(b), runs, rng.randrange(10**6)))
            res = pool.map(evaluate, props)
            it += 1
            for r in sorted(res, key=lambda r: r[0]):
                if r[0] < best[0] or (r[0] == best[0] and rng.random() < 0.3):
                    if r[0] < best[0]: print(json.dumps(dict(it=it, improved=r[0], flips=sum(r[1]), sec=round(time.time() - t0))), flush=True)
                    best = r
                    break
    n, F, cycles = CTX["n"], CTX["F"], CTX["cycles"]
    chs = chains_for(n, F, cycles, best[1])
    word = word_from_order(chs, best[2], n)
    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"orient_orbit{k}_{len(word)}.txt")
    open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
    print(json.dumps(dict(final=best[0], word_length=len(word), bits=best[1], file=outp)), flush=True)
