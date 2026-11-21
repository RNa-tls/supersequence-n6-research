#!/usr/bin/env python3
"""Round Omega -- build a frontier_compat.py configuration from coexistence tables (compat2d.py output) and the
two-sided tables of a table directory.

For a line with packing threshold LO, grid g_0 = LO < ... < g_k (all present in the coexistence table):
  Z     table <prefix>_lt<LO>.txt                        (census < LO)
  S[i]  table <prefix>_lt<g_{i+1}>_th<LO>.txt  (top level: <prefix>_full_th<LO>.txt)
  D     table given explicitly (full census, Case B restricted by the incompatible rectangles)
Compat(i, j) = table entry for (max(g_i, g_j), min(g_i, g_j)).
The incompatible rectangles for the D table are printed (the minimal pairs (p, q), p >= q, with Compat false).
usage: make_compat_config.py OUT.json CELLS.json ONLY.json|- NMAX
           L1:COMPAT.json:TABDIR:prefix:grid(comma):- L2:COMPAT.json:TABDIR:prefix:grid:-   (D tables <prefix>_D_lt<g>.txt / _D_full.txt)"""
import sys, json
out, cells, only, nmax = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
cfg = dict(rmax=800, nmax=nmax, cells=cells, only=None if only == '-' else only)
for spec in sys.argv[5:]:
    key, cpath, tdir, prefix, grid, dtab = spec.split(':')
    grid = [int(x) for x in grid.split(',')]; T = json.load(open(cpath))['table']
    LO = grid[0]; n = len(grid)
    def comp(a, b):
        k = '%d,%d' % (max(a, b), min(a, b)); return bool(T[k]['compatible'])
    C = [[int(comp(grid[i], grid[j])) for j in range(n)] for i in range(n)]
    kinds = [dict(name='Z', nu=0, table='%s/%s_lt%d.txt' % (tdir, prefix, LO))]
    for i in range(n):
        tab = '%s/%s_lt%d_th%d.txt' % (tdir, prefix, grid[i + 1], LO) if i + 1 < n else '%s/%s_full_th%d.txt' % (tdir, prefix, LO)
        kinds.append(dict(name='S%d' % grid[i], nu=1, level=i, table=tab))
    for i in range(n):              # D[i]: census < g_{i+1} (top: full), Case B restricted by the rectangles
        tab = '%s/%s_D_lt%d.txt' % (tdir, prefix, grid[i + 1]) if i + 1 < n else '%s/%s_D_full.txt' % (tdir, prefix)
        kinds.append(dict(name='D%d' % grid[i], nu=2, level=i, table=tab))
    rects = []
    for i in range(n):
        for j in range(i + 1):
            if not C[i][j] and not any(grid[i] >= p and grid[j] >= q for p, q in rects): rects.append((grid[i], grid[j]))
    print(key, 'grid', grid, 'incompatible rectangles (p >= q):', rects)
    cfg['line1' if key == 'L1' else 'line2'] = dict(levels=grid, compat=C, kinds=kinds, rectangles=rects)
json.dump(cfg, open(out, 'w'), indent=1)
