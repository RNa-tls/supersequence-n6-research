#!/usr/bin/env python3
"""Round K -- search for NEW bundles among long syllable words (Round I scanned S/X words of length
<= 7 only).  Words: S4^L with up to MAXESC positions replaced by any other syllable S_r / X_r.
A valid closed trail W^m is a bundle if its class set is a union of whole phi-sets P({a,b},C) of
one pair; saving = classes/6 - (chains + 1).  Reports every bundle found (deduplicated by
saving/classes) and flags any with saving per class above bundle A's 7/672.
usage: long_bundle_search.py MAXLEN MAXESC"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from long_trail_search import SYL, pi_of, order, canon, comp, Fp, T, I, n
from fractions import Fraction
def closed_cls(letters, m):
    P = I; out = []; seen = set()
    for l, s in letters * m:
        for j in range(l):
            c = canon(comp(P, Fp[j]))
            if c in seen: return None
            seen.add(c); out.append(c)
        P = comp(P, comp(Fp[l - 1], T(s)))
    return out
def bundle_pairs(cls):
    S = set(cls); pairs = []
    for a, b in itertools.combinations(range(n), 2):
        groups = {}
        for c in cls:
            C = tuple(x for x in c if x not in (a, b)); k = C.index(min(C)); C = C[k:] + C[:k]
            groups[C] = groups.get(C, 0) + 1
        if all(v == (n - 2) * (n - 1) for v in groups.values()): pairs.append((a, b))
    return pairs
maxlen, maxesc = int(sys.argv[1]), int(sys.argv[2])
others = [k for k in SYL if k != "S4"]
t0 = time.time(); seen = set(); found = {}; tested = 0; valid = 0
for L in range(1, maxlen + 1):
    for k in range(0, min(maxesc, L) + 1):
        for pos in itertools.combinations(range(L), k):
            for esc in itertools.product(others, repeat=k):
                word = ["S4"] * L
                for p_, e in zip(pos, esc): word[p_] = e
                key = min(tuple(word[i:] + word[:i]) for i in range(L))
                if key in seen: continue
                seen.add(key)
                letters = [x for s in word for x in SYL[s]]
                m = order(pi_of(letters)); classes = m * sum(l for l, _ in letters)
                tested += 1
                if classes > 5040 or classes % 42: continue
                sav = Fraction(classes, 6) - (m * len(letters) + 1)
                if sav <= 0: continue
                cls = closed_cls(letters, m)
                if cls is None: continue
                valid += 1
                pr = bundle_pairs(cls)
                if pr:
                    rec = dict(word=" ".join(word), m=m, classes=classes, chains=m * len(letters), saving=str(sav),
                               per_class=float(sav / classes), pairs=[list(p) for p in pr])
                    kk = (classes, str(sav))
                    if kk not in found:
                        found[kk] = rec; print(json.dumps(dict(BUNDLE=rec, better_than_A=bool(sav / classes > Fraction(7, 672)))), flush=True)
    print(json.dumps(dict(L=L, tested=tested, valid_positive_mod42=valid, bundles=len(found), sec=round(time.time() - t0, 1))), flush=True)
json.dump(dict(maxlen=maxlen, maxesc=maxesc, tested=tested, bundles=list(found.values())),
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"long_bundle_search_{maxlen}_{maxesc}.json"), "w"), indent=1)
