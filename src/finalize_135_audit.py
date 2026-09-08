#!/usr/bin/env python3
"""라운드 135 감사 — 판정 JSON 과 master 원장 갱신."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
sys.path.insert(0, str(ROOT / "src"))
import audit_r135_136 as A                                       # noqa: E402


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    d = A.summarise()
    d["partial_arc_contraction"] = A.partial_arc_contraction()
    (OUT / "rr_r135_audit_136.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    rt, ce, eq = d["resource_table"], d["capacity_exclusions"], d["equality_classification"]
    se, ec, pac = d["seam_exhaustion"], d["extremal_census"], d["partial_arc_contraction"]
    C = "CONFIRMED"
    verdicts = {
        "25_row_resource_decomposition": dict(verdict=C,
            evidence=f"independently derived P=122, O=27, D=13 and enumerated "
                     f"{rt['n_rows']} live rows = {rt['by_type_F']}; delta split "
                     f"{rt['by_delta']} - exactly 18 with delta=0 and 7 with delta=1"),
        "delta_plus_x_plus_H_le_F_minus_1": dict(verdict=C,
            evidence="L = 846 + S + H <= 871 gives f_out >= e + x + H + 1; Theorem 129.1 "
                     "gives f_out = F + e - delta with delta >= 0; substituting yields the "
                     "inequality. F=1 forces delta=x=H=0; F=2 allows delta+x+H <= 1"),
        "partial_rotational_arc_contraction": dict(verdict=C,
            evidence=f"lemma formulated and proved from scratch, verified on "
                     f"{pac['cases']} n=6 cases with zero violations: pass (v,a) + five "
                     f"passes filling orb(sigma^a v) ending at (sigma^a v, b) -> single "
                     f"pass (v, a+b); P-5, O-1, D/S/H unchanged. a+b=6 recovers Round 134",
            caveat="Astra's own statement could NOT be recovered - see lineage"),
        "type_A_contraction": dict(verdict=C,
            evidence="the tripled hexagon needs two contractions whose intermediate "
                     "replacement is a PARTIAL arc (v, l0+l1), which is exactly why the "
                     "generalised lemma is needed; both contraction orders are valid, and "
                     "the two locked runs sit in orb(sigma^{l0}v) and orb(sigma^{l0+l1}v), "
                     "distinct words of one hexagon hence distinct orbits, so O drops by 2"),
        "type_B_nested_contraction": dict(verdict=C,
            evidence="inner-first is forced exactly as in Round 134 (audited and confirmed "
                     "there): before the inner contraction the outer object is 11 passes, "
                     "so it is not yet of locked-block shape"),
        "contracted_parameter_accounting": dict(verdict=C,
            evidence="P' = 112 + u, O' = 25, D' = 13 - u derived independently; u = number "
                     "of orbit phases skipped inside the two contracted runs (u = 0 when "
                     "x = 0, since a skip needs an intra-run omega>=3 arc). b' = e' + x' = "
                     "2 + x + delta - F, consistent on all 25 rows"),
        "H0_capacity_exclusions": dict(verdict=C,
            evidence=f"{ce['n_rows']} rows with delta=0, H=0; every one excluded for every "
                     f"admissible u, since required 112+u exceeds N*(b',0,13-u)",
            audit_note="the reported capacity 106 is N*(1,0,15) - the s = 5k = 15 GLOBAL "
                       "pool, not the contracted object's actual deficit. That is sound "
                       "but loose. The tight cell is N*(1,0,13), which is NOT in the "
                       "stored Round-115 table; this audit computed it fresh: 98 "
                       "(681,902,414 nodes, uncapped). Both 98 and 106 are below 112, so "
                       "the conclusion is unaffected"),
        "H1_unique_heavy_joint": dict(verdict=C,
            evidence="H = sum of (omega-3)+ over joints; total 1 forces exactly one term "
                     "equal to 1, i.e. one omega=4 joint. Weight 5/6 contribute 2/3, two "
                     "heavy joints contribute >= 2, and H has no endpoint term"),
        "equality_46_plus_66": dict(verdict=C,
            evidence=f"cutting at the unique weight-4 joint splits the deficit as "
                     f"d1+d2=13 with both pieces at b=g=0; max of N*(0,0,d1)+N*(0,0,d2) "
                     f"is {eq['max_total']} attained ONLY at {eq['equality_tuples']}, so "
                     f"both chains must be extremal. All cells uncapped"),
        "seam_exhaustion_312": dict(verdict=C,
            evidence=f"312 reconstructed independently as 1*13*12 + 12*13*1 = 156+156; "
                     f"all {se['combinations']} fail: {se['outcome']}. Zero survivors. "
                     f"The two chains must be disjoint in BOTH hexagons and orbits "
                     f"(10+15 = 25 = O' and 46+66 = 112 = P' leave no slack)"),
        "18_row_exclusion": dict(verdict=C,
            evidence="the 18 excluded rows are exactly the delta=0 rows: 13 closed by the "
                     "H=0 capacity argument and 5 by the H=1 argument"),
        "7_row_residual_classification": dict(verdict=C,
            evidence="the 7 survivors are exactly the delta=1 rows. delta=0 IS the "
                     "equality case of Theorem 129.1, which is the sole hypothesis of "
                     "Theorem 131.1; only there are the locality locks forced, so only "
                     "there does a locked block exist to contract. The limitation is a "
                     "THEOREM-SCOPE limit, not a compute limit"),
        "regression_suite_18_of_18": dict(verdict="PARTIAL",
            evidence="cannot be audited: the Round-135 branch and commit are absent from "
                     "the repository, so the tests themselves are unavailable. This is a "
                     "repository-state limitation, not a mathematical failure"),
        "lineage": dict(verdict="PARTIAL",
            evidence="commit 7b3fa9516bca80ac522dd8927f3adda05a4fb1f4 is not an object in "
                     "this repository and branch codex/round135-g2-k3 is not among the "
                     "remote heads after `git fetch origin`. Astra's source, report and "
                     "certificate could not be inspected"),
    }
    rep = dict(
        round=135, kind="PROOF AUDIT (Claude independent review of Astra/Codex Round 135)",
        target="(k,G) = (3,2)",
        overall="PARTIAL",
        overall_reason="every mathematical claim that could be reconstructed independently "
                       "reproduces exactly, but the Round-135 artefact itself (commit, "
                       "branch, source, report, 18/18 regression suite) is absent from the "
                       "repository, so sections 2, 15 and 16 could not be performed on the "
                       "deliverable under audit",
        verdicts=verdicts,
        independently_reconstructed=dict(
            P=rt["P"], O=rt["O"], D=rt["D"], inequality=rt["inequality"],
            n_rows=rt["n_rows"], by_delta=rt["by_delta"], by_type_F=rt["by_type_F"],
            contracted=dict(P="112 + u", O=25, D="13 - u"),
            capacities=ce["capacities_used"],
            equality_tuples=eq["equality_tuples"],
            extremal_chains=dict(s4=ec["extremal_chains_s4"], s9=ec["extremal_chains_s9"]),
            seam_combinations=se["combinations"], seam_all_fail=se["all_fail"]),
        delta1_survivors=rt["delta1_rows"],
        h0_closure_table=ce["rows"],
        findings=[
            "the reported capacity 106 is N*(1,0,15) (the s = 5k = 15 global pool), not the "
            "tight cell for the contracted object; the tight cell N*(1,0,13) is absent from "
            "the stored Round-115 table and was computed fresh here as 98. Conclusion "
            "unaffected - both are below the required 112",
            "the Round-135 branch/commit is unavailable, so sections 2 (recover the exact "
            "definition), 15 (18/18 regression) and 16 (lineage) could not be performed",
            "the 18/7 split is not an empirical outcome but an exact structural dichotomy: "
            "the excluded rows are precisely delta=0 and the survivors precisely delta=1"],
        scope=dict(
            cell_status="(k,G) = (3,2) remains OPEN - 7 delta=1 rows survive",
            outer_ledger="10/55 (k,G) - unchanged",
            NR6="ASSUMED",
            does_not_prove="L6 >= 872"),
        certificate=dict(
            source_commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                         capture_output=True, text=True).stdout.strip(),
            auditor_module=sha(ROOT / "src" / "audit_r135_136.py"),
            chain_capacity_115_c=sha(ROOT / "src" / "chain_capacity_115.c"),
            chain_capacity_115_bin=sha(ROOT / "src" / "chain_capacity_115.bin"),
            replays=[{"cell": "N*(1,0,13)", "passes": 98, "nodes": 681902414, "capped": False},
                     {"cell": "N*(1,0,12)", "passes": 98, "nodes": 307634294, "capped": False},
                     {"cell": "N*(0,0,13)", "passes": 83, "nodes": 14407541, "capped": False},
                     {"cell": "N*(0,0,4)", "passes": 46, "nodes": 3555, "capped": False},
                     {"cell": "N*(0,0,9)", "passes": 66, "nodes": 469852, "capped": False}],
            python_reimplementation="src/audit_r135_136.py chain_search() reproduces the C "
                                    "node counts exactly (3,555 and 469,852)"),
        label="ROUND-135 AUDIT - CLAUDE INDEPENDENT REVIEW",
        disclaimer="This project has not proved L6 >= 872")
    (OUT / "rr_r135_verdict_136.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    m = OUT / "superpermutation_n6_master_status.json"
    md = json.loads(m.read_text())
    md["round_135_audit_by_claude"] = rep
    m.write_text(json.dumps(md, ensure_ascii=False, indent=1))
    print(json.dumps(dict(overall=rep["overall"],
                          verdicts={k: v["verdict"] for k, v in verdicts.items()},
                          keys=len(md)), indent=1))


if __name__ == "__main__":
    main()
