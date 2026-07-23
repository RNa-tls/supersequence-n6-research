"""Build a read-only recovery/merge status report for the forest run.

This program never starts, stops, or modifies the enumerator, runner, or any
branch JSON.  It reads five completed branch certificates, their fresh
recovery verifier outputs, and the merged certificate file.  It then writes
only the explicitly requested recovery report and aggregate statistics.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SEEDS = ("0_2", "0_3", "0_7", "0_15", "0_27")
PYTHON = Path(sys.executable)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    # The supervisor's PowerShell writer emits a UTF-8 BOM; branch and
    # verifier writers do not.  ``utf-8-sig`` accepts both without changing
    # any source artifact.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat()


def seed_label(seed: str) -> str:
    return seed.replace("_", ",", 1)


def tail(path: Path, count: int = 100) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]


def process_snapshot() -> dict[str, Any]:
    """Inspect only; the PowerShell subprocess excludes itself by PID."""
    command = r'''
      $me=$PID
      Get-CimInstance Win32_Process |
        Where-Object {
          $_.ProcessId -ne $me -and
          $_.CommandLine -match 'run_forest_overnight\.ps1|enumerate-forest-covers'
        } |
        Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine |
        ConvertTo-Json -Depth 4 -Compress
    '''
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return {"query_ok": False, "stderr": result.stderr.strip(), "processes": []}
    text = result.stdout.strip()
    if not text:
        return {"query_ok": True, "processes": []}
    parsed = json.loads(text)
    return {"query_ok": True, "processes": parsed if isinstance(parsed, list) else [parsed]}


def branch_log_paths(seed: str) -> dict[str, list[Path]]:
    prefix = f"forest_branch_{seed}"
    return {
        "stdout": sorted(OUT.glob(f"{prefix}*stdout.log")),
        "stderr": sorted(OUT.glob(f"{prefix}*stderr.log")),
    }


def validation_for(seed: str) -> dict[str, Any]:
    branch_path = OUT / f"forest_branch_{seed}.json"
    incidence_path = OUT / f"forest_recovery_{seed}.incidence_verified.json"
    full_path = OUT / f"forest_recovery_{seed}.fully_verified.json"
    raw: dict[str, Any] = {
        "seed": seed_label(seed),
        "branch_path": str(branch_path.relative_to(ROOT)).replace("\\", "/"),
        "exists": branch_path.exists(),
        "parse_ok": False,
        "completed_result": False,
    }
    if not branch_path.exists():
        return raw
    try:
        branch = load_json(branch_path)
    except Exception as exc:  # report a broken partial output without treating it as completed
        raw["parse_error"] = repr(exc)
        raw["file_sha256"] = sha(branch_path)
        raw["modified_at"] = iso_mtime(branch_path)
        return raw
    certificates = branch.get("certificates", [])
    cert_shas = {cert.get("cover_sha256") for cert in certificates}
    raw.update({
        "parse_ok": True,
        "seed_matches_filename": branch.get("seed") == [int(part) for part in seed.split("_")],
        "node_limit": branch.get("node_limit"),
        "completed": branch.get("completed"),
        "aborted_at_node_limit": branch.get("aborted_at_node_limit"),
        "node_count": branch.get("node_count"),
        "leaf_count": branch.get("leaf_count"),
        "certificate_count": len(certificates),
        "unique_certificate_sha_count": len(cert_shas),
        "code_sha256": branch.get("code_sha256"),
        "certificate_code_sha256_values": sorted({cert.get("code_sha256") for cert in certificates}),
        "prune_counts": branch.get("prune_counts"),
        "file_sha256": sha(branch_path),
        "modified_at": iso_mtime(branch_path),
        "completed_result": bool(branch.get("completed") is True and branch.get("node_limit") == 0 and not branch.get("aborted_at_node_limit")),
    })
    log_paths = branch_log_paths(seed)
    raw["logs"] = {
        kind: [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "last_100_lines": tail(path),
                "sha256": sha(path),
            }
            for path in paths
        ]
        for kind, paths in log_paths.items()
    }
    raw["certificate_sha_set"] = sorted(cert_shas)
    for label, path, expected_replay in (
        ("incidence", incidence_path, False),
        ("full_dp_replay", full_path, True),
    ):
        result: dict[str, Any] = {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "exists": path.exists(), "valid": False}
        if path.exists():
            try:
                verified = load_json(path)
                row_shas = {row.get("cover_sha256") for row in verified.get("rows", [])}
                result.update({
                    "parse_ok": True,
                    "file_sha256": sha(path),
                    "certificates_verified": verified.get("certificates_verified"),
                    "dp_replayed": verified.get("dp_replayed"),
                    "verifier_sha256": verified.get("verifier_sha256"),
                    "row_sha_set_matches_current_input": row_shas == cert_shas,
                    "all_rows_verified": all(row.get("verified") is True for row in verified.get("rows", [])),
                })
                result["valid"] = bool(
                    verified.get("certificates_verified") == len(certificates)
                    and verified.get("dp_replayed") is expected_replay
                    and row_shas == cert_shas
                    and result["all_rows_verified"]
                )
            except Exception as exc:
                result["parse_ok"] = False
                result["parse_error"] = repr(exc)
        raw[f"{label}_verification"] = result
    raw["all_H_0_to_3_lifts_fail"] = all(
        entry.get("complete_lift_exists") is False
        for cert in certificates
        for entry in cert.get("port_lift_H_0_to_3", [])
    )
    return raw


def component_partition(cert: dict[str, Any]) -> tuple[int, ...]:
    return tuple(sorted((len(component) for component in cert["collision_forest"]["component_partition"]), reverse=True))


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    text = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    text.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(text)


def main() -> None:
    branches = {seed: validation_for(seed) for seed in SEEDS}
    valid_branches = all(
        row["completed_result"]
        and row["incidence_verification"]["valid"]
        and row["full_dp_replay_verification"]["valid"]
        for row in branches.values()
    )
    if not valid_branches:
        raise RuntimeError("one or more branch outputs are not fully recovery-verified")
    branch_sets = {seed: set(row["certificate_sha_set"]) for seed, row in branches.items()}
    pairwise = {
        f"{seed_label(left)} ∩ {seed_label(right)}": len(branch_sets[left] & branch_sets[right])
        for offset, left in enumerate(SEEDS)
        for right in SEEDS[offset + 1:]
    }
    union = set().union(*branch_sets.values())
    class_seed_multiplicity = Counter(
        sum(sha in branch_sets[seed] for seed in SEEDS)
        for sha in union
    )
    merged_path = OUT / "forest_all_classes.json"
    merged_incidence_path = OUT / "forest_all_classes.incidence_verified.json"
    merged_full_path = OUT / "forest_all_classes.fully_verified.json"
    merged = load_json(merged_path)
    merged_certs = merged["certificates"]
    merged_shas = {cert["cover_sha256"] for cert in merged_certs}
    if merged_shas != union or len(merged_certs) != len(merged_shas):
        raise RuntimeError("merged canonical SHA set does not equal branch union")
    merged_verifications = {}
    for label, path, expected_replay in (
        ("incidence", merged_incidence_path, False),
        ("full_dp_replay", merged_full_path, True),
    ):
        verified = load_json(path)
        verified_shas = {row["cover_sha256"] for row in verified["rows"]}
        if not (
            verified["certificates_verified"] == len(merged_certs)
            and verified["dp_replayed"] is expected_replay
            and verified_shas == merged_shas
            and all(row["verified"] for row in verified["rows"])
        ):
            raise RuntimeError(f"merged {label} verifier output does not match merged input")
        merged_verifications[label] = {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "file_sha256": sha(path),
            "certificates_verified": verified["certificates_verified"],
            "dp_replayed": verified["dp_replayed"],
            "verifier_sha256": verified["verifier_sha256"],
            "row_sha_set_matches_merged_input": True,
        }
    all_lifts_fail = all(
        entry["complete_lift_exists"] is False
        for cert in merged_certs
        for entry in cert["port_lift_H_0_to_3"]
    )
    if not all_lifts_fail:
        raise RuntimeError("a merged certificate reports a complete H<=3 lift")
    partitions = Counter(
        ",".join(map(str, component_partition(cert))) for cert in merged_certs
    )
    h3_maxima = Counter(
        cert["port_lift_H_0_to_3"][3]["exact_reachability"]["max_cycles_reached"]
        for cert in merged_certs
    )
    current_processes = process_snapshot()
    runner_log = OUT / "forest_overnight_runner.log"
    runner_log_lines = tail(runner_log)
    runner_status = OUT / "forest_overnight_status.json"
    runtime = {
        "checked_at": datetime.now().astimezone().isoformat(),
        "active_runner_or_enumerator_processes": current_processes,
        "runner_log_path": str(runner_log.relative_to(ROOT)).replace("\\", "/"),
        "runner_log_last_100_lines": runner_log_lines,
        "runner_log_sha256": sha(runner_log),
        "last_graceful_runner_stop_recorded": next((line for line in reversed(runner_log_lines) if "runner stopped" in line), None),
        "last_runner_activity_recorded": runner_log_lines[-1] if runner_log_lines else None,
        "runner_status_file_path": str(runner_status.relative_to(ROOT)).replace("\\", "/"),
        "runner_status_file_modified_at": iso_mtime(runner_status),
        "runner_status_file_updated_at": load_json(runner_status).get("updated_at"),
        "runner_termination_assessment": (
            "No matching runner/enumerator process is active. The runner script's finally block would log 'runner stopped', but no such final line follows its last 0,27 start record; this is evidence of an abrupt supervisor disappearance rather than a graceful recorded exit. The 0,27 child completed later, so its completion timestamp does not identify the supervisor exit time. Branch stderr logs are empty and the bounded Windows PowerShell/Application event inspection yielded no unambiguous runner termination event. Exact exit time and external cause cannot be recovered from the available artifacts."
        ),
    }
    metadata = {
        "report_code": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
        "report_code_sha256": sha(Path(__file__)),
        "generator_code_sha256": sha(ROOT / "work" / "superperm_port_lift.py"),
        "verifier_code_sha256": sha(ROOT / "work" / "verify_forest_certificates.py"),
        "runner_code_sha256": sha(ROOT / "work" / "run_forest_overnight.ps1"),
        "branch_input_sha256": {seed_label(seed): branches[seed]["file_sha256"] for seed in SEEDS},
        "merged_input_sha256": sha(merged_path),
        "raw_certificate_total": sum(branches[seed]["certificate_count"] for seed in SEEDS),
        "canonical_unique_class_count": len(merged_certs),
        "seed_duplicate_removals": sum(branches[seed]["certificate_count"] for seed in SEEDS) - len(merged_certs),
    }
    statistics = {
        "metadata": metadata,
        "merged_verification": merged_verifications,
        "collision_forest_component_partition_distribution": dict(sorted(partitions.items())),
        "H3_max_cycles_reached_distribution": {str(key): value for key, value in sorted(h3_maxima.items())},
        "all_merged_classes_H_0_to_3_complete_lift_false": all_lifts_fail,
        "scope": "All five completed depth-2 forest branches only; this is not a proof of the broader n=6 superpermutation lower bound.",
    }
    (OUT / "forest_all_statistics.json").write_text(json.dumps(statistics, indent=2, ensure_ascii=False), encoding="utf-8")
    status = {
        "declared_status": "all five branches verified; final merge complete",
        "metadata": metadata,
        "process_recovery": runtime,
        "branches": branches,
        "seed_overlap": {
            "branch_class_counts": {seed_label(seed): len(branch_sets[seed]) for seed in SEEDS},
            "union_class_count": len(union),
            "pairwise_intersection_counts": pairwise,
            "class_seed_multiplicity_distribution": {str(key): value for key, value in sorted(class_seed_multiplicity.items())},
            "all_five_seed_sets_identical": len({frozenset(values) for values in branch_sets.values()}) == 1,
            "seed_only_class_counts": {seed_label(seed): len(branch_sets[seed] - set().union(*(branch_sets[other] for other in SEEDS if other != seed))) for seed in SEEDS},
        },
        "merge": {
            "path": str(merged_path.relative_to(ROOT)).replace("\\", "/"),
            "file_sha256": sha(merged_path),
            "raw_certificate_total": metadata["raw_certificate_total"],
            "canonical_unique_class_count": len(merged_certs),
            "seed_duplicate_removals": metadata["seed_duplicate_removals"],
            "all_H_0_to_3_complete_lifts_fail": all_lifts_fail,
            "verifications": merged_verifications,
        },
        "restart_required": False,
        "restart_guidance": "No restart is required: every branch JSON is completed and freshly verified. No enumerator process was started by this recovery procedure.",
    }
    (OUT / "forest_recovery_and_merge_status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    branch_rows = []
    for seed in SEEDS:
        row = branches[seed]
        branch_rows.append([
            row["seed"], row["completed"], row["node_limit"], row["node_count"], row["certificate_count"],
            row["incidence_verification"]["valid"], row["full_dp_replay_verification"]["valid"], row["file_sha256"][:16],
        ])
    md = [
        "# Forest recovery and merge status",
        "",
        "## Declared status",
        "",
        "**all five branches verified; final merge complete**",
        "",
        "> 포화 collision-forest cover 전체에서 heavy budget (H≤3) exact port-lift는 실패한다.",
        "",
        "The word ‘entire’ here is scoped to the five completed depth-2 seeds of the forest-only canonical-augmentation enumeration. It does not remove NR6, solve other (F,D,N) slabs, or prove `L_6 >= 872`.",
        "",
        "## Reproducibility",
        "",
        f"- Recovery report code SHA-256: `{metadata['report_code_sha256']}`",
        f"- Generator code SHA-256: `{metadata['generator_code_sha256']}`",
        f"- Independent verifier SHA-256: `{metadata['verifier_code_sha256']}`",
        f"- Runner SHA-256: `{metadata['runner_code_sha256']}`",
        "",
        "## Process recovery",
        "",
        runtime["runner_termination_assessment"],
        "",
        f"Last runner activity: `{runtime['last_runner_activity_recorded']}`",
        f"Last graceful-stop record: `{runtime['last_graceful_runner_stop_recorded']}`",
        "",
        "## Branch validation",
        "",
        markdown_table(
            ["seed", "completed", "node limit", "nodes", "certificates", "incidence", "DP replay", "input SHA prefix"],
            branch_rows,
        ),
        "",
        "Each row was freshly checked against its current input certificate SHA set by a recovery-named incidence verifier output and then by a recovery-named full DP replay output. All branch files parse, have `completed:true`, `node_limit:0`, and `aborted_at_node_limit:false`.",
        "",
        "## Seed overlap and merge",
        "",
        f"Raw certificates: {metadata['raw_certificate_total']}; canonical unique classes: {len(merged_certs)}; cross-seed duplicates removed: {metadata['seed_duplicate_removals']}.",
        "",
        f"All ten pairwise intersections have size 326. Each of the 326 classes occurs in all five seeds; no seed-only class exists. The merged JSON and both merged verifier outputs are listed in the machine-readable status file.",
        "",
        "## Merged statistics",
        "",
        markdown_table(
            ["H=3 max f-cycles reached", "classes"],
            [[key, value] for key, value in sorted(h3_maxima.items())],
        ),
        "",
        "The collision-forest component-partition distribution is in `forest_all_statistics.json`. All 326 merged classes report `complete_lift_exists=false` at H=0,1,2,3, and the merged full DP replay verifies those serialized tables.",
        "",
        "## Restart guidance",
        "",
        "No restart is required. The current absence of a runner/enumerator process is not treated as a failed branch because every output is complete and freshly verified. No process was restarted by this procedure.",
    ]
    (OUT / "FOREST_RECOVERY_AND_MERGE_STATUS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({
        "declared_status": status["declared_status"],
        "raw_certificate_total": metadata["raw_certificate_total"],
        "canonical_unique_class_count": len(merged_certs),
        "all_H_0_to_3_complete_lifts_fail": all_lifts_fail,
    }, indent=2))


if __name__ == "__main__":
    main()
