#!/usr/bin/env python3
"""Machine-checkable certificate for the round-144 results.

Records, for every load-bearing exhaustive search: the exact node count, the
uncapped flag, a deterministic digest of the proved table, the source hash and
the binary hash.  Nothing here is a proof by itself; it is the audit trail.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    cert = {"disclaimer":
            "This repository has NOT proved L6 >= 872.  Every number below is "
            "an exhaustive search inside an explicitly relaxed upper-bound "
            "model, or an identity check.  Capped searches are marked."}
    sources = ["src/l6_master_identity_144.py", "src/l6_sigma_deficit_144.py",
               "src/l6_incidence_144.py", "src/l6_certificate_144.py",
               "src/l6_marked_capacity_144.py", "src/l6_marked_capacity_144.c",
               "src/l6_marked_capacity_pruned_144.c", "src/l6_coupled_144.py",
               "src/l6_chain_capacity_144.c", "src/l6_chain_rows_144.py",
               "src/l6_build_captable_144.py", "src/l6_build_chaintable_144.py"]
    cert["sources"] = {s: sha(ROOT / s) for s in sources}
    cert["binaries"] = {b: sha(ROOT / "outputs" / b) for b in
                        ("l6cap_144.exe", "l6cap_p_144.exe", "l6chain_144.exe")}

    pt = json.loads((ROOT / "outputs" /
                     "rr_l6_marked_capacity_table_144.json").read_text())
    cert["piece_table"] = dict(
        digest=digest(pt["tables"]),
        cells=len(pt["cells"]),
        capped_cells=[k for k, v in pt["cells"].items() if v["capped"]],
        total_nodes=sum(v["nodes"] for v in pt["cells"].values()),
        bmax=pt["bmax"])

    ct = json.loads((ROOT / "outputs" /
                     "rr_l6_chain_capacity_144.json").read_text())
    cert["chain_table"] = dict(
        digest=digest({k: v["cc"] for k, v in ct.items()}),
        cells=len(ct),
        capped_cells=[k for k, v in ct.items() if v["capped"]],
        total_nodes=sum(v["nodes"] for v in ct.values()))

    sys.path.insert(0, str(ROOT / "src"))
    import l6_marked_capacity_144 as MC
    import l6_incidence_144 as IN
    cert["hand_lemmas"] = dict(
        joint_catalogue=MC.catalogue_check(),
        companion_hex=MC.companion_lemma(),
        mixed_shadow=MC.shadow_theorem(),
        left_S6_symmetry=MC.s6_symmetry(),
        incidence=IN.check(4000))
    import l6_chain_rows_144 as CR
    CR.load_cache()
    verdicts = {}
    for t in range(0, 5):
        CR.REQUESTED.clear()
        CR._best.cache_clear()
        r = CR.run(t)
        verdicts[f"L{867 + t}"] = dict(
            rows=r["rows"], strict=r["strict"],
            strict_by_piece_model=r["strict_by_piece_model"],
            surviving=r["surviving"],
            surviving_using_fallback=r["surviving_using_fallback"],
            unproved_cells=len(CR.REQUESTED),
            row_digest=digest([[x["verdict"], x["chain_bound"], x["required"]]
                               for x in CR.rows_for(t, False)]))
    cert["chain_model_verdicts"] = verdicts
    (ROOT / "outputs" / "rr_l6_certificate_144.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in cert.items()
                      if k not in ("sources", "binaries", "hand_lemmas")},
                     ensure_ascii=False, indent=1)[:2500])
    print(json.dumps({k: v.get("holds") for k, v in cert["hand_lemmas"].items()},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
