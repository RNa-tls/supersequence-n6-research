#!/usr/bin/env python3
"""Round L -- cross-check of the mixed phi-set table: the MIP minima (phi_mixed_min.py) against the
exhaustive Algorithm X enumeration of all partitions with 7 E_P <= 14 (phi_configs.py 14).
For every k (number of world-b classes): if the MIP minimum is <= 2 the enumeration must attain it and
nothing lower; if it is 3 the enumeration must contain no partition with that k."""
import json, os
from fractions import Fraction
here = os.path.dirname(os.path.abspath(__file__))
mip = json.load(open(os.path.join(here, "..", "certs", "phi_mixed_min.json")))["min_E_by_worldb_classes"]
cf = json.load(open(os.path.join(here, "..", "certs", "phi_configs_14.json")))
best = {}
for s in cf["shapes"]:
    k = 42 - s["worldA_classes"]; best[k] = min(best.get(k, 99), s["sevenE"])
ok = all((best.get(k) == 7 * Fraction(mip[str(k)])) if Fraction(mip[str(k)]) <= 2 else (k not in best) for k in range(43))
print(json.dumps(dict(crosscheck_ok=ok, k_checked=43)))
