#!/usr/bin/env python3
"""Round Omega -- the 46135 frontier knapsack with LEVELLED packing types and a two-threshold coexistence table.
(Version 2: optional sub-threshold levels for nu = 0 chains; see the state description below.)

For each line (1: 4r - 9d <= 56, 2: 17r - 38d <= 264) fix a packing threshold LO (kappa(LO) <= 2 proved) and a grid of
levels g_0 = LO < g_1 < ... < g_k.  A primitive part (forward- or backward-primitive sub-chain of the Hamiltonian path)
of value >= LO is "high"; its level is the largest i with value >= g_i.  Proved facts used:
  (K) kappa(LO) <= 2: at most two pairwise row-disjoint high parts in the whole path;
  (C) Compat(i, j) = false  ==>  there are no two row-disjoint high parts of levels >= i and >= j
      (rOmega/src/compat2d.py, exact, from the complete FP(LO) placement list).
Chain kinds (per line), each with its two-sided table (Round X lemma X1 on census points truncated as stated):
  Z      nu = 0: no high part                    census < LO
  S[i]   nu = 1, highest part at level i         census < g_{i+1} (full for the top level), Case B with both ends >= LO excluded
  D[i]   nu = 2, highest part at level i         census < g_{i+1}, Case B ends restricted to compatible level pairs
(nu = largest number of pairwise row-disjoint high parts inside the chain.)  Two different chains are row-disjoint, so
two S chains of levels i, j need Compat(i, j); a D chain excludes every other chain with a high part (K).
Line state: none / one S chain at level i / full.  Chain type = (kind on line 1, kind on line 2), deficit table as in
rX/src/frontier_packing.py (both lines, and the census rule v1 >= 54 and v2 >= 258 => v1 = 56).  Junction refinement
(free-junction loops and pairs, shared rows) exactly as in rX/src/frontier_packing.py.
usage: frontier_compat.py CONFIG.json OUT.json      (config: see make_compat_config.py)"""
import sys, json, hashlib
import numpy as np
INF = 10 ** 9
def feas(path):
    F = {}
    for l in open(path):
        if l.startswith('#'): continue
        t = l.split(); F[int(t[0])] = {int(x.split(':')[0]) for x in t[1:]}
    return F
