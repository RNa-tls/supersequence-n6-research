#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- old-format regression.

1. No pre-existing file changed: `git diff --stat <base> -- . ':!r172'` is empty.
2. A real Round-171 production certificate (L6-EXTREE-3) is REPLAYED (its own
   hash-trust entry removed for this call) by
     - the unchanged Round-168 verifier A (verifyA168 -> extree152),
     - the unchanged Round-168 verifier B (verify168 -> routeb164.TreeVerifier),
     - verifier A4's and B4's old-format delegation path,
   and all four must accept with the node count recorded when it was certified.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import trust172                                                   # noqa: E402
import verifyA172 as VA                                           # noqa: E402
import verifyB172 as VB                                           # noqa: E402
import verifyA168 as A3                                           # noqa: E402
import verify168 as B3                                            # noqa: E402

BASE = "0a9884e54659590b617ea8458988bee30fe2494b"
JOB = "r171/certs/bulk_j171/jobs/1_4_5_0_1_0_c10000000_e0.json"
OUT = "r172/certs/old_format_regression.json"


def main():
    diff = subprocess.run(["git", "diff", "--stat", BASE, "--", ".", ":!r172"],
                          cwd=ROOT, capture_output=True, text=True).stdout.strip()
    trust172.setup()
    job = json.loads((ROOT / JOB).read_text())
    rel = job["certificate"]["path"]
    sha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    assert sha == job["certificate"]["sha256"]
    B3.TRUST.pop(sha, None)                   # force a real replay of THIS file
    rows = {}
    for name, fn in (("A3_unchanged_verifyA168", lambda: A3.verify(rel, log=lambda *_: None)),
                     ("B3_unchanged_verify168", lambda: B3.verify_any(rel)),
                     ("A4_old_format_delegation", lambda: VA.verify(rel, log=lambda *_: None)),
                     ("B4_old_format_delegation", lambda: VB.verify_any4(rel))):
        t = time.monotonic()
        r = fn()
        rows[name] = dict(ok=r["ok"], nodes=r.get("nodes"),
                          trusted_on_hash=bool(r.get("trusted")),
                          seconds_noncanonical=round(time.monotonic() - t, 1))
        print(name, rows[name], flush=True)
    ok = (not diff and all(r["ok"] and r["nodes"] == job["nodes"]
                           and not r["trusted_on_hash"] for r in rows.values()))
    out = dict(title="old-format regression (EXPERIMENTAL round)",
               pre_existing_files_changed=diff or None, base_commit=BASE,
               certificate=rel, container_sha256=sha, recorded_nodes=job["nodes"],
               results=rows, passed=ok)
    (ROOT / OUT).write_text(json.dumps(out, indent=1) + "\n")
    print("PASSED" if ok else "FAILED")


if __name__ == "__main__":
    main()
