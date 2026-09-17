#!/usr/bin/env python3
"""Round 168 phase 24 -- clean-checkout reproduction, twice, byte identical.

A fresh clone of HEAD is made twice and the deterministic round-168 artefacts
are rebuilt in each, then compared with each other and with the committed
copies.

What is IN: the target recheck, the independence-restricted census, the
capacity agreement, the mutation suite and the generator-bug controls.  Those
cover every analysis artefact and both regression harnesses, and the mutation
suite rebuilds its own two-level certificate DAG from scratch, so the
generator and both verifiers are exercised end to end.

What is OUT, and why: re-running verifier A and verifier B over the committed
proof trees costs hours per pass, and regenerating the batch costs hours more.
Those are cost exclusions, not determinism gaps -- no artefact in this round
stores a wall clock, and the certificate containers are written with
filename="" and mtime=0 so their bytes are a pure function of their text.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STEPS = [
    ("state", ["python3", "r168/src/recheck168.py"],
     ["r168/certs/state_168.json"]),
    ("census", ["python3", "r168/src/census168.py",
                "--verification", "r168/certs/verification_b_168.json"],
     ["r168/certs/census_168.json"]),
    ("agreement", ["python3", "r168/src/agree168.py",
                   "--verification", "r168/certs/verification_b_168.json",
                   "--generation", "r168/certs/generation_batch1_168.json"],
     ["r168/certs/agreement_168.json"]),
    ("mutations", ["python3", "r168/src/mutate168.py"],
     ["r168/certs/mutations_168.json", "r168/certs/mut_a_168.txt.gz",
      "r168/certs/mut_b_168.txt.gz"]),
    ("generator_controls", ["python3", "r168/src/controls168.py"],
     ["r168/certs/generator_controls_168.json"]),
]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_once(clone):
    out = {}
    for name, cmd, arts in STEPS:
        t0 = time.time()
        r = subprocess.run(cmd, cwd=clone, capture_output=True, text=True)
        out[name] = dict(returncode=r.returncode,
                         seconds=round(time.time() - t0, 1),
                         artifacts={a: (sha(clone / a)
                                        if (clone / a).exists() else None)
                                    for a in arts},
                         stderr_tail=r.stderr[-400:] if r.returncode else "")
    return out


def main():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    base = Path(tempfile.mkdtemp(prefix="r168repro-"))
    runs = {}
    for i in (1, 2):
        clone = base / f"run{i}"
        subprocess.run(["git", "clone", "--quiet", str(ROOT), str(clone)],
                       check=True)
        subprocess.run(["git", "checkout", "--quiet", head], cwd=clone,
                       check=True)
        runs[f"run{i}"] = run_once(clone)
    same, diffs, committed = True, [], {}
    for name, _cmd, arts in STEPS:
        for a in arts:
            h1 = runs["run1"][name]["artifacts"][a]
            h2 = runs["run2"][name]["artifacts"][a]
            if h1 is None or h1 != h2:
                same = False
                diffs.append(dict(artifact=a, run1=h1, run2=h2,
                                  reason="the two clean runs differ"))
            p = ROOT / a
            committed[a] = sha(p) if p.exists() else None
            if committed[a] and h1 and committed[a] != h1:
                same = False
                diffs.append(dict(artifact=a, clean=h1,
                                  working_tree=committed[a],
                                  reason="clean run differs from the "
                                         "committed artifact"))
    ok = same and all(v["returncode"] == 0 for r in runs.values()
                      for v in r.values())
    out = dict(head=head,
               runs={k: {n: {kk: vv for kk, vv in v.items() if kk != "seconds"}
                         for n, v in r.items()} for k, r in runs.items()},
               committed=committed, identical=same, differences=diffs, ok=ok,
               excluded=dict(
                   artifacts=["r168/certs/verification_a_168.json",
                              "r168/certs/verification_b_168.json",
                              "r168/certs/extree_batch1_168.txt.gz"],
                   reason="replaying the committed proof trees costs hours "
                          "per pass and regenerating the batch costs more; "
                          "no artefact stores a wall clock and the container "
                          "is written with filename='' and mtime=0, so this "
                          "is a cost exclusion, not a determinism gap"))
    (ROOT / "r168" / "certs" / "reproduction_168.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"},
                     ensure_ascii=False, indent=1))
    for k, r in runs.items():
        print(k, {n: v["seconds"] for n, v in r.items()})
    shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
