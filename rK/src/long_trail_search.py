#!/usr/bin/env python3
"""Round K -- break attempt: long closed trails dominated by S4 syllables.

S4 = (5,bac)(7,bac)^4 has local rate 5/33 (the certified lower bound on every trail's rate) and
S4^10 is a closed valid trail (330 classes).  A word W = S4^a1 Y1 S4^a2 Y2 ... with short escapes Y
gives the closed trail W^m (m = order of the position product Pi(W)); it is valid iff its classes are
distinct (independent of the start).  rate = (m*chains(W) + 1) / (m*classes(W)).  Words are filtered
by rate BEFORE the (expensive) validity check; reported: every valid closed trail with rate below
the best known 127/822 = 0.154501..., and the best rates found.
usage: long_trail_search.py MAXLEN MAXESC"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import syllables, comp
n = 8
SYL = syllables(n)
I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
T = lambda s: tuple(list(range(2, n - 1)) + list(s))
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
def pi_of(letters):
    P = I
    for l, s in letters: P = comp(P, comp(Fp[l - 1], T(s)))
    return P
def order(P):
    m = 1; X = P
    while X != I: X = comp(X, P); m += 1
    return m
def valid_closed(letters, m):
    P = I; seen = set()
    for l, s in letters * m:
        for j in range(l):
            c = canon(comp(P, Fp[j]))
            if c in seen: return False
            seen.add(c)
        P = comp(P, comp(Fp[l - 1], T(s)))
    return True
BEST_KNOWN = 127 / 822
def main():
    maxlen, maxesc = int(sys.argv[1]), int(sys.argv[2])
    esc_names = [k for k in SYL if k != "S4"]
    t0 = time.time(); tested = 0; checked = 0; found = []; best = []
    seen_cyc = set()
    for L in range(1, maxlen + 1):
        for k in range(0, min(maxesc, L) + 1):
            for pos in itertools.combinations(range(L), k):
                for esc in itertools.product(esc_names, repeat=k):
                    word = ["S4"] * L
                    for p_, e in zip(pos, esc): word[p_] = e
                    rots = [tuple(word[i:] + word[:i]) for i in range(L)]
                    key = min(rots)
                    if key in seen_cyc: continue
                    seen_cyc.add(key)
                    letters = [x for s in word for x in SYL[s]]
                    chains = len(letters); classes = sum(l for l, _ in letters)
                    m = order(pi_of(letters)); tested += 1
                    if m * classes > 5040: continue
                    rate = (m * chains + 1) / (m * classes)
                    if rate >= BEST_KNOWN - 1e-12 and len(best) >= 5 and rate >= best[-1][0]: continue
                    checked += 1
                    if not valid_closed(letters, m): continue
                    rec = (rate, " ".join(word), m, m * chains, m * classes)
                    best.append(rec); best.sort(); best = best[:15]
                    if rate < BEST_KNOWN - 1e-12:
                        found.append(rec); print(json.dumps(dict(NEW_BETTER_TRAIL=rec)), flush=True)
        print(json.dumps(dict(L=L, tested=tested, checked=checked, sec=round(time.time() - t0, 1))), flush=True)
    out = dict(maxlen=maxlen, maxesc=maxesc, tested=tested, checked=checked, better_than_known=found,
               best=[dict(rate=r, word=w, m=m, chains=c, classes=k) for r, w, m, c, k in best])
    print(json.dumps(out), flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"long_trail_search_{maxlen}_{maxesc}.json"), "w"), indent=1)
if __name__ == "__main__":
    main()
