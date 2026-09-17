#!/usr/bin/env python3
"""Round 168 phase 25 -- provenance.

Every certificate is pinned twice: by its gzip container hash and by the
canonical plain-text hash that actually carries the mathematics (rule G1).
No wall-clock field is stored in any artefact this file hashes; timings go to
stdout and to the non-proof measurement log.

Historical hash-pinned artefacts are recorded, never rewritten.
"""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r167" / "src"))
from gzrule167 import plain_sha256                                # noqa: E402

AUDITED = ["r152/src/checker152.py", "r152/src/extree152.py",
           "r152/src/rows152.py", "r163/src/hidden163.py",
           "r164/src/routeb164.py", "r166/src/bridge166.py",
           "r166/src/extree_basis_verify.py",
           "r167/BRIDGE_AWARE_BASIS.md",
           "r167/certs/row_optimum_167.json",
           "r167/certs/optimality_certificate_167.json",
           "r167/certs/round168_plan_167.json",
           "r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz"]


def sha(p):
    q = ROOT / p
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def main():
    src = sorted(p.name for p in (ROOT / "r168" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r168" / "certs").iterdir()
                   if p.is_file())
    gz = [f"r168/certs/{n}" for n in certs if n.endswith(".gz")]
    tot = {}
    for name, path, keys in (
        ("state", "r168/certs/state_168.json",
         ("baseline", "target", "claim_sufficient", "claim_necessary",
          "free_layer", "ok")),
        ("generation", "r168/certs/generation_batch1_168.json",
         ("format", "cells_built", "failures", "total_search_nodes",
          "total_proof_nodes", "plain_bytes", "plain_sha256",
          "stored_bytes", "stored_sha256", "ok")),
        ("verifier_b", "r168/certs/verification_b_168.json",
         ("all_ok", "total_cells", "total_proof_nodes",
          "histogram_mismatches", "trusted_on_hash", "replayed_here")),
        ("verifier_a", "r168/certs/verification_a_168.json",
         ("all_ok", "total_cells", "total_nodes", "extree152_sha256")),
        ("agreement", "r168/certs/agreement_168.json",
         ("compared", "agrees", "plan_value_refuted",
          "historical_disagreements", "ok")),
        ("census", "r168/certs/census_168.json",
         ("certificates", "rows", "tail", "ok", "complete")),
        ("mutations", "r168/certs/mutations_168.json",
         ("invalid", "invalid_rejected", "valid", "valid_accepted",
          "real_batch_invalid", "real_batch_rejected", "ok")),
        ("generator_controls", "r168/certs/generator_controls_168.json",
         ("controls", "applied", "caught", "caught_by_the_verifier",
          "caught_by_divergence", "missed", "ok")),
        ("reproduction", "r168/certs/reproduction_168.json",
         ("identical", "ok")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            trimmed = {}
            for k in keys:
                v = d.get(k)
                if isinstance(v, (dict, list)) and len(json.dumps(v)) > 600:
                    v = f"<{len(v)} entries>"
                trimmed[k] = v
            tot[name] = trimmed
    out = dict(round=168, node="progressive EXTREE certification of the "
                               "190-cell basis",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               generator_sha256=sha("r168/src/gen168.py"),
               verifier_b_sha256=sha("r168/src/verify168.py"),
               verifier_b_engine_sha256=sha("r164/src/routeb164.py"),
               verifier_a_driver_sha256=sha("r168/src/verifyA168.py"),
               verifier_a_logic_sha256=sha("r152/src/extree152.py"),
               bridge_theorem_sha256=sha("r166/src/bridge166.py"),
               audited_sources={p: sha(p) for p in AUDITED},
               audited_plain_sha256={p: plain_sha256(ROOT / p)
                                     for p in AUDITED if p.endswith(".gz")},
               r168_sources={f"r168/src/{n}": sha(f"r168/src/{n}")
                             for n in src},
               r168_certs={f"r168/certs/{n}": sha(f"r168/certs/{n}")
                           for n in certs},
               r168_certificate_plain_sha256={
                   p: plain_sha256(ROOT / p) for p in gz},
               audit_doc=sha("r168/EXTREE_190_PROGRESS.md"),
               totals=tot)
    (ROOT / "r168" / "certs" / "provenance_168.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