def main():
    cfg = json.load(open(sys.argv[1])); outp = sys.argv[2]
    RMAX = cfg.get('rmax', 800); NMAX = cfg.get('nmax', 14)
    lines = []
    for key in ('line1', 'line2'):
        L = cfg[key]; nlev = len(L['levels'])
        comp = [[bool(x) for x in row] for row in L['compat']]
        for i in range(nlev):
            for j in range(nlev):
                assert comp[i][j] == comp[j][i]
                if i + 1 < nlev: assert comp[i][j] >= comp[i + 1][j]          # monotone in the thresholds
        kinds = []
        for k in L['kinds']:
            kinds.append(dict(name=k['name'], nu=k['nu'], level=k.get('level'), F=feas(k['table']), table=k['table']))
        ent = dict(nlev=nlev, comp=comp, kinds=kinds, levels=L['levels'])
        if 'sublevels' in L:
            ent['sublevels'] = L['sublevels']; ent['compat_ext'] = L['compat_ext']
            q = len(L['sublevels']); M = L['compat_ext']
            for i in range(q, q + nlev):               # the joint matrix agrees with the level matrix and is monotone
                for j in range(q, q + nlev): assert bool(M[i][j]) == comp[i - q][j - q]
            for i in range(q + nlev):
                for j in range(q + nlev):
                    assert M[i][j] == M[j][i]
                    if i + 1 < q + nlev and i >= q - 1: assert M[i][j] >= M[i + 1][j]
        lines.append(ent)
    # Each line has the levels L['levels'] = [g_0 = LO < ... < g_k] (kinds S, D) and optional sub-levels
    # L['sublevels'] = [z_1 < ... < z_q < LO] (kinds Z with 'level' = index into sublevels; Z without level = bottom).
    # Compat is given on the joint grid sublevels + levels (matrix 'compat_ext' of size q + k + 1); pairs of two
    # sub-levels are never tested.  State per line: (nu, h, l): nu = sum of nu so far, h = highest S/D level so far
    # (-1 none), l = highest sub-level of a nu = 0 chain so far (-1 bottom).  All pairs of distinct chains must be
    # compatible; by monotonicity it suffices to test each new chain against h and l (the two maxima).
    for L in lines:
        q = len(L.get('sublevels', [])); L['q'] = q
        if 'compat_ext' in L: L['C'] = [[bool(x) for x in row] for row in L['compat_ext']]
        else:
            assert q == 0; L['C'] = L['comp']
    def C(L, a, b):                 # a, b indices on the joint grid (sub-levels first)
        return L['C'][a][b]
    def trans(li, s, kind):
        L = lines[li]; q = L['q']; nu, h, l = s
        if kind['nu'] == 0:
            lv = kind.get('level'); lv = -1 if lv is None else lv
            if lv >= 0 and h >= 0 and not C(L, q + h, lv): return None
            return (nu, h, max(l, lv))
        i = kind['level']
        if l >= 0 and not C(L, q + i, l): return None
        if kind['nu'] == 2:
            return (2, i, l) if nu == 0 else None
        if nu == 0: return (1, i, l)
        if nu == 2: return None
        if not C(L, q + h, q + i): return None
        return (2, max(h, i), l)
    def dtab(F1, F2):
        dm = np.full(RMAX + 1, INF, dtype=np.int64)
        for r in range(1, RMAX + 1):
            d = 0
            while d <= 7 * r:
                v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
                if (v1 <= 0 or v1 in F1.get(r, ())) and (v2 <= 0 or v2 in F2.get(r, ())) and not (v1 >= 54 and v2 >= 258 and v1 != 56): break
                d += 1
            dm[r] = d
        return dm
    K1, K2 = lines[0]['kinds'], lines[1]['kinds']
    base = {}
    for a, k1 in enumerate(K1):
        for b, k2 in enumerate(K2):
            base[(a, b)] = dtab(k1['F'], k2['F'])
    def states(L): return [(nu, h, l) for nu in range(3) for h in range(-1, L['nlev']) for l in range(-1, L['q'])]
    S1 = states(lines[0]); S2 = states(lines[1])
    # grouped transitions: for each (s1, s2) the target (t1, t2) and the pointwise least table over the kinds
    # optional cross-line coexistence: X12[i][j] for the joint grid index i of line 1 and j of line 2 (sub-levels
    # first): a line-1 part of level i and a line-2 part of level j in DIFFERENT chains must have X12 true.  Both
    # maxima of the earlier chains are kept in the states, and X12 is antitone in both arguments (checked), so it
    # suffices to test the new chain against them.
    X12 = cfg.get('cross')
    if X12 is not None:
        n1 = lines[0]['q'] + lines[0]['nlev']; n2 = lines[1]['q'] + lines[1]['nlev']
        assert len(X12) == n1 and all(len(r) == n2 for r in X12)
        for i in range(n1):
            for j in range(n2):
                if i + 1 < n1: assert X12[i][j] >= X12[i + 1][j]
                if j + 1 < n2: assert X12[i][j] >= X12[i][j + 1]
    def jlev(li, kind):              # joint-grid index of a kind's level (-1 = bottom)
        L = lines[li]
        if kind['nu'] == 0: return -1 if kind.get('level') is None else kind['level']
        return L['q'] + kind['level']
    def smax(li, s):                 # joint-grid index of the largest level of the earlier chains on line li
        L = lines[li]; nu, h, l = s
        return L['q'] + h if h >= 0 else l
    def cross_ok(s1, s2, k1, k2):
        if X12 is None: return True
        a = jlev(0, k1); b = jlev(1, k2); m1 = smax(0, s1); m2 = smax(1, s2)
        if a >= 0 and m2 >= 0 and not X12[a][m2]: return False
        if b >= 0 and m1 >= 0 and not X12[m1][b]: return False
        return True
    groups = {}
    for s1 in S1:
        for s2 in S2:
            g = {}
            for a, k1 in enumerate(K1):
                t1 = trans(0, s1, k1)
                if t1 is None: continue
                for b, k2 in enumerate(K2):
                    t2 = trans(1, s2, k2)
                    if t2 is None: continue
                    if not cross_ok(s1, s2, k1, k2): continue
                    g.setdefault((t1, t2), []).append((a, b))
            groups[(s1, s2)] = g
    toe_cache = {}
    def toeplitz(key, arr):
        if key not in toe_cache:
            T = np.full((RMAX + 1, RMAX + 1), INF, dtype=np.int64)
            for s in range(RMAX + 1): T[s, s:] = arr[:RMAX + 1 - s]
            T[:, :] = np.where(T >= INF, INF, T); toe_cache[key] = T
        return toe_cache[key]
    gmin = {}
    for s, g in groups.items():
        for t, lst in g.items():
            key = tuple(sorted(lst))
            if key not in gmin:
                arr = np.minimum.reduce([base[x] for x in lst]); arr = arr.copy(); arr[0] = INF
                gmin[key] = arr
    def conv(f, key):
        idx = np.nonzero(f < INF)[0]
        if len(idx) == 0: return None
        T = toeplitz(key, gmin[key])
        M = f[idx][:, None] + T[idx, :]
        return np.minimum(M.min(axis=0), INF)
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    P = [{((0, -1, -1), (0, -1, -1)): unit}]
    for m in range(1, NMAX + 1):
        cur = {}
        for s, arr in P[-1].items():
            for t, lst in groups[s].items():
                h = conv(arr, tuple(sorted(lst)))
                if h is None: continue
                cur[t] = h if t not in cur else np.minimum(cur[t], h)
        P.append(cur)
    best = []
    for m in range(NMAX + 1):
        arrs = list(P[m].values()); best.append(np.minimum.reduce(arrs) if arrs else np.full(RMAX + 1, INF, dtype=np.int64))
    def at(m, x):
        if m < 0 or x < 0 or m > NMAX or x > RMAX: return INF
        return int(best[m][x])
    def decompose(m, x):            # one optimal chain list for best[m][x]
        val = at(m, x); assert val < INF
        st = [s for s in P[m] if int(P[m][s][x]) == val][0]
        out = []
        while m > 0:
            target = int(P[m][st][x]); done = False
            for s, arr in P[m - 1].items():
                lst = groups[s].get(st)
                if not lst: continue
                g = gmin[tuple(sorted(lst))]
                rr = np.arange(1, x + 1); prev = arr[x - rr]; tot = prev + g[rr]
                hit = np.nonzero((prev < INF) & (g[rr] < INF) & (tot == target))[0]
                if len(hit) == 0: continue
                r = int(rr[hit[0]]); d = int(g[r])
                ab = [ab for ab in lst if int(base[ab][r]) == d][0]
                out.append(dict(r=r, d=d, v1=4 * r - 9 * d, v2=17 * r - 38 * d, line1_kind=K1[ab[0]]['name'], line2_kind=K2[ab[1]]['name']))
                m, x, st = m - 1, x - r, s; done = True; break
            assert done
        return out
    W = json.load(open(cfg['cells']))
    only = None
    if cfg.get('only'):
        prev = json.load(open(cfg['only'])); only = {(r['R'], r['p'], r['F']) for r in prev['rows'] if not r['excluded']}
    rows = []
    for cl in W['rows']:
        R, n, D, F = cl['R'], cl['chains'], cl['Delta'], cl['F']
        if only is not None and (R, cl['p'], F) not in only: continue
        assert n <= NMAX, 'NMAX too small for this cell'
        lb = INF; arg = None
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                cand = [(at(m, pieces), m) for m in range(0, n - Fi - sh + 1)]
                bm, mm = min(cand)
                if bm >= INF: continue
                v = bm + Fi + 8 * Fii - 6 * sh
                if v < lb: lb = v; arg = dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh, chains_used=mm, pieces=pieces)
        row = dict(R=R, p=cl['p'], F=F, chains=n, Delta=D, min_deficit=int(lb), excluded=bool(lb > D), margin=int(lb - D), junction_argmin=arg)
        if not row['excluded'] and arg is not None:
            row['decomposition'] = decompose(arg['chains_used'], arg['pieces'])
            assert sum(c['r'] for c in row['decomposition']) == arg['pieces']
            assert sum(c['d'] for c in row['decomposition']) + arg['F_loops'] + 8 * arg['F_pairs'] - 6 * arg['shared_rows'] == lb
        rows.append(row)
    surv = [r for r in rows if not r['excluded']]
    res = dict(config=cfg, cells=len(rows), excluded=len(rows) - len(surv), survivors=len(surv), rows=rows)
    s = json.dumps(res, indent=1); open(outp, 'w').write(s)
    print(json.dumps({k: v for k, v in res.items() if k not in ('rows', 'config')}))
    print('survivors:', [(r['R'], r['p'], r['F'], r['margin']) for r in surv])
    print('sha256', hashlib.sha256(s.encode()).hexdigest())
main()
