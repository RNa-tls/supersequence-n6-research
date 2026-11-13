#!/usr/bin/env python3
"""Round V -- the entry lemma for closed walks of rows (n = 8 framework, states = orderings of 0..5).
For every state y0 and every short row (x, v), v in {1, 2, 3, 4}, with step(x, v) = y0, the loop of x is the loop of
G6^4(y0), the fifth loop of the orbit y0, G6(y0), .., G6^4(y0) of the full rows.
Consequence: in a closed walk through distinct loops a run of full rows that is entered by a short row has at most
three rows before the next short row.  Every closed walk other than 66666 is a cyclic sequence of segments 6^k v with
k <= 3, so  Q >= 2 * (number of segments) >= L / 2.
Also checked: the walk types of a library never contain 6666 followed by a short row.
usage: entry_lemma.py OUT.json [TYPES.txt ...]"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL
res = collections.Counter(); bad = 0
pre = {y: [] for y in SL.STATES}
for x in SL.STATES:
    for v in (1, 2, 3, 4): pre[SL.step(x, v)].append((x, v))
for y0 in SL.STATES:
    orb = [y0]
    for _ in range(4): orb.append(SL.step(orb[-1], 6))
    assert SL.step(orb[-1], 6) == y0 and len({SL.canon(y) for y in orb}) == 5
    loops = [SL.canon(y) for y in orb]
    for x, v in pre[y0]:
        j = loops.index(SL.canon(x)) if SL.canon(x) in loops else -1; res[(v, j)] += 1; bad += j != 4
out = dict(states=len(SL.STATES), short_predecessors_checked=sum(res.values()), predecessor_loop_index_in_orbit={"v%d_loop%d" % k: n for k, n in sorted(res.items())}, lemma_holds=bad == 0)
lib = []
for p in sys.argv[2:]:
    n = 0; viol = 0
    for l in open(p):
        q = l.split()
        if len(q) < 4: continue
        w = q[3] + q[3]; n += 1; viol += any(w[i:i + 4] == "6666" for i in range(len(q[3])))
    lib.append(dict(file=os.path.basename(p), types=n, types_with_four_consecutive_full_rows=viol))
out["libraries"] = lib
json.dump(out, open(sys.argv[1], "w"), indent=1); print(out)
