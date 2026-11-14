#!/usr/bin/env python3
"""Round Z -- covers of one {z,t}-block in which one world has at most 3 used 2-cycles (exact enumeration).

Block B({z,t}, E), E = e_0 .. e_5 a 6-cycle; gap g of E lies between e_{g-1} and e_g.  Classes: (g, h) = z in gap g,
t in gap h (g != h, 30 classes), and for every gap g the two classes with z and t both in gap g: Dzt_g (z before t)
and Dtz_g (t before z).  42 classes.
  z-2-cycle (row) R_h = {classes with t in gap h}; z moving forward visits (h+1,h), (h+2,h), ..., (h-1,h), Dzt_h, Dtz_h.
  t-2-cycle (column) C_g = {classes with z in gap g}; t moving forward visits (g,g+1), ..., (g,g-1), Dtz_g, Dzt_g.
(The orders are checked against the class model in rZ/src/block_check.py.)
Every class needs its row or its column, so a block cover uses all 6 rows or all 6 columns.  We enumerate the covers
with b <= 3 used columns (all 6 rows used): choose the columns and one arc in each (or several arcs = a split column,
not allowed here), then every row must be the complementary arc of its remaining classes (one arc, no split row).
The case "a <= 3 rows, all columns" is the same enumeration with the roles of rows and columns exchanged.
For every cover: b, the multiset of z-row sizes and of t-row sizes, W_B = 7 b, partial rows, 6-rows.
usage: block_configs.py OUT.json"""
import sys, json, itertools, collections
classes = [('c', g, h) for g in range(6) for h in range(6) if g != h] + [('zt', g) for g in range(6)] + [('tz', g) for g in range(6)]
cid = {c: i for i, c in enumerate(classes)}
rows = [[cid[('c', (h + k) % 6, h)] for k in range(1, 6)] + [cid[('zt', h)], cid[('tz', h)]] for h in range(6)]
cols = [[cid[('c', g, (g + k) % 6)] for k in range(1, 6)] + [cid[('tz', g)], cid[('zt', g)]] for g in range(6)]
def arcs(cy):
    out = [frozenset(cy)]
    for s in range(7):
        for l in range(1, 7): out.append(frozenset(cy[(s + i) % 7] for i in range(l)))
    return out
def is_arc(cy, S):                      # S nonempty subset of the cyclic order cy: one arc?
    if len(S) == 7: return True
    inS = [c in S for c in cy]
    starts = sum(1 for i in range(7) if inS[i] and not inS[i - 1])
    return starts == 1
def enumerate_side(major, minor):
    res = collections.Counter(); n = 0
    for b in range(0, 4):
        for J in itertools.combinations(range(6), b):
            for choice in itertools.product(*[arcs(minor[j]) for j in J]):
                T = set()
                ok = True
                for A in choice:
                    if T & A: ok = False; break
                    T |= A
                if not ok: continue
                zs = []
                for cy in major:
                    rem = [c for c in cy if c not in T]
                    if not rem: ok = False; break          # the row would be unused: then a < 6 and b = 6, not this case
                    if not is_arc(cy, set(rem)): ok = False; break
                    zs.append(len(rem))
                if not ok: continue
                ts = sorted((len(A) for A in choice), reverse=True); zs.sort(reverse=True)
                res[(b, tuple(zs), tuple(ts))] += 1; n += 1
    return res, n
rz, nz = enumerate_side(rows, cols)      # all rows used, b <= 3 columns
rt, nt = enumerate_side(cols, rows)      # all columns used, a <= 3 rows
types = []
for side, R in (('z-major (a=6, b<=3)', rz), ('t-major (b=6, a<=3)', rt)):
    for (m, maj, mino), cnt in sorted(R.items()):
        sizes = list(maj) + list(mino)
        types.append(dict(side=side, minor_cycles=m, major_rows=list(maj), minor_rows=list(mino), covers=cnt, W_B=7 * m,
                          partial_rows=sum(1 for x in sizes if x < 7), six_rows=sum(1 for x in sizes if x == 6),
                          non6_partial=sum(1 for x in sizes if x < 6), holes=sum(7 - x for x in sizes)))
res = dict(covers_z_major=nz, covers_t_major=nt, types=types)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print('covers with a = 6, b <= 3:', nz, ' with b = 6, a <= 3:', nt, ' types:', len(types))
best = collections.defaultdict(lambda: None)
for t in types:
    if t['side'].startswith('z'):
        k = t['minor_cycles']
        if best[k] is None or t['non6_partial'] > best[k]['non6_partial']: best[k] = t
for k in sorted(best): print('b =', k, 'max non-6 partial rows:', best[k]['non6_partial'], best[k])
for t in types:
    if t['side'].startswith('z') and t['minor_cycles'] <= 2: print(t)
