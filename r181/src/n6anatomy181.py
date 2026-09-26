#!/usr/bin/env python3
"""Round 181 -- anatomy of the n = 6 payload obstruction (r179 gap179: two 22-row trails).
For each trail: row specials, hidden classes, the 24 invisible classes grouped by their
c-words (H minus the dominant special), and omega = max number of invisible classes inside a
single non-row block.  If omega * 6 < 24 the obstruction is the counting bound
payload >= ceil(|Inv| / omega)."""
import json, os, sys
from itertools import permutations
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
n = 6; A = CheckerA(n)
rep = json.load(open("r179/certs/gap179.json"))
hexrep = lambda s: min(s[i:] + s[:i] for i in range(n))
allc = {hexrep(p) for p in permutations(range(n))}
out = []
for t in rep:
    rows = [(tuple(int(ch) for ch in s), l, ()) for s, l in t["trail"]]
    specials = Counter(r[0][-1] for r in rows)
    vis = set().union(*[A.visible(r) for r in rows])
    hidden = set()
    for r in rows:
        st = A.states(r[0], n - 1)
        for i in range(r[1], n - 1): hidden.add(hexrep(st[i]))
    inv = allc - vis
    rowblocks = {A.block(r[0]) for r in rows}
    # all blocks and their class sets
    blocks = {}
    for p in permutations(range(n)):
        b = A.block(p)
        if b not in blocks: blocks[b] = {hexrep(q) for q in A.states(p, n - 1)}
    over = Counter()
    for b, cls in blocks.items():
        if b in rowblocks: continue
        over[len(cls & inv)] += 1
    omega = max(k for k in over if over[k])
    sp = max(specials, key=specials.get)
    def cword(H):
        i = H.index(sp); w = H[i + 1:] + H[:i]; return hexrep(w)  # s-word of H: cyclic word of H minus sp
    groups = Counter(cword(H) for H in inv)
    o = dict(specials=dict(specials), hidden=len(hidden), invisible=len(inv), hidden_in_inv=len(hidden & inv),
             invisible_not_hidden=len(inv - hidden), omega=omega, overlap_hist=dict(sorted(over.items())),
             counting_bound=-(-len(inv) // omega), inv_by_cword=sorted(groups.values(), reverse=True))
    out.append(o); print(o)
json.dump(out, open("r181/certs/n6anatomy181.json", "w"), indent=1)
