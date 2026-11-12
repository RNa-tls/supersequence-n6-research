#!/usr/bin/env python3
"""Round V -- selections in Pantone's completion framework for n = 8 (K = 6 loop letters 0..5, s = 6, z = 7).
A selection gives every loop (cyclic order of 012345) a row (x, v), v in {1, 2, 3, 4, 6}, or no row.  The rows must
be balanced: the row after (x, v) starts at step(x, v), which must be the row of its loop.
This module: the state graph, walks and trails of a selection, its closed trails as cyclic words (own construction,
rT/src/build_from_selection.py), run-level arcs for the exact path programme, and words of routes."""
import sys, os, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rT", "src"))
import build_from_selection as BS
import model as MD
K = 6
VS = (1, 2, 3, 4, 6)
STATES = ["".join(p) for p in itertools.permutations("012345")]
SID = {x: i for i, x in enumerate(STATES)}
def canon(x):
    i = x.index("0"); return x[i:] + x[:i]
LOOPS = sorted({canon(x) for x in STATES}); LID = {l: i for i, l in enumerate(LOOPS)}
def step(x, v):
    if v == K: return x[1:K - 1] + x[0:1] + x[K - 1:K]
    return x[v + 1:] + x[:v - 1] + x[v:v + 1] + x[v - 1:v]
def port_perm(v, j):
    if v == K: return (j - 1) % (K - 1)
    if j < v: return j + K - v - 1
    if j == v: return K - v - 2
    return j - v - 1
def walks_of(rows):
    """rows: dict state -> v.  Returns list of walks, each a list of (x, v) in order."""
    seen = set(); out = []
    for x0 in rows:
        if x0 in seen: continue
        wk = []; x = x0
        while x not in seen:
            seen.add(x); wk.append((x, rows[x])); x = step(x, rows[x]); assert x in rows, "unbalanced selection"
        assert x == x0, "not a closed walk"
        out.append(wk)
    return out
def trails_of_walk(wk):
    ports = list(range(K - 1))
    for x, v in wk: ports = [port_perm(v, j) for j in ports]
    seen = set(); n = 0
    for j in range(K - 1):
        if j in seen: continue
        n += 1; q = j
        while q not in seen: seen.add(q); q = ports[q]
    return n
def summary(rows):
    wks = walks_of(rows); used = {canon(x) for x in rows}; assert len(used) == len(rows), "two rows in one loop"
    Q = sum(K - v for v in rows.values()); rowless = len(LOOPS) - len(used); tw = [trails_of_walk(w) for w in wks]
    return dict(Q=Q, rowless=rowless, walks=len(wks), walk_lengths=sorted((len(w) for w in wks), reverse=True), walk_trails=tw, T=rowless + sum(tw),
                row_words=sorted("".join(str(v) for _, v in w) for w in wks))
def lines(rows):
    used = {canon(x) for x in rows}
    return [(x, v) for x, v in rows.items()] + [(l, 0) for l in LOOPS if l not in used]
def closed_trails(rows):
    """cyclic words of the closed trails (own slice construction)"""
    return [c for c, _ in BS.trails(lines(rows))]
def arcs_of(cyc):
    """run-level arcs: per trail, per run y: (trail, y, cost = 3 - c_in, head7, tail7); also the entry permutations"""
    arcs = []; entries = []
    for t, c in enumerate(cyc):
        rs = MD.runs_of(c); d = c + c; ent = [d[r[0]:r[0] + 8] for r in rs]; entries.append(ent); m = len(rs)
        for i in range(m): arcs.append((t, i, 0, 3 - rs[i - 1][2], ent[i][:7], ent[i - 1][:7]))
    return arcs, entries
def write_arcs(path, arcs):
    open(path, "w").write("".join("%d %d %d %d %s %s\n" % a for a in arcs))
def word_of(entries, witness):
    """witness: list of (trail, start run index).  Runs of each trail from its start run around."""
    route = []
    for t, i in witness:
        m = len(entries[t]); route += [entries[t][(i + q) % m] for q in range(m)]
    w = route[0] + route[0][:7]
    for a, b in zip(route, route[1:]):
        last = a[7] + a[:7]; k = next((k for k in range(7, 0, -1) if last[8 - k:] == b[:k]), 0); w += b[k:] + b[:7]
    return w
def read_selection(path):
    rows = {}
    for l in open(path):
        if not l.strip() or l.startswith("#"): continue
        x, v = l.split()[0], int(l.split()[1])
        if v > 0: rows[x] = v
    return rows
if __name__ == "__main__":
    rows = read_selection(sys.argv[1]); s = summary(rows); print(s)
    cyc = closed_trails(rows); arcs, ent = arcs_of(cyc); print("trails", len(cyc), "runs", sum(len(e) for e in ent), "sum R", sum(len(c) for c in cyc), "arcs", len(arcs))
    if len(sys.argv) > 2: write_arcs(sys.argv[2], arcs)
