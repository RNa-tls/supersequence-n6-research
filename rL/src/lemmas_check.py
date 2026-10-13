#!/usr/bin/env python3
"""Round L -- exhaustive machine check of the structural lemmas (independent code: no import from
rI/rK/trailcore; only the definitions below).

Definitions (n symbols, n-1 = position of the special):
  run start p; special a = p[n-1]; F-step p -> p[1..n-2] p[0] p[n-1]; full chain = p, pF, .., pF^(n-2);
  cost-3 join from run start x: t = x[2..n-2] + (x[s0], x[s1], x[s2]) for the 5 legal sigma
  (sigma = (n-1,0,1) gives a rotation of x: same class, excluded);
  class(p) = cyclic word of p; phi-set key of class c for pair {a,b}: cyclic word of c minus {a,b}.
  moving symbol of a full chain starting at p: w = p[n-2] (the symbol preceding a in its first class).

LEMMA A (anchoring).  For every full chain (start p, world a, moving symbol w), every cost-3
  successor t of its last run start and every cost-3 predecessor y of its first run start
  (y o T_sigma = p) has its class in the phi-set P({a,w}, C_p).  Moreover special(t) in {a, w}
  for every sigma except sigma = (0,n-1,1) (new special x1), and special(y) in {a, w} for every
  sigma except sigma = cba (predecessor special p[n-3]); in the {a,w} cases the neighbouring chain is
  a world-a or world-w orbit segment lying entirely inside P({a,w}, C_p).
LEMMA B (isolation).  A BAC-run of n-2 full chains covers its whole phi-set; consequently it has no
  cost-3 predecessor or successor at all: it is an entire trail.  (Checked directly.)
LEMMA C (two-world locality / phi-quotient).  For run start x (special a), every b != a and every
  sigma: if special(t) in {a, b} then [class(t) leaves P({a,b}, C_x)] <=> [sigma = bac and
  b not in {x0, x1}], and in that case C_t = C_x with the adjacent symbols x0, x1 exchanged, i.e. the
  (n-2)-level F-step of world x0.  A special change to b happens only if b in {x0, x1}.
usage: lemmas_check.py n"""
import sys, itertools, json, time

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    t0 = time.time()
    SIG = [s for s in itertools.permutations((0, 1, n - 1)) if s != (n - 1, 0, 1)]
    BAC = (1, 0, n - 1)
    def F(p): return p[1:n - 1] + p[:1] + p[n - 1:]
    def join(x, s): return x[2:n - 1] + tuple(x[k] for k in s)
    def cyc(seq):
        seq = list(seq); k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
    def cls(p): return cyc(p)
    def phikey(c, a, b): return cyc([x for x in c if x not in (a, b)])
    # inverse joins: y such that join(y, s) = p
    inv = {}
    for s in SIG:
        # join(y,s)[i] = y[2+i] for i < n-3; then y[s0], y[s1], y[s2]
        def pre(p, s=s):
            y = [None] * n
            for i in range(n - 3): y[2 + i] = p[i]
            for k, pos in enumerate(s): y[pos] = p[n - 3 + k]
            return tuple(y)
        inv[s] = pre
    nA = nB = nC = 0
    for p in itertools.permutations(range(n)):
        a = p[n - 1]; w = p[n - 2]
        C = phikey(cls(p), a, w)
        x = p
        for _ in range(n - 2): x = F(x)
        # LEMMA A, successors and predecessors
        for s in SIG:
            t = join(x, s)
            assert phikey(cls(t), a, w) == C, ("A-succ", p, s)
            assert (t[n - 1] in (a, w)) == (s != (0, n - 1, 1)), ("A-succ-world", p, s)
            y = inv[s](p); assert join(y, s) == p
            assert phikey(cls(y), a, w) == C, ("A-pred", p, s)
            assert (y[n - 1] in (a, w)) == (s != (n - 1, 1, 0)), ("A-pred-world", p, s)
            nA += 2
        # LEMMA C for run start p as a join source
        for b in range(n):
            if b == a: continue
            Cx = phikey(cls(p), a, b)
            for s in SIG:
                t = join(p, s)
                if t[n - 1] not in (a, b): continue
                leaves = phikey(cls(t), a, b) != Cx
                assert leaves == (s == BAC and b not in (p[0], p[1])), ("C", p, b, s)
                if leaves:
                    # Cx with p0 moved forward past p1
                    L = list(Cx); i = L.index(p[0]); j = (i + 1) % len(L)
                    assert L[j] == p[1], ("C-adjacent", p, b)
                    L[i], L[j] = L[j], L[i]
                    assert phikey(cls(t), a, b) == cyc(L), ("C-step", p, b)
                if t[n - 1] == b: assert b in (p[0], p[1]), ("C-special", p, b, s)
                nC += 1
    # LEMMA B: complete BAC runs
    for p in itertools.permutations(range(n)):
        run = []; q = p; classes = set()
        for r in range(n - 2):
            x = q
            for i in range(n - 1):
                classes.add(cls(x))
                if i < n - 2: x = F(x)
            run.append((q, x)); q = join(x, BAC)
        if len(classes) != (n - 2) * (n - 1): continue          # not a valid run (cannot happen)
        first, last = run[0][0], run[-1][1]
        for s in SIG:
            assert cls(join(last, s)) in classes, ("B-succ", p, s)
            assert cls(inv[s](first)) in classes, ("B-pred", p, s)
        nB += 1
    print(json.dumps(dict(n=n, lemmaA_checks=nA, lemmaB_runs=nB, lemmaC_checks=nC, ok=True,
                          sec=round(time.time() - t0, 1))))

if __name__ == "__main__":
    main()
