#!/usr/bin/env python3
"""Round Y -- label coherence from the Round X disjoint-placement lists.
Each line of a list: "nameX nameY zeros zeros_rev | o:rank ..." with the Lehmer rank of a relabeling g in S8 (symbols
0..7, symbol 8 = index 7) such that X and g(Y) (o = 0) or g(reverse Y) (o = 1) share no class (rX/csrc/disjoint_bits.c,
LIST=1; the lists were produced and cross-checked by two implementations in Round X).  We decode every g and count
those with g(8) = 8 (the moving symbol of the first piece, 8 for every canonical chain, is kept).
usage: coherence_check.py LIST.txt [LIST.txt ...] OUT.json"""
import sys, math, json, hashlib
def unrank(r):
    avail = list(range(8)); g = []
    for i in range(8):
        f = math.factorial(7 - i); d = r // f; r %= f; g.append(avail.pop(d))
    return g
res = []
for fn in sys.argv[1:-1]:
    tot = same = 0; pairs = set(); pairs_cross = set(); lines = 0; counted = 0
    for l in open(fn):
        if l.startswith('#') or not l.strip(): continue
        a, _, b = l.partition('|'); t = a.split(); lines += 1
        z0, z1 = int(t[2]), int(t[3]); counted += z0 + z1
        for tok in b.split():
            o, r = map(int, tok.split(':')); g = unrank(r)
            assert sorted(g) == list(range(8))
            tot += 1; pairs.add((t[0], t[1]))
            if g[7] == 7: same += 1
            else: pairs_cross.add((t[0], t[1]))
    res.append(dict(file=fn, sha256=hashlib.sha256(open(fn, 'rb').read()).hexdigest(), pairs_listed=lines,
                    placements_counted=counted, placements_decoded=tot, keep_symbol_8=same, change_symbol_8=tot - same,
                    pairs_with_label_changing_placement=len(pairs_cross)))
    assert counted == tot, (fn, counted, tot)
json.dump(res, open(sys.argv[-1], 'w'), indent=1); print(json.dumps(res, indent=1))
