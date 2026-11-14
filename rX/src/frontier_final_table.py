#!/usr/bin/env python3
"""Round X -- canonical table of the cells that survive the exceptional-chain knapsack (rX/src/frontier_exceptional.py),
with one optimal configuration per cell: the junction pattern, the exceptional chain (pieces, dmin_full) or none, and
the other chains (pieces, dmin_restricted), each with its values v1 = 4 r - 9 d, v2 = 17 r - 38 d.
CROSS = 1 (one exceptional chain for both lines) is used for the reconstruction; the counts of CROSS = 0 are the same
(checked by the caller).
usage: frontier_final_table.py EXCEPTIONAL_KNAPSACK.json OUT.json"""
import sys, json, hashlib
import numpy as np
d = json.load(open(sys.argv[1])); outp = sys.argv[2]
df = np.array(d["dmin_full"]); dr = np.array(d["dmin_restricted"]); RMAX, INF = 800, 10 ** 9
unit = np.full(RMAX + 1, INF); unit[0] = 0
br = np.full(RMAX + 1, INF); br[1:] = dr[1:]
def conv_arg(f, g):
    h = np.full(RMAX + 1, INF); a = np.zeros(RMAX + 1, dtype=int)
    for x in range(RMAX + 1):
        r = np.arange(0, x + 1); v = f[x - r] + g[r]; i = int(np.argmin(v)); h[x] = v[i]; a[x] = r[i]
    return h, a
PR, AR = [unit], [None]
for n in range(1, 41):
    h, a = conv_arg(PR[-1], br); PR.append(h); AR.append(a)
def partR(m, x):
    out = []
    while m > 0:
        r = int(AR[m][x]); out.append(r); x -= r; m -= 1
    return sorted(out, reverse=True)
fmt = lambda r, dd: dict(r=int(r), d=int(dd[r]), v1=int(4 * r - 9 * dd[r]), v2=int(17 * r - 38 * dd[r]))
rows = []
for c in d["rows"]:
    if c["excluded"]: continue
    R, n, D, F = c["R"], c["chains"], c["Delta"], c["F"]; a = c["junction_argmin"]
    Fi, Fii, sh = a["F_loops"], a["F_pairs"], a["shared_rows"]; pieces = R - Fi - (2 * Fii - sh); tgt = c["min_deficit"] - (Fi + 8 * Fii - 6 * sh)
    best = None
    for m in range(1, n - Fi - sh + 1):
        for r0 in range(1, pieces + 1):
            if PR[m - 1][pieces - r0] + df[r0] == tgt: best = (r0, partR(m - 1, pieces - r0)); break
        if best: break
        if PR[m][pieces] == tgt: best = (None, partR(m, pieces)); break
    assert best, c
    r0, rest = best
    rows.append(dict(R=R, p=c["p"], F=F, chains=n, Delta=D, min_deficit=c["min_deficit"], margin=c["margin"],
                     cluster="S0" if F == 0 else "SLM", F_loops=Fi, F_pairs=Fii, shared_rows=sh,
                     exceptional_chain=fmt(r0, df) if r0 else None, other_chains=[fmt(r, dr) for r in rest]))
res = dict(cells=len(rows), margin_histogram={str(k): sum(r["margin"] == k for r in rows) for k in range(-6, 1)},
           S0=sum(r["cluster"] == "S0" for r in rows), rows=rows)
s = json.dumps(res, indent=1); open(outp, "w").write(s)
print(json.dumps({k: v for k, v in res.items() if k != "rows"})); print("sha256", hashlib.sha256(s.encode()).hexdigest())
