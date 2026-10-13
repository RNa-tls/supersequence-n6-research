#!/usr/bin/env python3
"""Round L -- dual certificate (and its independent check) for 'the complement of the S4^10 12-packing
needs >= 240 chains'.

Generator: for each packing in rK/certs/s4_packing.json, R = complement; y_C = 1/2 if C lies in a
world-7 orbit meeting R in exactly two classes, y_C = 1/7 otherwise.  Claim: every chain (segment of
any world-orbit) lying inside R has sum of y <= 1, and sum_C y_C = 240.  By LP duality every chain
partition of R has >= 240 chains, hence E_R >= 240 - 1080/7 = 85.71 and sum_{T in R}(k_T+1) >= 241.
The checker below recomputes everything from scratch with exact fractions (independent of the
MIP in complement_s4.py): all 8 worlds, all orbits, all segments inside R.
usage: complement_cert.py"""
import os, sys, json, itertools
from fractions import Fraction

n = 8
def canon(seq):
    k = seq.index(0); return tuple(seq[k:] + seq[:k])
reps = sorted({canon(list(p)) for p in itertools.permutations(range(n))})
cid = {c: i for i, c in enumerate(reps)}
def orbit(a, D):
    out = []
    for g in range(len(D)):
        s = list(D[:g + 1]) + [a] + list(D[g + 1:]); out.append(cid[canon(s)])
    return out

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    d = json.load(open(os.path.join(here, "..", "..", "rK", "certs", "s4_packing.json")))
    res = []
    for pk, pack in enumerate(d["packings"]):
        used = 0
        for m in pack: used |= int(m, 16)
        R = {i for i in range(len(reps)) if not (used >> i) & 1}
        # orbits per world
        orbits = []
        for a in range(n):
            seen = set()
            for c in reps:
                D = [x for x in c if x != a]; k = D.index(min(D)); D = tuple(D[k:] + D[:k])
                if (a, D) in seen: continue
                seen.add((a, D)); orbits.append((a, orbit(a, D)))
        assert len(orbits) == 8 * 720
        y = {C: Fraction(1, 7) for C in R}
        for a, cyc in orbits:
            if a == 7 and sum(1 for c in cyc if c in R) == 2:
                for c in cyc:
                    if c in R: y[c] = Fraction(1, 2)
        total = sum(y.values())
        worst = Fraction(0); nseg = 0
        for a, cyc in orbits:
            m = len(cyc)
            for s in range(m):
                for l in range(1, m + 1):
                    seg = [cyc[(s + t) % m] for t in range(l)]
                    if all(c in R for c in seg):
                        v = sum(y[c] for c in seg); nseg += 1
                        if v > worst: worst = v
        ok = (worst <= 1 and total == 240)
        res.append(dict(packing=pk, R=len(R), dual_sum=str(total), max_segment_sum=str(worst), segments_checked=nseg, certificate_ok=ok))
        print(json.dumps(res[-1]), flush=True)
    json.dump(res, open(os.path.join(here, "..", "certs", "complement_cert.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
