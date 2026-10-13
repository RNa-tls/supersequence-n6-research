#!/usr/bin/env python3
"""Join lemma J2 for bundle B (syllable word "S2 S2 S2 S3 X3", k = 12 arrangements, saving 3) and,
as a control, bundle A ("S3 S4 S3 S4 X4"), in the {0,7}-system of n = 8.

For a bundle G (its chains, realization X or X', orientation = optional swap of the pair symbols),
every cheap join (cost <= 4) between a chain of G and a chain outside G is classified:
  * the partner's arrangement C lies in G's arrangement set  -> internal (not a join between cycles);
  * the partner is a phi-chain start / last start with C outside G -> a realizable G <-> phi join;
  * the partner is a chain of some A- or B-image disjoint from G -> realizable bundle-bundle join;
  * otherwise -> the partner cannot be a chain boundary of an exact partition (non-admissible).
Lemma J2 (phi part) for G: no realizable G <-> phi join of cost <= 4 exists, i.e. every join
between G and a phi-cycle costs >= 5, for every packing containing G.

X' realization: the X-syllable [(5,CBA),(6,BAC),(7,CBA),(4,BAC)] is replaced by
[(5,BCA),(6,BAC),(6,BCA),(5,BAC)] (same length); it is used only if its closed trail covers the
same classes as the X realization up to a relabelling (checked)."""
import sys, os, json, itertools
from collections import Counter
n = 8
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
T = lambda s: tuple(list(range(2, n - 1)) + list(s))
BAC, CBA, BCA = (1, 0, n - 1), (n - 1, 1, 0), (1, n - 1, 0)
S_ = lambda r: [(n - 3, BAC)] + [(n - 1, BAC)] * r
X_ = lambda r: [(n - 3, CBA), (n - 2, BAC), (n - 1, CBA), (n - 4, BAC)] + [(n - 1, BAC)] * r
Xp_ = lambda r: [(5, BCA), (6, BAC), (6, BCA), (5, BAC)] + [(n - 1, BAC)] * r

def closed_chains(letters):
    """chains (start perm, length) of the closed trail of a letter sequence started at the identity"""
    Pi = I
    for l, s in letters: Pi = comp(Pi, comp(Fp[l - 1], T(s)))
    m = 1; X = Pi
    while X != I: X = comp(X, Pi); m += 1
    P = I; out = []
    for l, s in letters * m:
        out.append((P, l)); P = comp(P, comp(Fp[l - 1], T(s)))
    assert P == I
    return out
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
def classes(chs):
    out = []
    for s, l in chs:
        x = s
        for _ in range(l): out.append(canon(x)); x = comp(x, F)
    return out
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):
    k = p.index(0); w_ = list(p[k:] + p[:k]); return cyc_canon([v for v in w_ if v not in (0, n - 1)])
Rinv = lambda s: s[-1:] + s[:-1]
def last_of(s, l):
    x = s
    for _ in range(l - 1): x = comp(x, F)
    return x

def realizations(word_X, word_Xp, pair):
    """chains of the X and X' realizations, relabelled so that the trail's special pair becomes (0, 7)"""
    chX = closed_chains(word_X); clX = classes(chX)
    assert len(set(clX)) == len(clX)
    rest = [v for v in range(n) if v not in pair]
    sig = [0] * n; sig[pair[0]] = 0; sig[pair[1]] = n - 1
    for i, v in enumerate(rest): sig[v] = i + 1
    relab = lambda chs: [(tuple(sig[x] for x in s), l) for s, l in chs]
    out = {"X": relab(chX)}
    chP = closed_chains(word_Xp); clP = classes(chP)
    if len(set(clP)) == len(clP) and len(clP) == len(clX):
        target = frozenset(clX)
        for g in itertools.permutations(range(n)):
            if frozenset(canon(tuple(g[x] for x in c)) for c in clP) == target:
                out["X'"] = relab([(tuple(g[x] for x in s), l) for s, l in chP]); break
    return out

# words and special pairs as recorded in rI/certs/bundles_n8.json
shapes = {"A": (S_(3) + S_(4) + S_(3) + S_(4) + X_(4), S_(3) + S_(4) + S_(3) + S_(4) + Xp_(4), (2, 7)),
          "B": (S_(2) + S_(2) + S_(2) + S_(3) + X_(3), S_(2) + S_(2) + S_(2) + S_(3) + Xp_(3), (3, 7))}
sw = {0: n - 1, n - 1: 0}
def image(chs, g, ori):
    out = []
    for s, l in chs:
        s2 = tuple(g[v] for v in s)
        if ori: s2 = tuple(sw.get(v, v) for v in s2)
        out.append((s2, l))
    return out
def Cset(chs):
    return frozenset(Cof(x) for s, l in chs for x in [s] + [last_of(s, k + 1) for k in range(1, l)])

real = {name: realizations(*w) for name, w in shapes.items()}
for name in real: print(name, "realizations:", sorted(real[name]), "chains:", len(real[name]["X"]), flush=True)
# every image of A and B (relabel 1..6, realization, orientation): chain starts / last starts -> C-sets
start_imgs, last_imgs = {}, {}
for name in real:
    for rk, chs in real[name].items():
        for perm in itertools.permutations(range(1, n - 1)):
            g = [0] + list(perm) + [n - 1]
            for ori in (0, 1):
                im = image(chs, g, ori); CS = Cset(im)
                for s, l in im:
                    start_imgs.setdefault(s, set()).add(CS); last_imgs.setdefault(last_of(s, l), set()).add(CS)
pairs = (0, n - 1)
phi_start = lambda t: t[n - 2] in pairs and t[n - 1] in pairs
phi_last = lambda x: x[0] in pairs and x[n - 1] in pairs
allp = [p for p in itertools.permutations(range(n)) if p[n - 1] in pairs]
byprefix, tails = {}, {}
for p in allp:
    for k in range(4, n):
        byprefix.setdefault(p[:k], []).append(p); tails.setdefault(Rinv(p)[n - k:], []).append(p)
report = []
for name in real:
    for rk, chs0 in real[name].items():
        for ori in (0, 1):
            chs = image(chs0, list(range(n)), ori); G = Cset(chs)
            st = Counter()
            for s, l in chs:
                e = Rinv(last_of(s, l))
                for k in range(4, n):                     # OUT joins of cost n-k <= 4
                    for t in byprefix.get(e[n - k:], []):
                        if Cof(t) in G: continue
                        if phi_start(t): st["OUT->phi (cost<=4, realizable)"] += 1
                        elif t in start_imgs:
                            st["OUT->bundle disjoint" if any(not (H & G) for H in start_imgs[t]) else "OUT->bundle overlapping only"] += 1
                        else: st["OUT->non-admissible"] += 1
                for k in range(4, n):                     # IN joins of cost n-k <= 4
                    for xp in tails.get(s[:k], []):
                        if Cof(xp) in G: continue
                        if phi_last(xp): st["IN<-phi (cost<=4, realizable)"] += 1
                        elif xp in last_imgs:
                            st["IN<-bundle disjoint" if any(not (H & G) for H in last_imgs[xp]) else "IN<-bundle overlapping only"] += 1
                        else: st["IN<-non-admissible"] += 1
            r = dict(bundle=name, realization=rk, orientation=ori, arrangements=len(G), chains=len(chs), **st)
            r["J2_phi_holds"] = st["OUT->phi (cost<=4, realizable)"] == 0 and st["IN<-phi (cost<=4, realizable)"] == 0
            report.append(r); print(json.dumps(r), flush=True)
json.dump(report, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "bundle_join_lemma_B.json"), "w"), indent=1)
