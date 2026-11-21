#!/usr/bin/env python3
"""Round Omega -- the counting relaxation of Round Z (rZ/src/counting_relaxation.py) with SEGMENT-LEVEL line caps.

Added proved constraints.  A one-symbol segment (maximal run of rows with one moving symbol inside a chain) is a
contiguous sub-chain, so every line bound applies to it, and two different segments are row-disjoint, so the packing
and coexistence statements apply across segments:
  * a segment of value v > 0 contains a forward-primitive part of value >= v (the suffix after its last non-positive
    prefix), so 'segment values' inherit every statement about row-disjoint primitive parts;
  * line 1: kappa1(45) <= 2, Compat1(49, 49) = false, Compat1(51, 45) = false (rOmega coexistence table);
    so among the segments: at most one has v1 >= 49; if one has v1 >= 51 all others have v1 <= 44; at most two have
    v1 >= 45.  Hence  sum over segments of v1 <= 44 S + 12   (S = number of segments; 56 + 44 (S - 1) is the largest
    pattern; 50 + 48 + 44 (S - 2) is smaller).  Per world: V1_s <= 44 S_s + 12 (one world may hold the large one;
    the per-world form is implied by the global one only up to the +12, so we impose the global one and per world
    V1_s <= 44 S_s + 12).
  * line 2: kappa2(200) <= 2, Compat2(222, 219) = false, Compat2(231, 200) = false: at most one segment >= 222; if one
    is >= 231 all others are <= 199; a segment in [222, 230] allows one other in [200, 218].  The largest pattern is
    264 + 199 (S - 1) (versus 230 + 218 + 199 (S - 2) and 221 + 221 + 199 (S - 2)), so sum v2 <= 199 S + 65.
  Value of world s: V1_s = 4 R_s - 9 h_s, V2_s = 17 R_s - 38 h_s (h_s = holes of the rows of world s).
Everything else is Round Z's model (two worlds z, t).  A feasible answer is NOT a cover.
usage: counting_relaxation2.py R p F [LAM1] [objective minL|maxL|feas] [nocaps]"""
import sys, json
import highspy
R, p, F = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
LAM1 = int(sys.argv[4]) if len(sys.argv) > 4 else 4
obj = sys.argv[5] if len(sys.argv) > 5 else 'minL'
caps = not (len(sys.argv) > 6 and sys.argv[6] == 'nocaps')
n = 1 + p + F
Delta = 7 * (R - 720)
h = highspy.Highs(); h.setOptionValue('output_flag', False)
inf = highspy.kHighsInf
names = []
def var(name, lo=0, hi=inf):
    names.append(name); h.addVar(lo, hi); h.changeColIntegrality(len(names) - 1, highspy.HighsVarType.kInteger); return len(names) - 1
def row(coeffs, lo, hi):
    # merge repeated variables (HiGHS rejects a row with a repeated index and does NOT add it)
    acc = {}
    for c, a in coeffs: acc[c] = acc.get(c, 0) + a
    idx = sorted(i for i in acc if acc[i] != 0); val = [float(acc[i]) for i in idx]
    st = h.addRow(lo, hi, len(idx), idx, val)
    assert st == highspy.HighsStatus.kOk, 'row rejected'
W = ['z', 't']
V = {}
for s in W:
    V['F', s] = var('F_' + s); V['M', s] = var('M_' + s); V['f', s] = var('f_' + s); V['S', s] = var('S_' + s); V['S6', s] = var('S6_' + s)
    for k in range(1, 7):
        V['P', s, k] = var('P%d_%s' % (k, s)); V['Q', s, k] = var('Q%d_%s' % (k, s))
