#!/usr/bin/env python3
"""Round Omega copy of rZ/src/counting_relaxation.py with ONE change: the row helper merges repeated variables
(the original passed rows with repeated indices to HiGHS, which rejects them; the dropped row was f_s <= 7 R_o - h_o).
Round Z -- the counting relaxation of a frontier cover (exact integer program, HiGHS).

Every inequality below is a proved global counting statement about a sigma^2-reduced Hamiltonian path of R rows
(sections C, D, E of ROUND_Z_REPORT.md); the program asks whether integers satisfying all of them exist for a frontier
cell, and if so returns one solution.  A feasible answer is NOT a cover; it shows only that these counts do not exclude
the cell.  Worlds are modelled as two (z = dominant, t = everything else) -- splitting t further only adds freedom.

Variables per world s in {z, t}:  F_s full rows, P_s[k] rows of k blocks (k = 1..6), M_s extra rows of split 2-cycles,
f_s foreign classes in the used s-2-cycles, S_s one-symbol segments, h_s holes;  global: L label changes (b/c/f seams),
Lb, Lc, Lf by type, n chains (= cell value), E_s e-seams (taken 0, which only helps the cover: e-seams cost a split).
Constraints:
  R_s = F_s + sum_k P_s[k],  h_s = sum_k (7 - k) P_s[k] = 7 M_s + f_s           (deficit decomposition, per world)
  R_z + R_t = R,  h_z + h_t = 7 (R - 720)                                       (coverage count)
  f_z <= N_t := 7 R_t - h_t,  f_t <= N_z                                         (foreign classes come from the other world)
  run lemma per world:  F_s <= 5 (P_s + S_s) + S6_s,  S6_s <= S_s               (runs <= 6; a 6-run needs a b/f entry)
  6-row lemma per world: P_s[6] <= M_s + 2 S_s                                   (Lemma Z1 with E = 0)
  splits: rows of split 2-cycles <= 2 M_s;  single partial rows carry only foreign holes:
          sum_k (7-k) (P_s[k] - Q_s[k]) <= f_s,  Q_s[k] <= P_s[k],  sum_k Q_s[k] <= 2 M_s
  segments: S_z + S_t = n + L,  each world has at least one segment if it has rows
  b-seams: every b-seam enters a class of the previous row's 2-cycle: Lb <= f_z + f_t;  L = Lb + Lc + Lf
  lines with symbol-change price (proved by search): 4R - 9 Delta + LAM1 L <= 56 n + 5 F,
                                                    17R - 38 Delta + LAM2 L <= C2 n + 6 F   (free junction gammas)
  one-symbol exclusion (Y8) is implied: L = 0 and n = 1 force one world.
usage: counting_relaxation.py R p F [LAM1 LAM2 C2] [objective: minL|maxL|feas]"""
import sys, json
import highspy
R, p, F = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
LAM1 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
LAM2 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
C2 = int(sys.argv[6]) if len(sys.argv) > 6 else 264
obj = sys.argv[7] if len(sys.argv) > 7 else 'minL'
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
row(Rs('z') + Rs('t'), R, R)
row(hs('z') + hs('t'), Delta, Delta)
for s, o in (('z', 't'), ('t', 'z')):                                          # f_s <= 7 R_o - h_o
    row([(V['f', s], 1)] + [(c, -7 * a) for c, a in Rs(o)] + [(c, a) for c, a in hs(o)], -inf, 0)
row([(V['S', 'z'], 1), (V['S', 't'], 1), (V['L'], -1)], n, n)
row([(V['S', 'z'], 1)], 1, inf)
row([(V['L'], 1), (V['Lb'], -1), (V['Lc'], -1), (V['Lf'], -1)], 0, 0)
row([(V['Lb'], 1), (V['f', 'z'], -1), (V['f', 't'], -1)], -inf, 0)
# rows of world t exist iff it has a segment (big-M with R)
row(Rs('t') + [(V['S', 't'], -R)], -inf, 0)
# Y8: one world only if ... (with S_t = 0 the t-world is empty and f_z must be 0)
row([(V['f', 'z'], 1), (V['S', 't'], -7 * R)], -inf, 0)
# lines with the symbol-change price
row([(V['L'], LAM1)], -inf, 56 * n - (4 * R - 9 * Delta))
row([(V['L'], LAM2)], -inf, C2 * n - (17 * R - 38 * Delta))
cost = [0.0] * len(names)
if obj == 'minL': cost[V['L']] = 1.0
elif obj == 'maxL': cost[V['L']] = -1.0
h.changeColsCost(len(names), list(range(len(names))), cost)
h.run()
st = h.modelStatusToString(h.getModelStatus())
out = dict(cell=[R, p, F], n=n, Delta=Delta, lam1=LAM1, lam2=LAM2, c2=C2, objective=obj, status=st)
if st == 'Optimal':
    x = h.getSolution().col_value
    out['solution'] = {names[i]: int(round(x[i])) for i in range(len(names)) if abs(x[i]) > 1e-9}
print(json.dumps(out))
