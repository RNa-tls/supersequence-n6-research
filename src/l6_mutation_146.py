#!/usr/bin/env python3
"""Round 146 — MUTATION TESTING of the verifier and regression suite.

Each mutation is a deliberate fault injected into a load-bearing file.  The
harness applies it, runs a designated detector, records whether the detector
FAILED (= the fault was caught), then restores the file with git.  A mutation
that escapes every detector is a test-suite gap and is reported as such.

Two of the mutations reproduce soundness bugs this project actually made:
  M1  conflate the heavy budget with the reuse budget in the suffix bound;
  M2  combine the models at a COMMON s instead of maxing over each model's own s.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UB = ROOT / "outputs" / "rr_l6_chain_ub_144.txt"
SC = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
          "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")


def run(cmd, timeout=900):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          cwd=ROOT, timeout=timeout)


_SNAP = {}


def snapshot(files):
    """Back up BY CONTENT.  git checkout silently does nothing for untracked
    files, which in round 146 left injected faults in place and produced a
    bogus 'nu target is not a pass entry' finding before it was caught."""
    for f in files:
        _SNAP[f] = (ROOT / f).read_bytes()


def restore(files):
    for f in files:
        if f in _SNAP:
            (ROOT / f).write_bytes(_SNAP[f])
    run("gcc -O2 -o outputs/l6chain_144.exe src/l6_chain_capacity_144.c")


def patch(path, old, new):
    p = ROOT / path
    s = p.read_text()
    if old not in s:
        return False
    p.write_text(s.replace(old, new, 1))
    return True


MUTATIONS = []


def mut(name, files, apply_fn, detector, why):
    MUTATIONS.append(dict(name=name, files=files, apply=apply_fn,
                          detector=detector, why=why))


# ---- M1: the real heavy/reuse budget conflation
mut("M1_heavy_reuse_budget_conflation", ["src/l6_chain_capacity_144.c"],
    lambda: patch("src/l6_chain_capacity_144.c",
                  "left, HMAX - hu) - 1;", "left + (HMAX - hu), 0) - 1;"),
    lambda: _q2_witness_count(),
    "should make the Q2 witness enumeration wrong (root-pruned)")

# ---- M2: the real common-s model combination
mut("M2_common_s_model_combination", ["src/l6_rows_final_144.py"],
    lambda: patch("src/l6_rows_final_144.py",
                  "        if nch == 1 and r[\"s\"] != 0:\n            continue",
                  "        if False:\n            continue"),
    lambda: _rows_871(),
    "dropping the one-object s=0 rule must change the 871 survivor set")

# ---- M3/M4: corrupt the hexagon / orbit canonical key
mut("M3_hexagon_classes_merged", ["src/l6_cleanroom_146.py"],
    lambda: patch("src/l6_cleanroom_146.py",
                  "def hexkey(s):\n    x, best = s, s",
                  "def hexkey(s):\n    x, best = s, s\n    if s[0] == '1' and s[1] == '3':\n        return '123456'"),
    lambda: _cleanroom(),
    "merging two hexagon classes must break the 120-hexagon count and G")

mut("M3b_hexagon_step_wrong", ["src/l6_cleanroom_146.py"],
    lambda: patch("src/l6_cleanroom_146.py",
                  "def sig(s):                                 # full rotation  (hexagon step)\n    return s[1:] + s[0]",
                  "def sig(s):                                 # full rotation  (hexagon step)\n    return s[-1] + s[:-1]"),
    lambda: _cleanroom(),
    "reversing the hexagon step must break passes, nu and the identities")

mut("M3c_orbit_step_wrong", ["src/l6_cleanroom_146.py"],
    lambda: patch("src/l6_cleanroom_146.py",
                  "def tau(s):                                 # rotate all but the last (orbit step)\n    return s[1:-1] + s[0] + s[-1]",
                  "def tau(s):                                 # rotate all but the last (orbit step)\n    return s[1:] + s[0]"),
    lambda: _cleanroom(),
    "confusing tau with sigma must break the clean-E classification and MASTER")

mut("M4_orbit_id_altered", ["src/l6_cleanroom_146.py"],
    lambda: patch("src/l6_cleanroom_146.py",
                  "def orbkey(s):\n    x, best = s, s",
                  "def orbkey(s):\n    if s.startswith('12'):\n        return s\n    x, best = s, s"),
    lambda: _cleanroom(),
    "one wrong orbit id must break O, k and MASTER")

# ---- M5: drop one hidden window
mut("M5_drop_one_hidden_window", ["src/l6_cleanroom_146.py"],
    lambda: patch("src/l6_cleanroom_146.py",
                  "for o in range(1, gap) if len(set(raw[o:o + n])) == n]",
                  "for o in range(1, max(1, gap - 1)) if len(set(raw[o:o + n])) == n]"),
    lambda: _cleanroom(),
    "the hidden-count check must fire")

# ---- M6: change one connector weight
mut("M6_connector_weight_shifted", ["src/l6_cleanroom_146.py"],
    lambda: patch("src/l6_cleanroom_146.py",
                  "    for k in range(1, n):\n        if a[k:] == b[:n - k]:\n            return k",
                  "    for k in range(1, n):\n        if a[k:] == b[:n - k]:\n            return k + (1 if k == 2 else 0)"),
    lambda: _cleanroom(),
    "a wrong omega must break (FO) and the fixed-representative test")

# ---- M7: shift the orbit/hexagon incidence used by the coexistence solver
mut("M7_shift_ORBHEX_by_one", ["src/l6_circuit_coexist_144.py"],
    lambda: patch("src/l6_circuit_coexist_144.py",
                  "ORBHEX = [sorted({HEX[v] for v in ORBPORTS[q]}) for q in range(NQ)]",
                  "ORBHEX = [sorted({HEX[v] for v in ORBPORTS[(q + 1) % NQ]}) for q in range(NQ)]"),
    lambda: _coexist(),
    "a shifted orbit->hexagon table must change the coexistence verdict")

# ---- M8: delete one equality witness
mut("M8_remove_one_equality_witness", ["outputs/witness_144/wit_Q1.jsonl"],
    lambda: _drop_line("outputs/witness_144/wit_Q1.jsonl"),
    lambda: _witness_counts(),
    "the witness-count test must fail")


def _drop_line(path):
    p = ROOT / path
    ls = [l for l in p.read_text().splitlines() if l.strip()]
    p.write_text("\n".join(ls[:-1]) + "\n")
    return True


# ------------------------------------------------------------------ detectors
def _q2_witness_count():
    run("gcc -O2 -o outputs/l6chain_144.exe src/l6_chain_capacity_144.c")
    out = SC / "mut_q2.jsonl"
    r = run(f"./outputs/l6chain_144.exe 0 8 0 0 0 1 8000000000 "
            f"{UB} 92 {out}")
    try:
        j = json.loads(r.stdout)
    except Exception:
        return dict(detected=True, note="searcher failed to run")
    n = sum(1 for l in out.read_text().splitlines() if l.strip()) if out.exists() else -1
    return dict(detected=not (j.get("witnesses") == 1 and n == 1 and
                              j.get("capped") is False),
                observed=dict(witnesses=j.get("witnesses"), lines=n,
                              capped=j.get("capped")))


def _rows_871():
    r = run("python3 -c \"import sys;sys.path.insert(0,'src');"
            "import l6_coupled_144 as P,l6_chain_rows_144 as C,"
            "l6_871_analysis_144 as A,l6_rows_final_144 as R,json;"
            "P.load_caps();C.load_cache();A.load_h();"
            "x=R.run(4,allow_compute=False);"
            "print(json.dumps({'surv':x['surviving'],'fb':x['surviving_with_fallback']}))\"")
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(detected=True, note="evaluation crashed")
    return dict(detected=not (j["surv"] == 2 and j["fb"] == 0), observed=j)


def _cleanroom():
    r = run("python3 src/l6_cleanroom_146.py data/verified_872_witness.txt "
            "legacy_research/outputs/standard_6.txt")
    return dict(detected=(r.returncode != 0 or "failures=0" not in r.stdout),
                observed=r.stdout.strip().splitlines()[:1])


def _coexist():
    r = run("python3 -c \"import sys,json;sys.path.insert(0,'src');"
            "import l6_circuit_coexist_144 as C;"
            "ch=[json.loads(l)['ports'] for l in "
            "open('outputs/witness_144/wit_Q1.jsonl') if l.strip()];"
            "print(json.dumps([C.coexist(c,6)['ok'] for c in ch]))\"")
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(detected=True, note="coexistence crashed")
    return dict(detected=any(j), observed=j)


def _witness_counts():
    r = run("python3 -c \"import sys;sys.path.insert(0,'tests');"
            "exec(open('tests/test_l6_endgame_144.py').read().split("
            "'if __name__')[0]);test_witness_counts_are_two_and_one();"
            "print('PASSED')\"")
    return dict(detected=("PASSED" not in r.stdout), observed=r.stdout[-120:])


if __name__ == "__main__":
    res = []
    # only TRACKED modifications matter; new untracked outputs are fine
    st = run("git status --porcelain --untracked-files=no")
    if st.stdout.strip():
        print("REFUSING: tracked files are already modified"); sys.exit(2)
    for m in MUTATIONS:
        snapshot(m["files"])
        applied = m["apply"]()
        if not applied:
            res.append(dict(name=m["name"], applied=False,
                            note="patch target not found"))
            restore(m["files"])
            continue
        try:
            d = m["detector"]()
        except Exception as ex:
            d = dict(detected=True, note=f"detector raised {ex!r}")
        restore(m["files"])
        res.append(dict(name=m["name"], applied=True, why=m["why"], **d))
        print(f"{m['name']:38s} detected={d.get('detected')}  {d.get('observed', d.get('note',''))}")
    st = run("git status --porcelain --untracked-files=no")
    clean = (not st.stdout.strip()) and all(
        (ROOT / f).read_bytes() == b for f, b in _SNAP.items())
    escaped = [r["name"] for r in res if r.get("applied") and not r.get("detected")]
    out = dict(mutations=res, tree_restored=clean, escaped=escaped,
               ok=(clean and not escaped))
    (ROOT / "outputs" / "rr_l6_mutation_146.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\ntree_restored={clean}  escaped={escaped}")
