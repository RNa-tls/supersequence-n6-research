#!/usr/bin/env python3
"""Round N (section 15) -- mutation tests for the CC-LP certificate checkers.
 C1  inflate the dual of the s row by +1 (a fake certificate claiming a bound 1 higher): the checker's
     group corrections must absorb it -- the checked bound may not exceed the original one.
 C2  inflate every convexity dual by +0.5: same requirement.
 C3  lower every positive internal C1 excess by 1 (a wrong cost table): the cover group minimum must
     change and the bound must drop (the checker recomputes covers from the table).
 C4  drop the cut row (dual set to 0): the bound may only go down or stay.
usage: cc_cert_mutation.py FAMILY.json E.npy DUALS.npz MODE"""
import sys, os, json, tempfile, subprocess
import numpy as np

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))


def check(fam, E_p, d_p, mode):
    p = subprocess.run([PY, os.path.join(HERE, "cc_cert.py"), fam, E_p, d_p, mode, "y_best"], capture_output=True, text=True)
    return json.loads(p.stdout.strip().splitlines()[-1])


def main():
    fam, E_p, d_p, mode = sys.argv[1:5]
    D = dict(np.load(d_p)); base = check(fam, E_p, d_p, mode)
    LB0 = base["lower_bound_float"]; out = dict(original=LB0)
    NO = 10080; NT = 30
    comp = D["comp"]; nfree = int((comp == 0).sum()); ncomp = len(set(comp.tolist()) - {0})
    r_conv = 2 * NO + nfree + 2 * NT; s_row = r_conv + ncomp
    tmpd = tempfile.mkdtemp()
    def run_mut(name, y):
        D2 = dict(D); D2["y_best"] = y; p = os.path.join(tmpd, name + ".npz"); np.savez(p, **D2)
        return check(fam, E_p, p, mode)
    y = D["y_best"].astype(float).copy(); y[s_row] += 1.0
    r = run_mut("c1", y); out["C1_s_dual_plus_1"] = dict(LB=r["lower_bound_float"], rejected=r["lower_bound_float"] <= LB0 + 1e-9)
    y = D["y_best"].astype(float).copy(); y[r_conv:r_conv + ncomp] += 0.5
    r = run_mut("c2", y); out["C2_conv_plus_half"] = dict(LB=r["lower_bound_float"], rejected=r["lower_bound_float"] <= LB0 + 1e-9)
    sys.path.insert(0, HERE); import options as OP
    _, opts = OP.load(fam); T = np.array([o["t"] for o in opts])
    C1 = [2, 3, 4, 5, 6, 7, 23, 24, 25, 26, 27]
    idx = np.nonzero(np.isin(T, C1))[0]
    E = np.load(E_p); E2 = E.copy(); blk = E2[np.ix_(idx, idx)]
    blk = np.where((blk > 0) & (blk < 99), blk - 1, blk); E2[np.ix_(idx, idx)] = blk
    pE = os.path.join(tmpd, "E2.npy"); np.save(pE, E2)
    p = subprocess.run([PY, os.path.join(HERE, "cc_cert.py"), fam, pE, d_p, mode, "y_best"], capture_output=True, text=True)
    r = json.loads(p.stdout.strip().splitlines()[-1])
    out["C3_C1_internal_minus_1"] = dict(LB=r["lower_bound_float"], cover_rc_min=r["cover_rc_min"],
                                         changed=(r["cover_rc_min"] != base["cover_rc_min"]) and r["lower_bound_float"] < LB0)
    if len(D["sec_rows"]):
        y = D["y_best"].astype(float).copy(); y[D["sec_rows"]] = 0.0
        r = run_mut("c4", y); out["C4_drop_cut_dual"] = dict(LB=r["lower_bound_float"], ok=r["lower_bound_float"] <= LB0 + 1e-9)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
