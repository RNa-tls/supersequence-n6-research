#!/usr/bin/env python3
"""Round V -- the 46135 frontier with the new piece-count lemma.
Census of csrc/dsearch.c (CENSUS=1) for a line a r <= b d + c: for every value v = a r - b d of a chain all of whose
nonempty prefixes have value in (0, c], the least number of pieces.  Lemma (suffix argument): every chain with value
>= v >= 1 has at least  m(v) = min over v' >= v of that least number  pieces.
Cell of the arithmetic of Theorem D at length 46134: R rows, p = X + J = 769 - R, F free junctions, n = 1 + p + F chains,
sum of the chain values = a R - b * 7 (R - 720).  A cell is EXCLUDED by the lemma if no n values v_i <= c with
sum m(v_i) <= R reach that sum (chains with v <= 0 cost one piece).  With two lines both conditions are tested.
usage: cells_tight.py CENSUS_LINE1.json [CENSUS_LINE2.json] OUT.json"""
import sys, json
def load(path):
    L = open(path).read().strip().split("\n"); head = json.loads(L[0]); body = json.loads(L[1]); a, b, c = head["params"]
    mr = {int(k): v for k, v in body["least_pieces_by_value"].items()}; m = {}; cur = 10 ** 9
    for v in range(c, 0, -1):
        if v in mr: cur = min(cur, mr[v])
        m[v] = cur
    return a, b, c, m, head, body
def maxsum(n, R, c, m):
    """max of sum v_i over n chains with sum of pieces <= R  (v <= 0: one piece, value 0)"""
    NEG = -10 ** 9; best = [NEG] * (R + 1); best[0] = 0
    opts = sorted({(1, 0)} | {(m[v], v) for v in m})
    # keep only undominated (pieces, value)
    und = []; top = -1
    for pc, v in sorted(opts, key=lambda t: (t[0], -t[1])):
        if v > top: und.append((pc, v)); top = v
    for _ in range(n):
        nb = [NEG] * (R + 1)
        for used in range(R + 1):
            if best[used] == NEG: continue
            for pc, v in und:
                if used + pc > R: break
                if best[used] + v > nb[used + pc]: nb[used + pc] = best[used] + v
        best = nb
    return max(best)
lines = [load(p) for p in sys.argv[1:-1]]; outp = sys.argv[-1]
cells = []
for R in range(747, 770):
    p = 769 - R; D = 7 * (R - 720)
    for F in range(0, 60):
        if not (4 * R + 5 * F <= 9 * D + 56 * (1 + p) and 17 * R + 6 * F <= 38 * D + 264 * (1 + p)): break
        n = 1 + p + F; s1 = 9 * D + 56 * n - 4 * R; s2 = 38 * D + 264 * n - 17 * R
        if s1 < 0 or s2 < 0: continue
        if not (s1 == 0 or s1 >= 3 or s2 >= 7): continue
        cells.append((R, p, F, n, D))
res = dict(cells=len(cells), lines=[dict(a=a, b=b, c=c, tight_chains_by_pieces=body.get("tight_chains_by_pieces"), least_pieces_for_value_at_least={str(v): m[v] for v in sorted(m) if v >= c - 30}) for a, b, c, m, head, body in lines])
surv = []; killed = 0; rows = []
for R, p, F, n, D in cells:
    ex = []
    for a, b, c, m, head, body in lines:
        V = a * R - b * D; ms = maxsum(n, R, c, m)
        if ms < V: ex.append("line %d %d %d: needs %d, at most %d" % (a, b, c, V, ms))
    rows.append(dict(R=R, p=p, F=F, chains=n, excluded=bool(ex), why=ex))
    if ex: killed += 1
    else: surv.append((R, F))
res.update(excluded=killed, surviving=len(surv), surviving_by_R={str(R): sorted(F for r, F in surv if r == R) for R in sorted({r for r, _ in surv})}, cells_detail=rows)
json.dump(res, open(outp, "w"), indent=1)
print("cells", len(cells), "excluded", killed, "surviving", len(surv)); print(res["surviving_by_R"])
for l in res["lines"]: print(l["a"], l["b"], l["c"], "tight:", l["tight_chains_by_pieces"], {k: v for k, v in l["least_pieces_for_value_at_least"].items()})
