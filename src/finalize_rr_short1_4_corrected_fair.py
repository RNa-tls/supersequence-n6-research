#!/usr/bin/env python3
"""Verify and document a completed Round-50 v5 fair-pilot result.

This utility is read-only with respect to all v5 branch checkpoints: it only
reads completed aggregate files, calls the independent verifier, and writes
the requested reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=ROOT / "outputs" / "rr_short1_4_corrected_fair_results.json")
    parser.add_argument("--classes", type=Path, default=ROOT / "outputs" / "rr_short1_4_target_a_classes.json")
    parser.add_argument("--profiles", type=Path, default=ROOT / "outputs" / "rr_short5_cross_root_profiles.json")
    parser.add_argument("--verified", type=Path, default=ROOT / "outputs" / "rr_short1_4_corrected_fair_verified.json")
    args = parser.parse_args()
    result_path, classes_path, profiles_path, verified_path = (path.resolve() for path in (args.result, args.classes, args.profiles, args.verified))
    if not all(path.exists() for path in (result_path, classes_path, profiles_path)):
        raise SystemExit("completed v5 result/classes/profiles are required before finalization")
    subprocess.run([
        sys.executable, str(ROOT / "src" / "verify_rr_short1_4_corrected_fair.py"),
        "--result", str(result_path), "--classes", str(classes_path), "--profiles", str(profiles_path),
        "--output", str(verified_path),
    ], cwd=ROOT, check=True)
    result, classes, profiles, verified = map(read_json, (result_path, classes_path, profiles_path, verified_path))
    if verified.get("status") != "VERIFIED_CAPPED_PILOTS":
        raise AssertionError("verification failure; reports not written")

    rows = {str(row["root_id"]): row for row in profiles["roots"]}
    table = []
    failures = []
    for root_id in sorted(rows):
        row = rows[root_id]
        telemetry = row["telemetry"]
        total_expanded = sum(int(branch["expanded"]) for branch in row["fair_branches"])
        total_frontier = sum(int(branch["frontier_size"]) for branch in row["fair_branches"])
        table.append(
            f"| `{root_id}` | {row['admitted_R1_children']} | {total_expanded} | {total_frontier} | "
            f"{telemetry['legal_repair_events']} | {telemetry['repaired_R2_paths']} | "
            f"{telemetry['literal_Target_A_hits']} | `{row['status']}` |"
        )
        top = sorted(telemetry["failure_taxonomy"].items(), key=lambda pair: (-pair[1], pair[0]))[:4]
        failures.append(f"- `{root_id}`: " + (", ".join(f"{kind}={count}" for kind, count in top) or "no R2 failure record"))
    class_table = []
    for item in classes["canonical_state_classes"]:
        class_table.append(
            f"| `{item['canonical_state_hash'][:16]}` | {item['literal_witness_count']} | "
            f"{item['known18_comparison']['classification']} | `{item['target_b']['status']}` |"
        )
    if not class_table:
        class_table.append("| — | 0 | — | — |")

    provenance = "\n".join([
        f"- `{path.relative_to(ROOT)}` — SHA-256 `{sha256_file(path)}`"
        for path in (result_path, classes_path, profiles_path, verified_path)
    ])
    pilots_doc = f"""# Round 50 — corrected fair pilots for `short_ell1`–`short_ell4`

## Scope

This is a **bounded observational pilot**, not an exhaustion claim.  The
admission traversal spent `{result['admission_budget_per_root']}` pre-R
expansions per bare root.  Every observed R1 provenance child then received
the equal positive cap `{result['budget_per_R1_child']}` in a distinct v5
checkpoint.  A nonempty frontier is always `INCOMPLETE` for absence purposes.

The v5 schema is `{result['checkpoint_schema']}`; its recognizer is
`{result['recognizer_semantics']}`.  Literal R2 source-sensitive predicates
consume `edge.run.state`; the run uses Target-A-safe pruning only.

Independent verification returned `{verified['status']}` and replayed
`{verified['literal_Target_A_hits_replayed']}` literal Target-A hit(s).

## Per-root telemetry

| root | observed R1 children | expansions | frontier | repairs | repaired R2 paths | literal Target-A hits | bounded status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

The per-child fair-budget assertion is `{result['equal_budget_verified']}`.
Different roots can have different total work because they can have different
numbers of admitted R1 provenance children.

## Target-A to Target-B ledger

Literal witness count: `{classes['counts']['literal_Target_A_hits']}`.
Exact decorated boundary states: `{classes['counts']['exact_decorated_boundary_states']}`.
Canonical boundary classes: `{classes['counts']['canonical_state_classes']}`.
New canonical classes: `{classes['counts']['new_state_classes']}`.

| canonical boundary | literal multiplicity | known-18 comparison | helper-free Target-B disposition |
| --- | ---: | --- | --- |
{chr(10).join(class_table)}

## Reproducibility

{provenance}

- pilot driver SHA-256: `{result['driver_sha256']}`
- exact engine SHA-256: `{result['engine_sha256']}`
- checkpoint schema: `{result['checkpoint_schema']}`

No frequency reported here is a theorem or an exhaustion result.
"""
    comparison_doc = f"""# Round 50 — corrected cross-root comparison

## Scope

This compares only the v5 admission and equal-cap pilot prefixes for
`short_ell1`–`short_ell4`.  It does not deepen `short_ell0`, and a capped
branch is not an exclusion.

## Dominant observed R2-failure mechanisms

{chr(10).join(failures)}

## Cross-root descriptors

```json
{json.dumps(profiles['cross_root'], sort_keys=True, indent=2)}
```

The displayed frequencies are descriptive, not a theorem.  All R2
source-sensitive checks use the tagged literal joint source; canonical known-18
comparison uses only proved left-`S_6` symmetry.  Any future continuation must
resume the saved v5 branch-local checkpoint, not infer closure from this
pilot.
"""
    (ROOT / "research" / "RR_SHORT1_4_CORRECTED_FAIR_PILOTS_CODEX.md").write_text(pilots_doc, encoding="utf-8")
    (ROOT / "research" / "RR_SHORT5_CROSS_ROOT_COMPARISON_CODEX.md").write_text(comparison_doc, encoding="utf-8")
    print(json.dumps({"status": "FINALIZED_VERIFIED_CAPPED_PILOTS", "roots": sorted(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
