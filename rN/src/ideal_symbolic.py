#!/usr/bin/env python3
"""Round N (section 6) -- symbolic structure of zero-excess (e = 0) joins between phi-cycles.

A phi-cycle of version v is a 3-cycle with world c (c = 0 for v = 0, c = 7 for v = 1), moving symbol
m (= 7 resp. 0) and a FRAME F = cyclic order of the other six symbols; its six chains are the
2-cycles 'm inserted into gap g of F'.  For every e = 0 join between options of two different
phi-trails this script records the frame change (F -> F') and checks:
  (i)   F' = F o (adjacent transposition of two frame symbols {x, y})            [4-cycle move]
  (ii)  for every option o that has an e = 0 in-join AND an e = 0 out-join, the two joins move a
        common frame symbol in the same cyclic direction (so a chain of e = 0 joins moves one symbol
        x step by step through the 5 gaps of F \\ {x}: it lies in one 4-cycle, hence has <= 5 trails).
usage: ideal_symbolic.py FAMILY.json E.npy"""
import sys, os, json
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def canon(seq):
    seq = list(seq); i = seq.index(min(seq)); return tuple(seq[i:] + seq[:i])

def frame_of(run_start):
    world = run_start[7]; m = 7 if world == 0 else 0
    r = list(run_start[:7]); return canon([x for x in r if x != m]), m, world

def transposition(F, G):
    """if G = F with two cyclically adjacent symbols swapped, return (x, y, direction) where x moves
    forward past y in F's cyclic order; else None"""
    n = len(F)
    for i in range(n):
        a, b = F[i], F[(i + 1) % n]
        H = list(F); H[i], H[(i + 1) % n] = b, a
        if canon(H) == G: return (a, b)
    return None

def main():
    fam, opts = OP.load(sys.argv[1]); E = np.load(sys.argv[2])
    phi = [i for i, o in enumerate(opts) if o["m"] == 42]
    fr = {}
    for i in phi:
        o = opts[i]
        F, m, w = frame_of(o["entry"])
        ex = o["exit"]; rs = ex[1:] + ex[:1]
        F2, m2, w2 = frame_of(rs)
        assert (F, m, w) == (F2, m2, w2)
        fr[i] = (F, m, w)
    kinds = Counter(); moves = {}
    for i in phi:
        for j in phi:
            if opts[i]["t"] == opts[j]["t"] or E[i, j] != 0: continue
            (F, m, w), (G, m2, w2) = fr[i], fr[j]
            tpos = transposition(F, G)
            tag = "same-world" if (m, w) == (m2, w2) else "cross-world"
            kinds[tag + (" adjacent transposition" if tpos else " OTHER")] += 1
            moves[(i, j)] = ("tr", tpos) if tpos else ("other", None)
    # consistency at options with ideal in and out
    cons = Counter(); bad = []
    ins = {}; outs = {}
    for (i, j), mv in moves.items(): outs.setdefault(i, []).append((j, mv)); ins.setdefault(j, []).append((i, mv))
    for o in phi:
        if o not in ins or o not in outs: continue
        for (i, mv1) in ins[o]:
            for (j, mv2) in outs[o]:
                if opts[i]["t"] == opts[j]["t"]: continue
                if mv1[0] != "tr" or mv2[0] != "tr": cons["involves non-transposition join"] += 1; continue
                (a1, b1), (a2, b2) = mv1[1], mv2[1]
                same = (a1 == a2) or (b1 == b2)
                cons["common moving symbol" if same else "NO common symbol"] += 1
                if not same and len(bad) < 5: bad.append((opts[i]["t"], opts[o]["t"], opts[j]["t"], mv1[1], mv2[1]))
    print(json.dumps(dict(ideal_joins=sum(kinds.values()), kinds=dict(kinds), consecutive_pairs=dict(cons), counterexamples=bad)))

if __name__ == "__main__":
    main()
