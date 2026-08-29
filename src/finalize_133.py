#!/usr/bin/env python3
"""라운드 133 마무리 — 보고서 JSON, **재현 가능한 증명서**(§20), master 원장 키."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
sys.path.insert(0, str(ROOT / "src"))


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def digest(argv, row):
    """실행 하나의 결정론적 다이제스트 — 인자와 결과만으로 재현 검증할 수 있다."""
    blob = "|".join(map(str, argv)) + "#" + "|".join(
        str(row[k]) for k in ("verdict", "nodes", "best_passes"))
    return hashlib.sha256(blob.encode()).hexdigest()[:32]


def certificate():
    ce132 = ROOT / "src" / "g2_cell_132.c"
    ce133 = ROOT / "src" / "g2_cell_133.c"
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = None
    runs = []
    for label, argv, row in [
        ("B_e1_b11_P1b with ORDPIN",
         [1, 28, 25, 0, 3, 3, 1, 18, 20, 1, 1, 1, 25, 29, 0, 0, 0, 0, 60000000000, 1,
          13, 1, 5, 8, 0, 2],
         dict(verdict="UNSAT_COMPLETE", nodes=30124862589, best_passes=101, seconds=3261)),
        ("B_e1_b11_P1b without ORDPIN",
         [1, 28, 25, 0, 3, 3, 1, 18, 20, 1, 1, 1, 25, 29, 0, 0, 0, 0, 60000000000, 1,
          13, 1, 5, 8, 0, 0],
         dict(verdict="UNSAT_COMPLETE", nodes=41335694797, best_passes=102, seconds=4691)),
        ("A/e=1 l114 regression control",
         [0, 28, 25, 0, 3, 3, 1, 18, 20, 1, 1, 1, 25, 29, 0, 0, 0, 0, 30000000000, 1,
          7, 1, 3, 4, 2, 0],
         dict(verdict="UNSAT_COMPLETE", nodes=12981632834, best_passes=101, seconds=1171)),
    ]:
        r = dict(label=label, argv=argv, **row)
        r["digest"] = digest(argv, row)
        runs.append(r)
    return dict(
        source_commit=commit,
        engine_132=dict(file="src/g2_cell_132.c", sha256=sha(ce132),
                        binary_sha256=sha(ROOT / "src" / "g2_cell_132.bin")),
        engine_133_instrumented=dict(
            file="src/g2_cell_133.c", sha256=sha(ce133),
            binary_sha256=sha(ROOT / "src" / "g2_cell_133_instr.bin"),
            inert_binary_sha256=sha(ROOT / "src" / "g2_cell_133.bin"),
            note="g2_cell_133.c is g2_cell_132.c plus -DINSTR counters; built WITHOUT "
                 "-DINSTR it reproduces the Round-125 controls node-for-node"),
        drivers=dict(closure_132=sha(ROOT / "src" / "g2_b_closure_132.py"),
                     residual_133=sha(ROOT / "src" / "verify_b_residual_133.py"),
                     finalize_133=sha(Path(__file__))),
        gcc="gcc -O2", target="TARGET=122",
        runs=runs)


def instr(path):
    s = re.sub(r",(\s*\])", r"\1", Path(path).read_text())
    d = json.loads(s)
    agg = Counter()
    for r in d["by_depth"]:
        for k, v in r.items():
            if k not in ("depth", "nodes", "children"):
                agg[k] += v
    busiest = sorted(d["by_depth"], key=lambda r: -r["nodes"])[:8]
    return dict(
        max_depth=d["max_depth"],
        block_exit_raw=d["block_exit_raw"],
        block_exit_distinct_coarse=d["block_exit_distinct_coarse"],
        block_exit_distinct_full=d["block_exit_distinct_full"],
        compression_coarse=(round(d["block_exit_raw"] / d["block_exit_distinct_coarse"], 3)
                            if d["block_exit_distinct_coarse"] else None),
        compression_full=(round(d["block_exit_raw"] / d["block_exit_distinct_full"], 3)
                          if d["block_exit_distinct_full"] else None),
        death_census=dict(agg.most_common()),
        busiest_depths=[(r["depth"], r["nodes"]) for r in busiest],
        deep_tail={str(r["depth"]): r["nodes"] for r in d["by_depth"] if r["depth"] >= 88},
        reject_totals=dict(sorted(d["reject_totals"].items(), key=lambda kv: -kv[1])[:8]))


def main():
    res = json.loads((OUT / "rr_b_residual_133.json").read_text())
    b11 = instr(OUT / "rr_b_instr_133_b11.json")
    b33 = instr(OUT / "rr_b_instr_133_b33.json")
    bct = res["block_collision_theorem"]
    rep = dict(
        round=133, cell="(k,G) = (4,2)", outer_axis="G (never F)",
        headline=(
            "Theorem 133.1 (block collision) kills 32 of the 150 type-B classes with no "
            "search at all - including B_e1_b11_P1b, the class Round 132 closed with "
            "30,124,862,589 nodes.  But the residual block-exit state is essentially "
            "INCOMPRESSIBLE (full signature compression 1.000x), so no residual DP is "
            "available and the 118 surviving classes remain a hard core."),
        theorem_133_1=bct,
        n4_collision_control=res["n4_collision_control"],
        macros=dict(beta=res["beta_macro"]["macro"], alpha=res["alpha_macro"]["half_macro"],
                    model_T=res["model_t_macro"]["constraint"]),
        instrumentation=dict(
            dead_block_class_b11=b11, live_block_class_b33=b33,
            interpretation=(
                "on the analytically dead class b11 the search NEVER completes the short "
                "block in 2e9 nodes (block_exit_raw = 0), which is exactly what Theorem "
                "133.1 predicts; on the live class b33 the block completes 2,419,969 times "
                "but the FULL residual signature is distinct every single time")),
        compression=dict(
            raw_block_exit_states=b33["block_exit_raw"],
            distinct_coarse_signatures=b33["block_exit_distinct_coarse"],
            distinct_full_signatures=b33["block_exit_distinct_full"],
            coarse_reduction=b33["compression_coarse"],
            full_reduction=b33["compression_full"],
            target="10x", achieved=False,
            verdict=("the used-hexagon component of the residual state is essentially "
                     "incompressible: every block-exit state carries a distinct hexagon "
                     "fingerprint, so a block-exit DP would need one entry per DFS path")),
        ordpin_measurement=dict(
            with_pin=dict(nodes=30124862589, seconds=3261, verdict="UNSAT_COMPLETE"),
            without_pin=dict(nodes=41335694797, seconds=4691, verdict="UNSAT_COMPLETE"),
            node_reduction=round(41335694797 / 30124862589, 3),
            time_reduction=round(4691 / 3261, 3),
            verdict="a small constant factor - engineering value only, not a structural bound"),
        class_ledger=bct["class_ledger"],
        structural_reduction=round(150 / bct["class_ledger"]["round133_classes"], 3),
        target_reduction=10,
        sweep_launched=False,
        sweep_decision=("the measured structural reduction is 1.27x and the best "
                        "compression is 1.0x on the full signature, both far below the "
                        "10x bar, so the 150-class (now 118-class) sweep was NOT launched"),
        certificate=certificate(),
        cell_status=dict(A_e0="closed (Round 130)", B_e0="closed (Round 130)",
                         A_e1="closed (Round 131)",
                         B_e1="OPEN - hard core, 65 of 75 classes survive",
                         B_e2="OPEN - hard core, 53 of 75 classes survive"),
        cell_closed=False,
        claude_closed_outer_cells="9/55 (k,G) - NOT incremented",
        label="ROUND-133 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_Q2": "6396/6396", "NR6": "ASSUMED"},
        disclaimer="This project has not proved L6 >= 872")
    (OUT / "rr_b_133.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))

    m = OUT / "superpermutation_n6_master_status.json"
    d = json.loads(m.read_text())
    d["round_133_B_residual_obstruction"] = {
        k: rep[k] for k in ("round", "cell", "outer_axis", "headline", "theorem_133_1",
                            "n4_collision_control", "macros", "compression",
                            "ordpin_measurement", "class_ledger", "structural_reduction",
                            "sweep_launched", "sweep_decision", "certificate",
                            "cell_status", "cell_closed", "claude_closed_outer_cells",
                            "label", "ledger", "disclaimer")}
    m.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(dict(keys=len(d), classes=rep["class_ledger"],
                          reduction=rep["structural_reduction"],
                          compression_full=rep["compression"]["full_reduction"],
                          ordpin=rep["ordpin_measurement"]["node_reduction"],
                          cell_closed=rep["cell_closed"]), indent=1))


if __name__ == "__main__":
    main()
