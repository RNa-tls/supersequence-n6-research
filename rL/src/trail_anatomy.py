#!/usr/bin/env python3
"""Round L (section 9) -- exact anatomy of a closed syllable trail (default: the 1218-class trail
(S3 S3 S4 S2 S4 S4 S4)^6 of rK, rate 187/1218).

Reports: worlds; macro word (N(l) / F(j)); for every F-run its moving symbol w and its phi-set
P({a,w},C); pivot sequence (moving symbols in order and the pivot rule w -> w' at each N-chain);
orbits touched (full / partial); per pair {x,y} the histogram of |T cap P| over the 120 phi-sets;
holes and their 'partner' symbol (the symbol between the two missing gaps of an N5 = the world in
which the two holes are consecutive in one orbit); the (n-1)-level walk: chain orbits D as
7-cycles and the BAC moves as F-steps of world x0 on D.
usage: trail_anatomy.py ['WORD']"""
import sys, os, json, itertools
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import closed_letters
from worlds import World, canon_cyc

n = 8
W = World(n)
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
NAMES = {(1, 0, 7): "bac", (0, 1, 7): "skip", (0, 7, 1): "s071", (1, 7, 0): "s170", (7, 1, 0): "cba"}

def main():
    word = sys.argv[1] if len(sys.argv) > 1 else "S3 S3 S4 S2 S4 S4 S4"
    letters, Fp, T = closed_letters(n, word)
    P = tuple(range(n)); chains = []
    for l, s in letters:
        a = P[n - 1]
        cl = [W.cid[canon_cyc(list(comp(P, Fp[j])))] for j in range(l)]
        x = comp(P, Fp[l - 1])
        chains.append(dict(a=a, D=canon_cyc([z for z in P if z != a]), l=l, cl=cl, start=P, end=x, join=NAMES[s],
                           w=P[n - 2], exit_pair=(x[0], x[1])))
        P = comp(x, T(s))
    TS = set(c for ch in chains for c in ch["cl"])
    k = len(chains); size = len(TS)
    # macro word and F-runs
    macro = []; runs = []; i = 0
    while i < k:
        if chains[i]["l"] == 7:
            j = i
            while j + 1 < k and chains[j + 1]["l"] == 7 and chains[j]["join"] == "bac": j += 1
            ws = {chains[t]["w"] for t in range(i, j + 1)}
            assert len(ws) == 1, "phi-run lemma violated"
            w = ws.pop(); a = chains[i]["a"]
            C = canon_cyc([z for z in W.reps[chains[i]["cl"][0]] if z not in (a, w)])
            runs.append(dict(first=i, length=j - i + 1, w=w, a=a, C=C))
            macro.append(f"F{j - i + 1}"); i = j + 1
        else:
            macro.append(f"N{chains[i]['l']}"); i += 1
    # pivot sequence: moving symbol of each run, and the run's phi-set; N-chain pivot rule
    piv = []
    for r in runs:
        prev = chains[r["first"] - 1] if r["first"] > 0 else chains[-1]
        piv.append(dict(w=r["w"], prev_len=prev["l"], prev_exit_pair=prev["exit_pair"]))
    # N-chain pivot rule: N-chain starting with a after w (w = its own 'w'), length l, ends with a
    # followed by (d_l, d_l+1) where D = (w, d1, .., d6) read from w; next run moves d_l
    rule = Counter()
    for t, ch in enumerate(chains):
        if ch["l"] < 7:
            st = ch["start"]; a = st[n - 1]; w = st[n - 2]
            cyc = [z for z in W.reps[ch["cl"][0]] if z != a]
            kk = cyc.index(w); Dw = cyc[kk:] + cyc[:kk]
            nxt = chains[(t + 1) % k]
            rule[(ch["l"], Dw.index(nxt["w"]) if nxt["w"] in Dw else None)] += 1
    # orbits touched
    orb_full = sum(1 for ch in chains if ch["l"] == 7); orb_part = sum(1 for ch in chains if ch["l"] < 7)
    distinct_orbits = len({(ch["a"], ch["D"]) for ch in chains})
    # phi-set occupancy per pair
    occ = {}
    for x, y in itertools.combinations(range(n), 2):
        h = Counter()
        for key, mem in W.phi_sets(x, y).items():
            h[sum(1 for c in mem if c in TS)] += 1
        occ[f"{x}{y}"] = dict(sorted(h.items()))
    # holes and partner symbols
    holes = []; partner = Counter()
    for ch in chains:
        if ch["l"] < 7:
            mem = W.orbit_cycle(ch["a"], ch["D"])
            miss = [g for g, c in enumerate(mem) if c not in TS]
            holes += [mem[g] for g in miss]
            if len(miss) == 2 and (miss[1] - miss[0]) % 7 == 1:
                partner[ch["D"][(miss[0] + 1) % 7]] += 1        # symbol between the two missing gaps
    # (n-1)-level walk: BAC between chains = F-step of world x0 on D (7-cycle)
    steps = Counter()
    for t, ch in enumerate(chains):
        nxt = chains[(t + 1) % k]
        if ch["join"] == "bac":
            L = list(ch["D"]); x0, x1 = ch["exit_pair"]; i0 = L.index(x0); i1 = (i0 + 1) % 7
            assert L[i1] == x1
            L[i0], L[i1] = L[i1], L[i0]
            assert canon_cyc(L) == nxt["D"], "BAC is not the (n-1)-level F-step"
            steps["bac=F-step(x0)"] += 1
    res = dict(word=word, classes=size, chains=k, saving=round(size / 6 - (k + 1), 4), worlds=sorted({ch["a"] for ch in chains}),
               chain_lengths=dict(Counter(ch["l"] for ch in chains)), joins=dict(Counter(ch["join"] for ch in chains)),
               macro_period=" ".join(macro[:len(macro) // max(1, len(set([0])))]), runs=len(runs),
               run_lengths=dict(Counter(r["length"] for r in runs)), moving_symbols=dict(Counter(r["w"] for r in runs)),
               run_phi_sets_distinct=len({(min(r["a"], r["w"]), max(r["a"], r["w"]), r["C"]) for r in runs}),
               pivot_rule_N_len_to_index_of_next_w=dict((f"N{a}->d{b}", v) for (a, b), v in rule.items()),
               orbits_full=orb_full, orbits_partial=orb_part, distinct_orbits=distinct_orbits,
               holes=len(holes), distinct_holes=len(set(holes)), hole_partner_symbols=dict(partner),
               phi_occupancy_by_pair=occ, n_minus_1_level=dict(steps))
    print(json.dumps(res))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "anatomy_" + word.replace(" ", "") + ".json")
    json.dump(res, open(out, "w"), indent=1)

if __name__ == "__main__":
    main()
