#!/usr/bin/env python3
"""Variant local search for the 6A + 24 phi packing (n = 8).  Each bundle has 4 realizations:
detour X = (5,cba)(6,bac)(7,cba)(4,bac) or X' = (5,bca)(6,bac)(6,bca)(5,bac) [same class set], each in
orientation special-0 or (0 7)-relabelled; each free phi-cycle has 2 orientations.  All variants of a
cycle cover exactly the same classes (checked).  Evaluation: LKH (elkai) on the chain-level ATSP."""
import sys, os, json, math, itertools, random, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
from chain_atsp import word_from_order
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def cyc_canon(seq):
    k_ = seq.index(min(seq)); return tuple(seq[k_:] + seq[:k_])
def canon(p):
    k_ = p.index(0); return p[k_:] + p[:k_]
CTX = {}
def closed_trail(n, letters_period):
    I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
    Fp = [I]
    for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
    T = lambda s: tuple(list(range(2, n - 1)) + list(s))
    Pi = I
    for l, s in letters_period: Pi = comp(Pi, comp(Fp[l - 1], T(s)))
    m = 1; X = Pi
    while X != I: X = comp(X, Pi); m += 1
    P = I; out = []
    for _ in range(m):
        for l, s in letters_period:
            out.append((P, l)); P = comp(P, comp(Fp[l - 1], T(s)))
    return out
def classes_of(chs, F):
    cl = set()
    for s, l in chs:
        x = s
        for _ in range(l): cl.add(canon(x)); x = comp(x, F)
    return frozenset(cl)
def setup(src, orbfile, k):
    w, n = load(src); out, info = analyse(w, n)
    S, trails = info["S"], info["trails"]
    F = tuple(list(range(1, n - 1)) + [0, n - 1]); phi = tuple(list(range(1, n - 2)) + [0, n - 2, n - 1])
    BAC, CBA, BCA = (1, 0, n - 1), (n - 1, 1, 0), (1, n - 1, 0)
    def Cof(p):
        k_ = p.index(0); w_ = list(p[k_:] + p[:k_]); return cyc_canon([x for x in w_ if x not in (0, n - 1)])
    tmpl = [t for t in trails if len(t) == 104][0]
    tch = [(S[ch[0]], len(ch)) for ch in tmpl]
    Ctm = classes_of(tch, F)
    S_ = lambda r: [(n - 3, BAC)] + [(n - 1, BAC)] * r
    Xp = [(5, BCA), (6, BAC), (6, BCA), (5, BAC)] + [(n - 1, BAC)] * 4
    alt = closed_trail(n, S_(3) + S_(4) + Xp + S_(3) + S_(4))
    Calt = classes_of(alt, F)
    h = None
    for g in itertools.permutations(range(n)):
        if frozenset(canon(tuple(g[x] for x in c)) for c in Calt) == Ctm: h = g; break
    assert h is not None, "X' realization does not match the template class set"
    altch = [(tuple(h[x] for x in s), l) for s, l in alt]
    assert classes_of(altch, F) == Ctm
    rep = json.load(open(orbfile))["reps"][k]
    cycles = []; covered = set()
    for g in rep:
        v0 = [(tuple(g[x] for x in s), l) for s, l in tch]
        v1 = [(tuple(g[x] for x in s), l) for s, l in altch]
        assert classes_of(v0, F) == classes_of(v1, F)
        for s, l in v0:
            x = s
            for _ in range(l): covered.add(Cof(x)); x = comp(x, F)
        cycles.append([v0, v1])
    others = list(range(1, n - 1))
    for C in sorted({cyc_canon(list(p)) for p in itertools.permutations(others)}):
        if C in covered: continue
        s = tuple(C) + (n - 1, 0); cy = []
        for _ in range(n - 2): cy.append((s, n - 1)); s = comp(s, phi)
        cycles.append([cy])
    return n, F, cycles
def chains_for(n, F, cycles, state):
    Rinv = lambda s: s[-1:] + s[:-1]; sw = {0: n - 1, n - 1: 0}
    chs = []
    for cy, (real, ori) in zip(cycles, state):
        for s, l in cy[real]:
            if ori: s = tuple(sw.get(x, x) for x in s)
            last = s
            for _ in range(l - 1): last = comp(last, F)
            chs.append((s, Rinv(last), l))
    return chs
def evaluate(args):
    state, runs, seed = args
    import elkai
    n, F, cycles = CTX["n"], CTX["F"], CTX["cycles"]
    chs = chains_for(n, F, cycles, state); q = len(chs)
    M = [[0] * (q + 1) for _ in range(q + 1)]
    for a in range(q):
        e = chs[a][1]
        for b in range(q):
            if a != b: M[a][b] = cost(e, chs[b][0], n) - 2
    tour = elkai.DistanceMatrix(M).solve_tsp(runs=runs)
    if tour[-1] == tour[0]: tour = tour[:-1]
    i = tour.index(q); order = tour[i + 1:] + tour[:i]
    HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    return CONST - ORB + q + sum(M[a][b] for a, b in zip(order, order[1:])) - (q - 1), state, order
def init(src, orbfile, k):
    n, F, cycles = setup(src, orbfile, k); CTX.update(n=n, F=F, cycles=cycles)
if __name__ == "__main__":
    src, orbfile, k, minutes, workers, runs = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
    init(src, orbfile, k); cycles = CTX["cycles"]; nc = len(cycles); rng = random.Random(1000 + k)
    start = tuple((0, 0) for _ in range(nc))
    with Pool(workers, initializer=init, initargs=(src, orbfile, k)) as pool:
        best = pool.map(evaluate, [(start, runs, 0)])[0]
        print(json.dumps(dict(start=best[0])), flush=True)
        # also try: all bundles in X' realization
        allx = tuple((1 if len(cycles[i]) > 1 else 0, 0) for i in range(nc))
        r = pool.map(evaluate, [(allx, runs, 1)])[0]
        print(json.dumps(dict(all_Xprime=r[0])), flush=True)
        if r[0] < best[0]: best = r
        t0 = time.time(); it = 0
        while time.time() - t0 < minutes * 60:
            props = []
            for j in range(workers):
                st = list(best[1])
                for _ in range(rng.choice([1, 1, 2, 3])):
                    i = rng.randrange(nc); real, ori = st[i]
                    if len(cycles[i]) > 1 and rng.random() < 0.5: real ^= 1
                    else: ori ^= 1
                    st[i] = (real, ori)
                props.append((tuple(st), runs, rng.randrange(10**6)))
            res = pool.map(evaluate, props); it += 1
            for r in sorted(res, key=lambda r: r[0]):
                if r[0] < best[0] or (r[0] == best[0] and rng.random() < 0.3):
                    if r[0] < best[0]: print(json.dumps(dict(it=it, improved=r[0], sec=round(time.time() - t0))), flush=True)
                    best = r; break
    n, F = CTX["n"], CTX["F"]
    chs = chains_for(n, F, cycles, best[1]); word = word_from_order(chs, best[2], n)
    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"variant_orbit{k}_{len(word)}.txt")
    open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
    print(json.dumps(dict(final=best[0], word_length=len(word), state=best[1], file=outp)), flush=True)
