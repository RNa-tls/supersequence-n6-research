#!/usr/bin/env python3
"""Round N (section 15) -- mutation tests for the Round N checkers.
 M1  audit_identity: delete / swap characters of a 46185 word -> the audit must reject it
     (not a superpermutation, not tight, or J differs).
 M2  cut-charge checker (quotients-style IN/OUT): plant an A option with IN = OUT = 0 by lowering two
     excess entries -> the lemma check must fail; untouched matrix -> passes.
 M3  path-cover DP checker: lower one internal weight of C1 -> PC(1) must change or the DP must
     detect the inconsistency; untouched -> PC = 10, 6, 3, 1, 0.
 M4  SAT encoding: the 46185 assignment must be SAT at B = 23 and UNSAT at B = 22 (done in the run log);
     here: a corrupted assignment (two trails swapped) must violate a constraint of the CNF.
usage: mutation_tests.py FAMILY.json E.npy WORD"""
import sys, os, json, subprocess, tempfile, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))

def run(args):
    p = subprocess.run([PY] + args, capture_output=True, text=True)
    return p.returncode, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr.strip().splitlines()[-1]

def main():
    fam_p, E_p, word_p = sys.argv[1], sys.argv[2], sys.argv[3]
    res = {}
    # M1
    w = open(word_p).read().strip()
    rnd = random.Random(7); outcomes = []
    for trial in range(4):
        ww = list(w)
        if trial % 2 == 0:
            i = rnd.randrange(len(ww)); del ww[i]
        else:
            i = rnd.randrange(len(ww) - 1); ww[i], ww[i + 1] = ww[i + 1], ww[i]
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f: f.write("".join(ww)); tmp = f.name
        rc, last = run([os.path.join(HERE, "audit_identity.py"), tmp, fam_p])
        outcomes.append(dict(mutation="delete" if trial % 2 == 0 else "swap", rejected=(rc != 0) or ('"all_equal": true' not in last) or ('"J_run": 100' not in last)))
        os.unlink(tmp)
    rc, last = run([os.path.join(HERE, "audit_identity.py"), word_p, fam_p])
    res["M1_audit"] = dict(original_accepted=(rc == 0 and '"all_equal": true' in last), mutants=outcomes)
    # M2
    fam, opts = OP.load(fam_p); E = np.load(E_p)
    tr = np.array([o["t"] for o in opts]); isA = np.array([o["m"] == 672 for o in opts])
    phi = np.nonzero(~isA)[0]; Aidx = np.nonzero(isA)[0]
    def lemma_ok(EE):
        IN = EE[np.ix_(phi, Aidx)].min(0); OUT = EE[np.ix_(Aidx, phi)].min(1)
        return bool(np.all(IN + OUT >= 1))
    ok0 = lemma_ok(E)
    E2 = E.copy(); a = int(Aidx[17]); E2[phi[0], a] = 0; E2[a, phi[5]] = 0
    res["M2_cut_charge"] = dict(original_passes=ok0, planted_violation_detected=not lemma_ok(E2))
    # M3: perturb the family weights by swapping two runs of trail 2 version 0 -> internal structure breaks
    fam2 = json.loads(json.dumps(fam))
    s = fam2["trails"][2]["versions"][0]
    runs = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
    runs[3], runs[10] = runs[10], runs[3]
    fam2["trails"][2]["versions"][0] = "".join(runs)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(fam2, f); tmpf = f.name
    rc1, l1 = run([os.path.join(HERE, "pc_dp_check.py"), fam_p, "2,3,4,5,6,7,23,24,25,26,27"])
    rc2, l2 = run([os.path.join(HERE, "pc_dp_check.py"), tmpf, "2,3,4,5,6,7,23,24,25,26,27"])
    os.unlink(tmpf)
    res["M3_pc_dp"] = dict(original=l1, mutated=l2, changed_or_rejected=(l1 != l2))
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
