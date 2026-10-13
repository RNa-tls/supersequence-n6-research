#!/usr/bin/env python3
"""Round L -- CHECKER B for Lemmas A, B, C (independent of lemmas_check.py).

Different representation: classes as frozen cyclic words given by the 'successor map' (symbol ->
next symbol around the cycle); a run start p of special a is identified with (class, a); the F-step
moves a past its successor; joins are applied as explicit successor-map surgery (no position
arithmetic shared with checker A).
  LEMMA A: for every full chain (class c0, special a, w = predecessor of a in c0) all cost-3
           neighbour classes have the same cycle on the symbols other than a, w.
  LEMMA B: a run of n-2 bac-joined full chains has every cost-3 neighbour class inside it.
  LEMMA C: in pair {a,b}, a phi-set-changing cost-3 join with special in {a,b} is exactly bac with
           b not among the two symbols after a; then the {a,b}-free cycle changes by exchanging those
           two symbols.
Mutation mode (--mutate K) must make some check fail: K=0 keys by the world-a orbit only (claims the
neighbours stay in the same orbit), K=1 replaces bac by skip, K=2 uses a non-adjacent partner symbol.
(Remark: Lemma A also holds with the partner u = symbol after a; both adjacent symbols work.)
usage: lemmas_checkB.py n [--mutate K]"""
import sys, itertools, json

def main():
    n = int(sys.argv[1]); mut = int(sys.argv[sys.argv.index("--mutate") + 1]) if "--mutate" in sys.argv else -1
    syms = list(range(n))
    def succ_of(word):                       # cyclic word (tuple) -> successor dict
        return {word[i]: word[(i + 1) % n] for i in range(n)}
    def word_from(succ, start):
        out = [start]
        while len(out) < n: out.append(succ[out[-1]])
        return tuple(out)
    def key(succ, drop):
        # cycle on the symbols not in drop, canonical
        s0 = min(x for x in syms if x not in drop)
        out = [s0]; x = s0
        while True:
            x = succ[x]
            while x in drop: x = succ[x]
            if x == s0: break
            out.append(x)
        return tuple(out)
    # a run start = (succ, a): the run reads a's successor first ... ending with a
    # p as a tuple = word read starting after a: (succ[a], succ[succ[a]], ..., a)
    def perm(succ, a): return word_from(succ, succ[a])
    def from_perm(p): return succ_of(p), p[-1]
    def F(p):                                # move special past its successor: p0 .. p_{n-2} a -> p1 .. p_{n-2} p0 a
        return p[1:n - 1] + (p[0],) + (p[n - 1],)
    sigmas = [(0, 1, n - 1), (0, n - 1, 1), (1, 0, n - 1), (1, n - 1, 0), (n - 1, 1, 0)]
    def J(x, s):
        if mut == 1 and s == (1, 0, n - 1): s = (0, 1, n - 1)                                         # bac replaced by skip
        return x[2:n - 1] + tuple(x[k] for k in s)
    def cls(p): return key(succ_of(p), ())
    nA = nB = nC = 0
    for p in itertools.permutations(syms):
        a = p[n - 1]; w = p[n - 2] if mut != 2 else p[2]                                             # mutation 2: wrong partner
        C = key(succ_of(p), (a, w) if mut != 0 else (a,))                                            # mutation 0: world orbit only
        x = p
        for _ in range(n - 2): x = F(x)
        for s in sigmas:
            t = J(x, s)
            if key(succ_of(t), (a, w) if mut != 0 else (a,)) != C: print(json.dumps(dict(fail="A", p=p, s=s))); return 1
            nA += 1
        # Lemma C at p (as a join source)
        for b in syms:
            if b == a: continue
            Cx = key(succ_of(p), (a, b))
            for s in sigmas:
                t = J(p, s)
                if t[n - 1] not in (a, b): continue
                leaves = key(succ_of(t), (a, b)) != Cx
                bac = (s == (1, 0, n - 1))
                if leaves != (bac and b not in (p[0], p[1])): print(json.dumps(dict(fail="C", p=p, b=b, s=s))); return 1
                if leaves:
                    sc = dict(zip(Cx, Cx[1:] + Cx[:1]))
                    # exchange p0, p1 (adjacent in Cx: p0 followed by p1)
                    if sc[p[0]] != p[1]: print(json.dumps(dict(fail="C-adj"))); return 1
                    pred = {v: k for k, v in sc.items()}
                    u = pred[p[0]]; v = sc[p[1]]
                    sc[u] = p[1]; sc[p[1]] = p[0]; sc[p[0]] = v
                    s0 = min(Cx); out = [s0]
                    while len(out) < len(Cx): out.append(sc[out[-1]])
                    if key(succ_of(t), (a, b)) != tuple(out): print(json.dumps(dict(fail="C-step"))); return 1
                nC += 1
    # predecessor half of Lemma A and Lemma B via the successor relation (all perms are join targets)
    inv = {}
    for y in itertools.permutations(syms):
        for s in sigmas: inv.setdefault((J(y, s), s), y)
    for p in itertools.permutations(syms):
        a = p[n - 1]; w = p[n - 2]; C = key(succ_of(p), (a, w))
        for s in sigmas:
            y = inv.get((p, s))
            if y is None: continue
            if key(succ_of(y), (a, w)) != C: print(json.dumps(dict(fail="A-pred", p=p, s=s))); return 1
            nA += 1
        # Lemma B: run of n-2 bac-joined full chains from p
        q = p; covered = set(); first = p
        for r in range(n - 2):
            x = q
            for i in range(n - 1):
                covered.add(cls(x))
                if i < n - 2: x = F(x)
            q = J(x, (1, 0, n - 1))
        last = x
        for s in sigmas:
            if cls(J(last, s)) not in covered: print(json.dumps(dict(fail="B-succ", p=p, s=s))); return 1
            y = inv.get((first, s))
            if y is not None and cls(y) not in covered: print(json.dumps(dict(fail="B-pred", p=p, s=s))); return 1
        nB += 1
    print(json.dumps(dict(checker="B", n=n, lemmaA=nA, lemmaB=nB, lemmaC=nC, ok=True, mutation=mut)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
