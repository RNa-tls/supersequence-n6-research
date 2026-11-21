#!/usr/bin/env python3
"""Round Omega -- SECOND implementation of rOmega/src/frontier_compat.py (written separately, different algorithm).

Instead of a dynamic programme over resource states, the high parts are enumerated explicitly.
  * Per line, the multiset H of high chains is one of: empty; {S_i}; {S_i, S_j} with Compat(i, j); {D_i}.
  * A "special" chain carries a high item on line 1, on line 2, or on both; the items of H1 and H2 are matched into
    special chains in every possible way (partial matchings).  A special chain with an item on one line only takes on
    the other line the best Z kind whose sub-level is compatible with every high level of that line.
  * All remaining chains are Z/Z chains whose sub-levels are compatible with every high level on their line;
    their least total deficit for m chains and p pieces is the m-fold min-plus power of one table.
The least deficit for (m chains, p pieces) is the minimum over configurations of (special tables) * (Z/Z power).
Deficit tables are rebuilt here from the two-sided feasibility files (same rule as frontier_packing.py).
The junction refinement over (F_loops, F_pairs, shared rows) is applied as in frontier_packing.py.
usage: frontier_compat_enum.py CONFIG.json FIRST_IMPLEMENTATION_OUT.json OUT.json"""
import sys, json, itertools, hashlib
import numpy as np
INF = 10 ** 9
cfg = json.load(open(sys.argv[1])); first = json.load(open(sys.argv[2])); outp = sys.argv[3]
RMAX = cfg.get('rmax', 800)
def readfeas(path):
    F = {}
    with open(path) as fh:
        for l in fh:
            if l[0] == '#': continue
            t = l.split(); F[int(t[0])] = frozenset(int(x.split(':')[0]) for x in t[1:])
    return F
lines = []
for key in ('line1', 'line2'):
    L = cfg[key]; q = len(L.get('sublevels', [])); K = len(L['levels'])
    M = L['compat_ext'] if q else L['compat']
    kinds = [dict(k, F=readfeas(k['table'])) for k in L['kinds']]
    lines.append(dict(q=q, K=K, M=[[bool(x) for x in r] for r in M], kinds=kinds))
def deficits(F1, F2):
    out = np.full(RMAX + 1, INF, dtype=np.int64)
    for r in range(1, RMAX + 1):
        f1, f2 = F1.get(r, frozenset()), F2.get(r, frozenset())
        for d in range(0, 7 * r + 1):
            v1 = 4 * r - 9 * d; v2 = 17 * r - 38 * d
            ok1 = v1 <= 0 or v1 in f1; ok2 = v2 <= 0 or v2 in f2
            if ok1 and ok2 and not (v1 >= 54 and v2 >= 258 and v1 != 56): out[r] = d; break
    return out
cacheD = {}
def D(a, b):
    if (a, b) not in cacheD: cacheD[(a, b)] = deficits(lines[0]['kinds'][a]['F'], lines[1]['kinds'][b]['F'])
    return cacheD[(a, b)]
def minplus(f, g, cap):
    h = np.full(cap + 1, INF, dtype=np.int64)
    fi = np.nonzero(f[:cap + 1] < INF)[0]
    for s in fi:
        seg = f[s] + g[:cap + 1 - s]; h[s:] = np.minimum(h[s:], seg)
    return np.minimum(h, INF)
def joint(L, kind):         # index of the kind's level on the joint grid (None = bottom)
    if kind['nu'] == 0: return None if kind.get('level') is None else kind['level']
    return L['q'] + kind['level']
def ok(L, a, b):
    if a is None or b is None: return True
    return L['M'][a][b]
# per line: the possible high multisets (as lists of kind indices)
def high_sets(L):
    S = [i for i, k in enumerate(L['kinds']) if k['nu'] == 1]; Dk = [i for i, k in enumerate(L['kinds']) if k['nu'] == 2]
    out = [()]
    out += [(i,) for i in S]
    for a, b in itertools.combinations_with_replacement(S, 2):
        if ok(L, joint(L, L['kinds'][a]), joint(L, L['kinds'][b])): out.append((a, b))
    out += [(i,) for i in Dk]
    return out
X12 = cfg.get('cross')               # optional cross-line table on the joint grids (line-1 index, line-2 index)
if X12 is not None:
    q1, q2 = lines[0]['q'], lines[1]['q']
    for i in range(q1):
        for j in range(q2): assert X12[i][j], 'sub-level/sub-level cross entries must be unused (true)'
def xok(a, b):                       # a: joint index on line 1 (None = bottom), b: joint index on line 2
    if X12 is None or a is None or b is None: return True
    return bool(X12[a][b])
