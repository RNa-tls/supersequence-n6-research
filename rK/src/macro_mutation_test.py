#!/usr/bin/env python3
"""Mutation tests for macro_check.py: each tampered certificate must be rejected."""
import json, sys, os, subprocess, tempfile, copy
cert = sys.argv[1]; PY = sys.executable
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macro_check.py")
C = json.load(open(cert))
def run(c):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(c, f); p = f.name
    r = subprocess.run([PY, "-I", CK, p], capture_output=True, text=True); os.unlink(p); return r.returncode == 0
from fractions import Fraction
res = {"original_accepted": run(C)}
b = Fraction(C["beta_verified"])
c = copy.deepcopy(C); c["beta_verified"] = str(b + Fraction(1, 10000)); res["larger_beta_rejected"] = not run(c)
c = copy.deepcopy(C); i = max(range(len(c["potentials"])), key=lambda k: c["potentials"][k]); c["potentials"][i] += 10**6; res["raised_potential_rejected"] = not run(c)
c = copy.deepcopy(C); c["potentials"][0] = -1; res["root_potential_rejected"] = not run(c)
c = copy.deepcopy(C); c["states_list"] = c["states_list"][:-1]; c["potentials"] = c["potentials"][:-1]; res["dropped_state_rejected"] = not run(c)
c = copy.deepcopy(C); c["states_list"][1], c["states_list"][2] = c["states_list"][2], c["states_list"][1]; res["swapped_states_rejected"] = not run(c)
c = copy.deepcopy(C); c["w"] = C["w"] - 1; res["wrong_window_rejected"] = not run(c)
print(json.dumps(res)); assert all(res.values())
