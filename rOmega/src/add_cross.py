#!/usr/bin/env python3
"""Round Omega -- add a cross-line coexistence matrix X12 to a frontier_compat configuration.

X12[i][j], i on the joint grid of line 1 (sub-levels first), j on the joint grid of line 2: false means that no
line-1 primitive part of level >= i and line-2 primitive part of level >= j can lie in different chains (row-disjoint).
Entries come from compat_cross.py tables (each table states which line its X side and its Y side belong to).
An entry is FALSE if some proved false entry (a, b) has a <= level_1(i) and b <= level_2(j) (antitone: more value
cannot restore compatibility); otherwise TRUE (true = no constraint, always sound).  Sub-level/sub-level entries are
left true.
usage: add_cross.py IN.json OUT.json  TABLE.json:xline(1|2) ..."""
import sys, json
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
falses = []                                  # (line-1 threshold, line-2 threshold) pairs proved incompatible
for spec in sys.argv[3:]:
    path, xline = spec.rsplit(':', 1); T = json.load(open(path))['table']
    for k, e in T.items():
        a, b = map(int, k.split(','))
        if not e['compatible']:
            falses.append((a, b) if xline == '1' else (b, a))
def joint(L): return L.get('sublevels', []) + L['levels']
g1, g2 = joint(cfg['line1']), joint(cfg['line2'])
q1, q2 = len(cfg['line1'].get('sublevels', [])), len(cfg['line2'].get('sublevels', []))
X = [[1] * len(g2) for _ in g1]
for i, a in enumerate(g1):
    for j, b in enumerate(g2):
        if i < q1 and j < q2: continue
        if any(a >= fa and b >= fb for fa, fb in falses): X[i][j] = 0
cfg['cross'] = X; cfg['cross_sources'] = sys.argv[3:]
json.dump(cfg, open(out, 'w'), indent=1)
print('line-1 grid', g1); print('line-2 grid', g2)
for i, a in enumerate(g1): print(a, X[i])