def allowed_Z(L, H, other=(), li=0):
    # Z kinds of line li compatible with every high level of the same line (H) and, across lines, with every
    # high item of the other line carried by a DIFFERENT chain (other = joint levels of those items)
    lv = [joint(L, L['kinds'][i]) for i in H]
    out = []
    for i, k in enumerate(L['kinds']):
        if k['nu'] != 0: continue
        z = joint(L, k)
        if not all(ok(L, z, x) for x in lv): continue
        if li == 0 and not all(xok(z, y) for y in other): continue
        if li == 1 and not all(xok(y, z) for y in other): continue
        out.append(i)
    return out
NMAX = max(c['chains'] for c in first['rows'])
CAP = max(c['R'] for c in first['rows'])
H1s, H2s = high_sets(lines[0]), high_sets(lines[1])
zpow_cache = {}
def zpow(Z1, Z2):
    key = (tuple(Z1), tuple(Z2))
    if key not in zpow_cache:
        base = np.minimum.reduce([D(a, b) for a in Z1 for b in Z2]).copy(); base[0] = INF
        P = [np.full(CAP + 1, INF, dtype=np.int64)]; P[0][0] = 0
        for m in range(1, NMAX + 1): P.append(minplus(P[-1], base, CAP))
        zpow_cache[key] = P
    return zpow_cache[key]
best = [np.full(CAP + 1, INF, dtype=np.int64) for _ in range(NMAX + 1)]
nconf = 0
for H1 in H1s:
    J1 = [joint(lines[0], lines[0]['kinds'][i]) for i in H1]
    for H2 in H2s:
        J2 = [joint(lines[1], lines[1]['kinds'][i]) for i in H2]
        Z1 = allowed_Z(lines[0], H1, J2, 0); Z2 = allowed_Z(lines[1], H2, J1, 1)     # kinds of the Z/Z chains
        if not Z1 or not Z2: continue
        P = zpow(Z1, Z2)
        # matchings between the items of H1 and H2
        items1, items2 = list(range(len(H1))), list(range(len(H2)))
        for k in range(0, min(len(H1), len(H2)) + 1):
            for A in itertools.combinations(items1, k):
                for B in itertools.permutations(items2, k):
                    same = set(zip(A, B))
                    # cross pairs carried by different chains must be compatible
                    if not all(xok(J1[x], J2[y]) for x in items1 for y in items2 if (x, y) not in same): continue
                    chains = []; bad = False
                    for x, y in zip(A, B): chains.append(D(H1[x], H2[y]))
                    for x in items1:
                        if x not in A:
                            Zo = allowed_Z(lines[1], H2, [J1[u] for u in items1 if u != x], 1)
                            if not Zo: bad = True; break
                            chains.append(np.minimum.reduce([D(H1[x], b) for b in Zo]))
                    for y in items2:
                        if bad: break
                        if y not in B:
                            Zo = allowed_Z(lines[0], H1, [J2[u] for u in items2 if u != y], 0)
                            if not Zo: bad = True; break
                            chains.append(np.minimum.reduce([D(a, H2[y]) for a in Zo]))
                    if bad: continue
                    nconf += 1
                    acc = np.full(CAP + 1, INF, dtype=np.int64); acc[0] = 0
                    for t in chains:
                        t2 = t.copy(); t2[0] = INF; acc = minplus(acc, t2, CAP)
                    ns = len(chains)
                    for m in range(ns, NMAX + 1):
                        best[m] = np.minimum(best[m], minplus(acc, P[m - ns], CAP))
def at(m, x):
    if m < 0 or m > NMAX or x < 0 or x > CAP: return INF
    return int(best[m][x])
rows = []; mism = []
for c in first['rows']:
    R, n, F, Dl = c['R'], c['chains'], c['F'], c['Delta']; lb = INF
    for Fi in range(F + 1):
        Fii = F - Fi
        for sh in range(Fii + 1):
            if Fi + sh > n: continue
            pieces = R - Fi - (2 * Fii - sh)
            if pieces < 0: continue
            bm = min(at(m, pieces) for m in range(0, n - Fi - sh + 1))
            if bm >= INF: continue
            lb = min(lb, bm + Fi + 8 * Fii - 6 * sh)
    rows.append(dict(R=R, p=c['p'], F=F, min_deficit=int(lb), margin=int(lb - Dl), excluded=bool(lb > Dl)))
    if int(lb) != c['min_deficit']: mism.append((R, c['p'], F, int(lb), c['min_deficit']))
res = dict(configurations=nconf, cells=len(rows), survivors=sum(1 for r in rows if not r['excluded']), mismatches=mism, rows=rows)
s = json.dumps(res, indent=1); open(outp, 'w').write(s)
print(json.dumps({k: v for k, v in res.items() if k != 'rows'}))
print('sha256', hashlib.sha256(s.encode()).hexdigest())
