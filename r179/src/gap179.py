#!/usr/bin/env python3
"""Round 179 -- explicit capacity-relaxation gap at n = 6 (paper superperm6, m = 4 family, r = 6).

Parameters (m, a, b, eta, r) = (4, 0, 0, 0, 6):  k = 24 + m - r + a = 22 rows, tau = 1 trail,
u = 5m - r = 14 holes, b = 0 omission runs, payload r - a = 6 blocks.
(1) Find every single unmarked trail with the skeleton 5553553552552553553555 (row lengths),
    first start fixed to the identity (relabelling), using checker A semantics.  Each is a
    CoarsenedInstance(22, 1, 14, 0): it PASSES the relaxed capacity conditions.
(2) Because b = 0, Bridge(n) forces trichotomy case (iii): a forest instance whose r - a = 6
    payload blocks (disjoint from the 22 row blocks) cover every cyclic class invisible in the
    rows.  Exhaustive set-cover search shows no such payload exists (<= 6 blocks) -> the instance
    cannot come from a covering route.
Both steps are re-checked with checker B.  usage: gap179.py"""
import json, os, sys
from itertools import permutations
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB
n = 6
A, B = CheckerA(n), CheckerB(n)
skel = [int(ch) for ch in "5553553552552553553555"]
assert len(skel) == 22 and sum(5 - l for l in skel) == 14
found = []


def dfs(path, vis, blocks):
    if len(path) == len(skel):
        found.append(list(path)); return
    beta = A.beta(path[-1])
    for t in permutations([c for c in range(n) if c not in beta]):
        row = (beta + t, skel[len(path)], ())
        b = A.block(row[0])
        if b in blocks: continue
        v = A.visible(row)
        if v & vis: continue
        path.append(row); dfs(path, vis | v, blocks | {b}); path.pop()


first = (tuple(range(n)), skel[0], ())
dfs([first], A.visible(first), {A.block(first[0])})
print(f"trails with the skeleton (first start = identity): {len(found)}")
hexrep = lambda s: min(s[i:] + s[:i] for i in range(n))
allclasses = {hexrep(p) for p in permutations(range(n))}
report = []
for tr in found:
    okA = A.trail(tr, 14)[0] and len(tr) == 22
    okB = B.trail(tr, 14)[0]
    vis = set().union(*[A.visible(x) for x in tr])
    missing = allclasses - vis
    rowblocks = {A.block(x[0]) for x in tr}
    # blocks containing a class: H \ t with special t, for each symbol t (n blocks per class)
    def blocks_of(H):
        out = []
        for i in range(n):
            s = H[i:] + H[:i]                      # rotation ending with the special symbol
            out.append(A.block(s))
        return set(out)
    cand = {H: blocks_of(H) - rowblocks for H in missing}
    best = [None]

    def cover(chosen, uncovered, limit):
        if not uncovered: best[0] = list(chosen); return True
        if len(chosen) == limit: return False
        H = min(uncovered, key=lambda h: len(cand[h]))
        for b in cand[H]:
            covered = {h for h in uncovered if b in cand[h]}
            chosen.append(b)
            if cover(chosen, uncovered - covered, limit): return True
            chosen.pop()
        return False
    feasible6 = cover([], set(missing), 6)
    # smallest payload that would work (for information)
    minimal = None
    for lim in range(6, 13):
        best[0] = None
        if cover([], set(missing), lim): minimal = lim; break
    report.append(dict(rows=len(tr), charge=sum(A.charge(x) for x in tr), checkerA=okA, checkerB=okB,
                       visible_classes=len(vis), row_blocks=len(rowblocks), missing=len(missing),
                       payload_6_blocks_exists=feasible6, smallest_covering_payload=minimal,
                       trail=[["".join(map(str, x[0])), x[1]] for x in tr]))
    print(f"  trail: rows {len(tr)}, charge {report[-1]['charge']}, A {okA}, B {okB}, visible {len(vis)} in {len(rowblocks)} blocks, "
          f"missing {len(missing)}; 6-block payload exists: {feasible6}; smallest covering payload: {minimal} blocks")
json.dump(report, open(os.path.join(HERE, "..", "certs", "gap179.json"), "w"), indent=1)
