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
    import l6_coupled_144 as PIECE
    import l6_chain_rows_144 as CR
    import l6_871_analysis_144 as AN
    import l6_rows_final_144 as RF
    PIECE.load_caps()
    CR.load_cache()
    AN.load_h()
    verdicts = {}
    for t in range(0, 5):
        r = RF.run(t, allow_compute=False)
        verdicts[f"L{867 + t}"] = dict(
            coordinate_rows=r["coordinate_rows"], strict=r["strict"],
            surviving=r["surviving"],
            surviving_with_fallback=r["surviving_with_fallback"],
            survivors=[{k: x[k] for k in ("k", "Z", "H", "Bstar", "G", "c", "d",
                                          "D2", "h", "required", "bound",
                                          "verdict")} for x in r["survivors"]],
            row_digest=digest(sorted(
                [[x["verdict"], x["bound"], x["required"]] for x in
                 RF.run(t, allow_compute=False)["survivors"]])))
    cert["model_verdicts"] = verdicts

    wit = ROOT / "outputs" / "witness_144"
    cert["equality_witnesses"] = {}
    for name in sorted(p.name for p in wit.glob("*.jsonl")):
        txt = (wit / name).read_text()
        lines = [l for l in txt.splitlines() if l.strip()]
        cert["equality_witnesses"][name] = dict(
            count=len(lines),
            digest=hashlib.sha256(txt.encode()).hexdigest())
    (ROOT / "outputs" / "rr_l6_certificate_144.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in cert.items()
                      if k not in ("sources", "binaries", "hand_lemmas")},
                     ensure_ascii=False, indent=1)[:2500])
    print(json.dumps({k: v.get("holds") for k, v in cert["hand_lemmas"].items()},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
