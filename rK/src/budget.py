#!/usr/bin/env python3
"""Round K, sec. 1 -- exact budget of a hypothetical r = 0 route with L <= 46186 (n = 8).
Identities (rJ/rI, Lean R0Identity):  L = CONST + E + (tau - 1) + lam,  E = q - ORB (extra chains),
tau = trails, lam = sum over inter-trail joins of (c - 4) >= 0;  equivalently L = 46204 - sum_T s_T + lam,
s_T = |T|/6 - (k_T + 1).  Certified trail-ratio bound (rK macro automaton, w = 3, checked by
macro_check.py):  k_T + 1 >= (5/33)|T|  for every trail, hence E + tau >= ceil(5040*5/33) - 720 = 44
and s_T <= |T|/66."""
import json
from fractions import Fraction
CONST, ORB, HEX = 46085, 720, 5040
beta = Fraction(5, 33)
need = 46186 - CONST                          # E + tau - 1 + lam <= 101
ET_min = -(-int(beta * HEX * 1000) // 1000)   # placeholder, recomputed exactly below
import math
ET_min = math.ceil(beta * HEX) - ORB          # E + tau >= 44
rows = []; total = 0
for s in range(ET_min, need + 2):             # s = E + tau
    for lam in range(0, need + 1 - (s - 1) + 1):
        if s - 1 + lam > need: break
        cnt = s                               # tau = 1..s, E = s - tau
        total += cnt
        rows.append(dict(E_plus_tau=s, lam=lam, length=CONST + s - 1 + lam, pairs=cnt,
                         min_classes_in_positive_trails=66 * (18 + lam)))
summary = dict(target="L <= 46186 (r = 0)", identity="E + (tau-1) + lam <= 101", trail_ratio=str(beta),
               E_plus_tau_min=ET_min, lam_max=need - (ET_min - 1), admissible_triples=total,
               saving_needed="sum_T s_T >= 18 + lam", s_T_max="|T|/66",
               positive_trail_classes_min=66 * 18,
               remark="every admissible route needs >= 1188 classes (23.6%) in trails strictly more efficient than phi-cycles")
json.dump(dict(summary=summary, rows=rows), open("rK/certs/budget_r0_46186.json", "w"), indent=0)
print(json.dumps(summary, ensure_ascii=False))