V['L'] = var('L'); V['Lb'] = var('Lb'); V['Lc'] = var('Lc'); V['Lf'] = var('Lf')
def Rs(s): return [(V['F', s], 1)] + [(V['P', s, k], 1) for k in range(1, 7)]
def hs(s): return [(V['P', s, k], 7 - k) for k in range(1, 7)]
for s in W:
    row(hs(s) + [(V['M', s], -7), (V['f', s], -1)], 0, 0)                    # h_s = 7 M_s + f_s
    row([(V['F', s], 1)] + [(V['P', s, k], -5) for k in range(1, 7)] + [(V['S', s], -5), (V['S6', s], -1)], -inf, 0)
    row([(V['S6', s], 1), (V['S', s], -1)], -inf, 0)
    row([(V['P', s, 6], 1), (V['M', s], -1), (V['S', s], -2)], -inf, 0)       # 6-row lemma
    for k in range(1, 7): row([(V['Q', s, k], 1), (V['P', s, k], -1)], -inf, 0)
    row([(V['Q', s, k], 1) for k in range(1, 7)] + [(V['M', s], -2)], -inf, 0)
    row([(V['P', s, k], 7 - k) for k in range(1, 7)] + [(V['Q', s, k], -(7 - k)) for k in range(1, 7)] + [(V['f', s], -1)], -inf, 0)
    if caps:
        # V1_s = 4 R_s - 9 h_s <= 44 S_s + 12 ;  V2_s = 17 R_s - 38 h_s <= 199 S_s + 65
        row([(c, 4 * a) for c, a in Rs(s)] + [(c, -9 * a) for c, a in hs(s)] + [(V['S', s], -44)], -inf, 12)
        row([(c, 17 * a) for c, a in Rs(s)] + [(c, -38 * a) for c, a in hs(s)] + [(V['S', s], -199)], -inf, 65)
row(Rs('z') + Rs('t'), R, R)
row(hs('z') + hs('t'), Delta, Delta)
for s, o in (('z', 't'), ('t', 'z')):                                          # f_s <= 7 R_o - h_o
    row([(V['f', s], 1)] + [(c, -7 * a) for c, a in Rs(o)] + [(c, a) for c, a in hs(o)], -inf, 0)
row([(V['S', 'z'], 1), (V['S', 't'], 1), (V['L'], -1)], n, n)
row([(V['S', 'z'], 1)], 1, inf)
row([(V['L'], 1), (V['Lb'], -1), (V['Lc'], -1), (V['Lf'], -1)], 0, 0)
row([(V['Lb'], 1), (V['f', 'z'], -1), (V['f', 't'], -1)], -inf, 0)
row(Rs('t') + [(V['S', 't'], -R)], -inf, 0)
row([(V['f', 'z'], 1), (V['S', 't'], -7 * R)], -inf, 0)
if caps:                                                                       # global segment caps
    row([(c, 4 * a) for s in W for c, a in Rs(s)] + [(c, -9 * a) for s in W for c, a in hs(s)] + [(V['S', s], -44) for s in W], -inf, 12)
    row([(c, 17 * a) for s in W for c, a in Rs(s)] + [(c, -38 * a) for s in W for c, a in hs(s)] + [(V['S', s], -199) for s in W], -inf, 65)
row([(V['L'], LAM1)], -inf, 56 * n - (4 * R - 9 * Delta))
cost = [0.0] * len(names)
if obj == 'minL': cost[V['L']] = 1.0
elif obj == 'maxL': cost[V['L']] = -1.0
h.changeColsCost(len(names), list(range(len(names))), cost)
h.run()
st = h.modelStatusToString(h.getModelStatus())
out = dict(cell=[R, p, F], n=n, Delta=Delta, lam1=LAM1, caps=caps, objective=obj, status=st)
if st == 'Optimal':
    x = h.getSolution().col_value
    out['solution'] = {names[i]: int(round(x[i])) for i in range(len(names)) if abs(x[i]) > 1e-9}
    sol = out['solution']
    for s in W:
        Rv = sol.get('F_' + s, 0) + sum(sol.get('P%d_%s' % (k, s), 0) for k in range(1, 7)); hv = sum((7 - k) * sol.get('P%d_%s' % (k, s), 0) for k in range(1, 7))
        out['V1_' + s] = 4 * Rv - 9 * hv; out['V2_' + s] = 17 * Rv - 38 * hv; out['R_' + s] = Rv; out['h_' + s] = hv
print(json.dumps(out))
