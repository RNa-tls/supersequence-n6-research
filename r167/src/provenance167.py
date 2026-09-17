#!/usr/bin/env python3
"""Round 167 -- provenance for the bridge-aware basis re-optimisation.

No wall-clock field is stored in any round-167 certificate.  Provenance hashes
every one of them, so a timing anywhere would make provenance itself
irreproducible -- the wart round 163 had to repair.  Timings go to stdout.

Compressed artifacts are pinned twice from this round on: by the container
hash and by the canonical plain-text hash (rule G1 of gzrule167.py).
"""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r167" / "src"))
from gzrule167 import plain_sha256                                # noqa: E402

AUDITED = ["r152/src/checker152.py", "r152/src/piece152.py",
           "r152/src/extree152.py", "r152/src/rows152.py",
           "r163/HAND_PROOF_INVENTORY.md",
           "r164/ROUTE_B_CERTIFICATE_REPLAY.md",
           "r165/MACHINE_PROOF_BASIS.md",
           "r166/EXTREE_BASIS_CERTIFICATION.md",
           "r165/certs/row_closure_graph_165.json",
           "r166/certs/verification_166.json",
           "r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz"]
INPUTS = ["r152/certs/verify_all_c152.json",
          "r152/certs/verify_piece_c152.json",
          "r152/certs/cap_cert_all_152.txt", "r152/certs/pcert_all_152.txt",
          "r163/src/hidden163.py", "r164/src/routeb164.py",
          "r164/certs/targets_164.json", "r164/certs/verifygen_164.json",
          "r165/src/closure165.py", "r166/src/bridge166.py",
          "r166/src/extree_basis_verify.py"]


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
    src = sorted(p.name for p in (ROOT / "r167" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r167" / "certs").iterdir()
                   if p.is_file())
    tot = {}
    for name, path, keys in (
        ("rebasis", "r167/certs/bridge_rebasis_167.json",
         ("facts", "bridge_enumeration", "fact_level_objective", "ok")),
        ("row_optimum", "r167/certs/row_optimum_167.json",
         ("baseline", "exposed_rows", "round_165_exposed_rows", "consulted",
          "universe", "optimum", "fact_level_plan", "already_certified",
          "cost", "ok")),
        ("optimality", "r167/certs/optimality_certificate_167.json",
         ("claim", "exposed_rows", "upper_bound", "lower_bound",
          "weighted_variants", "progress", "ok")),
        ("plan", "r167/certs/round168_plan_167.json",
         ("calibration", "margins", "generation_plan", "ok")),
        ("verifier_a", "r167/certs/verifier_a_167.json",
         ("batches", "all_ok", "total_cells", "total_nodes")),
        ("gzip_rule", "r167/certs/gzip_rule_167.json",
         ("demonstration", "existing_artifacts", "ok")),
        ("reproduction", "r167/certs/reproduction_167.json",
         ("runs", "identical", "ok")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            trimmed = {}
            for k in keys:
                v = d.get(k)
                if isinstance(v, dict):
                    v = {kk: vv for kk, vv in v.items()
                         if not isinstance(vv, (list, dict))
                         or len(json.dumps(vv)) < 400}
                trimmed[k] = v
            tot[name] = trimmed
    plain = {p: plain_sha256(ROOT / p) for p in AUDITED if p.endswith(".gz")}
    out = dict(round=167, node="bridge-aware second-route basis "
                              "re-optimisation",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               audited_plain_sha256=plain,
               inputs={p: sha(p) for p in INPUTS},
               r167_sources={f"r167/src/{n}": sha(f"r167/src/{n}")
                             for n in src},
               r167_certs={f"r167/certs/{n}": sha(f"r167/certs/{n}")
                           for n in certs},
               audit_doc=sha("r167/BRIDGE_AWARE_BASIS.md"),
               totals=tot)
    (ROOT / "r167" / "certs" / "provenance_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
