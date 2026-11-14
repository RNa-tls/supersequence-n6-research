#!/usr/bin/env python3
"""Round Z -- independent check of the block model of rZ/src/block_configs.py against the class model.
For every one of the 120 {z,t}-blocks with z = 8, t = 7 (symbols 1..8; the other six in a 6-cycle E), the 42 classes
(cyclic words) are built directly; for every z-2-cycle (row) and t-2-cycle (column) of the block the classes are
listed in the order produced by the door step (the moving symbol passes its right neighbour), and compared with the
abstract orders:  row R_h: (h+1,h), ..., (h-1,h), Dzt_h, Dtz_h;  column C_g: (g,g+1), ..., (g,g-1), Dtz_g, Dzt_g.
Also: the 6 rows and the 6 columns each partition the 42 classes, every row meets every column, in one class off the
diagonal and in two on it.  usage: block_check.py"""
import itertools
def canon(w):
    k = w.index(1); return tuple(w[k:] + w[:k])
def word_with(E, zg, tg, order):
    """E: 6 symbols in cyclic order; place z=8 in gap zg (between E[zg-1] and E[zg]) and t=7 in gap tg; if zg == tg,
    order = 'zt' or 'tz' gives their order inside the gap."""
    out = []
    for i in range(6):
        if i == zg and i == tg: out += [8, 7] if order == 'zt' else [7, 8]
        elif i == zg: out.append(8)
        elif i == tg: out.append(7)
        out.append(E[i])
    return canon(out)
def next_class(X, m):
    """the class after X in the 2-cycle of the moving symbol m: m passes its right neighbour"""
    X = list(X); k = X.index(m); j = (k + 1) % 8; X[k], X[j] = X[j], X[k]; return canon(X)
ok = 0; bad = 0; blocks = 0
for perm in itertools.permutations(range(2, 7)):
    E = (1,) + perm
    # the 6-cycles on {1..6} with E[0] = 1: 5! = 120, one per block
    blocks += 1
    cls = {}
    for g in range(6):
        for h in range(6):
            if g != h: cls[('c', g, h)] = word_with(E, g, h, None)
        cls[('zt', g)] = word_with(E, g, g, 'zt'); cls[('tz', g)] = word_with(E, g, g, 'tz')
    assert len(set(cls.values())) == 42
    for h in range(6):
        want = [cls[('c', (h + k) % 6, h)] for k in range(1, 6)] + [cls[('zt', h)], cls[('tz', h)]]
        got = [want[0]]
        for _ in range(6): got.append(next_class(got[-1], 8))
        ok += got == want; bad += got != want
    for g in range(6):
        want = [cls[('c', g, (g + k) % 6)] for k in range(1, 6)] + [cls[('tz', g)], cls[('zt', g)]]
        got = [want[0]]
        for _ in range(6): got.append(next_class(got[-1], 7))
        ok += got == want; bad += got != want
print('blocks', blocks, 'orders checked', ok + bad, 'agree', ok, 'disagree', bad)
