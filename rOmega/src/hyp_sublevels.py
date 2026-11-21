#!/usr/bin/env python3
"""Round Omega -- add sub-threshold levels to a frontier_compat configuration.

Given a configuration made by make_compat_config.py and, per line, a list of sub-levels z_1 < ... < z_q < LO with the
Z tables <prefix>_lt<z>.txt, this writes a configuration whose joint-grid compat matrix uses
  (high, high): the original table;  (sub, sub): true (never tested);
  (high g_i, sub z_a): given by a rule: either a coexistence table file (proved values) or a HYPOTHESIS
  'cut:G:Z' meaning 'levels >= G are incompatible with sub-levels >= Z' (several cuts allowed).
Z kinds: Z[bottom] = census < z_1, Z[z_a] = census < z_{a+1} (z_{q+1} = LO).
usage: hyp_sublevels.py IN.json OUT.json LINE(1|2) TABDIR PREFIX sub1,sub2,.. RULE [RULE ...]
   RULE = cut:G:Z  (hypothesis)  |  table:COMPAT.json (proved entries 'g,z' looked up; missing => error)"""
import sys, json
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]; key = 'line%s' % sys.argv[3]; tdir = sys.argv[4]; prefix = sys.argv[5]
subs = [int(x) for x in sys.argv[6].split(',')]; rules = sys.argv[7:]
L = cfg[key]; G = L['levels']; q = len(subs); n = len(G)
tables = [json.load(open(r.split(':', 1)[1]))['table'] for r in rules if r.startswith('table:')]
cuts = [tuple(map(int, r.split(':')[1:])) for r in rules if r.startswith('cut:')]
def comp_high_sub(g, z):
    # monotonicity: if g is compatible with LO (a level pair already in the proved level matrix), it is compatible
    # with every sub-level z < LO
    gi = G.index(g)
    if L['compat'][gi][0]: return True
    for T in tables:
        k = '%d,%d' % (g, z)
        if k in T: return bool(T[k]['compatible'])
    if cuts: return not any(g >= cg and z >= cz for cg, cz in cuts)
    raise SystemExit('no value for (%d, %d)' % (g, z))
joint = subs + G
M = [[True] * (q + n) for _ in range(q + n)]
for i in range(q + n):
    for j in range(q + n):
        if i >= q and j >= q: M[i][j] = bool(L['compat'][i - q][j - q])
        elif i >= q and j < q: M[i][j] = comp_high_sub(joint[i], joint[j])
        elif i < q and j >= q: M[i][j] = comp_high_sub(joint[j], joint[i])
L['sublevels'] = subs; L['compat_ext'] = [[int(x) for x in row] for row in M]
kinds = [k for k in L['kinds'] if k['nu'] != 0]
z = [dict(name='Z', nu=0, table='%s/%s_lt%d.txt' % (tdir, prefix, subs[0]))]
for a in range(q):
    nxt = subs[a + 1] if a + 1 < q else G[0]
    z.append(dict(name='Z%d' % subs[a], nu=0, level=a, table='%s/%s_lt%d.txt' % (tdir, prefix, nxt)))
L['kinds'] = z + kinds; L['rules'] = rules
json.dump(cfg, open(out, 'w'), indent=1)
print(key, 'sublevels', subs, 'rules', rules)
