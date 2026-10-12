#!/usr/bin/env python3
"""Parameter region of a hypothetical r = 0, n = 8 route of length <= 46186 (sec. 6).
Exact identity (Round I):  L = CONST + E + (tau - 1) + lam,  E = q - ORB >= 0, tau = #trails >= 1,
lam = sum_{inter-trail joins} (c - 4) >= 0;  equivalently  L = f(8) - (sum_T s_T - lam),
s_T = |T|/6 - (k_T + 1)  (saving of trail T relative to phi-cycles).
Proven constraints used:
  (A) window automaton + Lemma R (Round I, exact-verified):  sum_T (k_T + 1) >= 3/20 * HEX  ->  E + tau >= 36
  (R) Lemma R counting:  E >= (120 - tau)/8
  (S) per trail (A applied to one trail):  s_T <= |T| (1/6 - 3/20) = |T|/60
Outputs the region and the implied minimum amount of classes in 'efficient' trails."""
import json, math
CONST = 46085; f8 = 46204; HEX = 5040
region = []
for tau in range(1, 103):
    for E in range(0, 102):
        if E + tau < 36: continue
        if 8 * E < 120 - tau: continue
        lam_max = 101 - E - (tau - 1)
        if lam_max < 0: continue
        region.append((E, tau, lam_max))
n_tuples = sum(l + 1 for _, _, l in region)
# required saving: sum s_T >= 18 + lam ; each efficient trail saves at most |T|/60
min_classes = 60 * 18
out = dict(tuples_E_tau=len(region), tuples_E_tau_lam=n_tuples,
           E_range=(min(e for e, _, _ in region), max(e for e, _, _ in region)),
           tau_range=(min(t for _, t, _ in region), max(t for _, t, _ in region)),
           required_total_saving="sum_T s_T >= 18 + lam",
           min_classes_in_trails_with_positive_saving=min_classes,
           note="any length-<=46186 r=0 route needs trails beating phi-cycles on >= 1080 classes (>= 21% of all classes)")
print(json.dumps(out, indent=1))
json.dump(out, open(__file__.replace("src/r0_region.py", "certs/r0_region.json"), "w"), indent=1)
