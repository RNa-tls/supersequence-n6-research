#!/usr/bin/env python3
"""Round 167 phase 19 -- reproduce every planning artifact from a clean clone.

A fresh `git clone` of HEAD is made in a scratch directory, the round-167
modules are run there twice, and the produced bytes are compared

  * between the two runs, and
  * against the artifacts committed in the working tree.

Nothing in this round writes a wall-clock field, so byte identity is the
expected outcome and any difference is a defect to fix, not to explain away.

The verifier-A rerun over all three batches is excluded here by cost only
(about fifty minutes per run).  Batch 1 is included so that the streaming
driver's determinism is covered by the same test.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STEPS = [
    ("rebasis", ["python3", "r167/src/rebasis167.py"],
     ["r167/certs/bridge_rebasis_167.json"]),
    ("rowopt", ["python3", "r167/src/rowopt167.py"],
     ["r167/certs/row_optimum_167.json"]),
    ("optcert", ["python3", "r167/src/optcert167.py"],
     ["r167/certs/optimality_certificate_167.json"]),
    ("plan", ["python3", "r167/src/plan167.py"],
     ["r167/certs/round168_plan_167.json"]),
    ("gzrule", ["python3", "r167/src/gzrule167.py"],
     ["r167/certs/gzip_rule_167.json"]),
    ("verifier_a_batch1",
     ["python3", "r167/src/verifyA167.py",
      "--batch", "r164/certs/extree_prefix_164.txt.gz",
      "--report", "r167/certs/verifier_a_batch1_167.json"],
     ["r167/certs/verifier_a_batch1_167.json"]),
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
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    base = Path(tempfile.mkdtemp(prefix="r167repro-"))
    runs = {}
    try:
        for i in (1, 2):
            clone = base / f"run{i}"
            subprocess.run(["git", "clone", "--quiet", str(ROOT), str(clone)],
                           check=True)
            subprocess.run(["git", "checkout", "--quiet", head], cwd=clone,
                           check=True)
            runs[f"run{i}"] = run_once(clone)
    finally:
        pass
    same, diffs = True, []
    committed = {}
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
            if committed[a] is not None and h1 is not None and committed[a] != h1:
                same = False
                diffs.append(dict(artifact=a, clean=h1,
                                  working_tree=committed[a],
                                  reason="the clean run differs from the "
                                         "committed artifact"))
    ok = same and all(v["returncode"] == 0 for r in runs.values()
                      for v in r.values())
    out = dict(head=head, working_tree_dirty=dirty,
               runs={k: {n: {kk: vv for kk, vv in v.items()
                             if kk != "seconds"}
                         for n, v in r.items()} for k, r in runs.items()},
               committed=committed, identical=same, differences=diffs, ok=ok,
               excluded=dict(
                   artifact="r167/certs/verifier_a_167.json",
                   reason="the full three-batch verifier-A rerun costs about "
                          "fifty minutes per run; batch 1 is reproduced here "
                          "and the driver stores no timing, so the exclusion "
                          "is a cost decision, not a determinism gap"))
    (ROOT / "r167" / "certs" / "reproduction_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"},
                     ensure_ascii=False, indent=1))
    for k, r in runs.items():
        print(k, {n: v["seconds"] for n, v in r.items()})
    shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
