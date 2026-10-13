#!/usr/bin/env python3
"""Round L -- break attempt: SELF-REPAIRING (hole-free) closed trails of ANY world structure.

Round K searched only for single-pair bundles (class count = 0 mod 42, union of phi-sets of one
pair).  Here a closed syllable trail W^m is kept if it is valid (distinct classes), has positive
saving, and is hole-free: every world-orbit containing one of its non-full chains is entirely
inside the trail (so the trail needs no repair from outside).  Reported for every hit: worlds used,
classes, chains, saving, rate (k+1)/|T|, whether it is a one-pair phi-union.
Word families:  'all L'  = every cyclic word of length L over the 12 syllables S0..S5, X0..X5;
                'esc L K' = S4^L with at most K positions replaced by another syllable.
usage: holefree_search.py all L | esc L K"""
import sys, os, json, time, itertools
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rK", "src"))
from long_trail_search import SYL, pi_of, order, canon, comp, Fp, T, I, n

def closed_chains(letters, m):
    P = I; seen = set(); out = []
    for l, s in letters * m:
        a = P[n - 1]; cl = []
        for j in range(l):
            c = canon(comp(P, Fp[j]))
            if c in seen: return None
            seen.add(c); cl.append(c)
        D = [x for x in P if x != a]; k = D.index(min(D)); D = tuple(D[k:] + D[:k])
        out.append((a, D, l, cl))
        P = comp(P, comp(Fp[l - 1], T(s)))
    return out, seen

def orbit_classes(a, D):
    out = []
    for g in range(len(D)):
        s = list(D[:g + 1]) + [a] + list(D[g + 1:]); out.append(canon(tuple(s)))
    return out

def one_pair_union(seen):
    for x, y in itertools.combinations(range(n), 2):
        groups = {}
        for c in seen:
            C = tuple(z for z in c if z not in (x, y)); k = C.index(min(C)); C = C[k:] + C[:k]
            groups[C] = groups.get(C, 0) + 1
        if all(v == (n - 2) * (n - 1) for v in groups.values()): return [x, y]
    return None

def words(mode, args):
    names = sorted(SYL)
    if mode == "all":
        L = args[0]
        for w in itertools.product(names, repeat=L):
            if min(w[i:] + w[:i] for i in range(L)) == w: yield list(w)
    else:
        L, K = args
        others = [s for s in names if s != "S4"]
        seen = set()
        for k in range(0, min(K, L) + 1):
            for pos in itertools.combinations(range(L), k):
                for esc in itertools.product(others, repeat=k):
                    w = ["S4"] * L
                    for p_, e in zip(pos, esc): w[p_] = e
                    key = min(tuple(w[i:] + w[:i]) for i in range(L))
                    if key in seen: continue
                    seen.add(key); yield w

def main():
    mode = sys.argv[1]; args = [int(x) for x in sys.argv[2:]]
    t0 = time.time(); tested = valid = 0; hits = {}
    for w in words(mode, args):
        letters = [x for s in w for x in SYL[s]]
        m = order(pi_of(letters)); classes = m * sum(l for l, _ in letters)
        tested += 1
        if classes > 5040: continue
        sav = Fraction(classes, 6) - (m * len(letters) + 1)
        if sav <= 0: continue
        r = closed_chains(letters, m)
        if r is None: continue
        valid += 1
        chains, seen = r
        holefree = True
        for a, D, l, cl in chains:
            if l < n - 1:
                for c in orbit_classes(a, D):
                    if c not in seen: holefree = False; break
            if not holefree: break
        if not holefree: continue
        worlds = sorted({a for a, D, l, cl in chains})
        key = (classes, str(sav), len(worlds))
        if key in hits: continue
        rec = dict(word=" ".join(w), m=m, classes=classes, chains=m * len(letters), saving=str(sav),
                   rate=round((m * len(letters) + 1) / classes, 6), worlds=worlds, one_pair=one_pair_union(seen))
        hits[key] = rec
        print(json.dumps(dict(HOLEFREE=rec)), flush=True)
    out = dict(mode=mode, args=args, tested=tested, valid_positive=valid, holefree=list(hits.values()), sec=round(time.time() - t0, 1))
    print(json.dumps({k: v for k, v in out.items() if k != "holefree"}), flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"holefree_{mode}_{'_'.join(map(str, args))}.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
