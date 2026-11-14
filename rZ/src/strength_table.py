#!/usr/bin/env python3
"""Round Z -- for every surviving cell of the 46135 frontier, the strength a new global statement must have to remove
it, read off the hypothetical knapsack runs of Round Y (rY/certs/hyp_*), and the proved symbol-change budget.
Columns:
  need      = 1 - margin                      extra deficit the cover must be shown to have (deficit units)
  need_v2   = 38 * need                       the same in line-2 value (one deficit unit = 38)
  cap150    = the largest c in {1,50,100,150,200} such that "every chain with >= 150 rows has 17r-38d <= c" removes it
  x2line2   = the largest theta2 in {220,200,180,150} such that "no two disjoint primitive parts of line-2 value >=
              theta2" removes it
  kappa1    = the largest theta1 in {45,44,42,40,36} such that "at most two disjoint primitive parts of line-1 value
              >= theta1" removes it
  Lmax1     = the proved budget of symbol changes inside chains, from 4r-9d+4L <= 56 summed over the n chains:
              4 L <= 56 n - V1   (V1 = 4R - 9 Delta)  -- a necessary condition, not an exclusion
usage: strength_table.py OUT.json"""
import json, re, sys
cells = json.load(open('rY/certs/frontier40_table.json'))['rows']
def survivors_from_caps(r0, cap):
    for line in open('rY/certs/hyp_long_chain_caps.txt'):
        head = json.loads(line[:line.index('}') + 1])
        if head['mode'] == 'LONG' and head['r0'] == r0 and head['cap'] == cap:
            return {(a, b) for a, b, _ in eval(line[line.index('survivors:') + 10:])}
    return None
def survivors_json(path):
    d = json.load(open(path)); return {(c['R'], c['F']) for c in d['rows'] if not c['excluded']}
caps = {c: survivors_from_caps(150, c) for c in (1, 50, 100, 150, 200)}
x2 = {t: survivors_json('rY/certs/hyp_line2_x2_%d.json' % t) for t in (220, 200, 180, 150)}
k1 = {t: survivors_json('rY/certs/hyp_kappa1_%d_le2.json' % t) for t in (45, 44, 42, 40, 36)}
rows = []
for c in cells:
    R, p, F = c['R'], c['p'], c['F']; key = (R, F); n = c['chains']
    need = 1 - c['margin']
    cap = max([cc for cc in caps if key not in caps[cc]], default=None)
    xt = max([t for t in x2 if key not in x2[t]], default=None)
    kt = max([t for t in k1 if key not in k1[t]], default=None)
    V1 = 4 * R - 9 * c['Delta']
    Lmax1 = (56 * n - V1) // 4
    rows.append(dict(R=R, p=p, F=F, n=n, margin=c['margin'], need=need, need_v2=38 * need, cap150=cap, x2line2=xt, kappa1=kt, Lmax1=Lmax1))
json.dump(rows, open(sys.argv[1], 'w'), indent=1)
print('| (R,p,F) | n | margin | need | need_v2 | cap150 | X2 line2 | kappa1 | L budget |')
for r in rows:
    print('| (%d,%d,%d) | %d | %d | %d | %d | %s | %s | %s | %d |' % (r['R'], r['p'], r['F'], r['n'], r['margin'], r['need'], r['need_v2'], r['cap150'], r['x2line2'], r['kappa1'], r['Lmax1']))
