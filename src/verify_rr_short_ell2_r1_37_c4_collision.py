#!/usr/bin/env python3
"""Independent certificate checks for the Round-60 C4 collision audit."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import analyze_rr_short_ell2_r1_37_fz1_candidates as fz1


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
LEDGER = OUT / "rr_short_ell2_r1_37_c4_collision_ledger.json"
CLASSES = OUT / "rr_short_ell2_r1_37_c4_collision_classes.json"
TOUCH = OUT / "rr_short_ell2_r1_37_c4_first_touch_audit.json"
CLOSURE = OUT / "rr_short_ell2_r1_37_c4_predecessor_closure.json"
ROUND59 = OUT / "rr_short_ell2_r1_37_fz1_condition_ledger.json"
MANIFEST = OUT / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
VERIFIED = OUT / "rr_short_ell2_r1_37_c4_verified.json"

exact, core = fz1.exact, fz1.core


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def verify_representative(row: dict[str, object]) -> None:
    source = tuple(int(x) for x in row["literal_joint_source"])
    target = tuple(int(x) for x in row["collided_permutation"])
    move_by_label = {move.label: move for move in exact.ALL_MOVES}
    move = move_by_label[str(row["attempted_joint"])]
    if move.weight != 3 or core.word_after(source, move.action) != target:
        raise AssertionError("representative joint action does not reproduce collided target")
    q, phase = exact.ORBIT_PHASE[target]
    h, hpos = exact.HEX_POSITION[target]
    if (int(q), int(phase), int(h), int(hpos)) != (
        int(row["candidate_orbit"]), int(row["candidate_phase"]),
        int(row["target_hexagon"]), int(row["target_hex_position"]),
    ):
        raise AssertionError("representative fixed-table coordinate mismatch")
    joint_mask = int(row["target_hex_mask_at_joint_source"])
    macro_mask = int(row["target_hex_mask_at_macro_entry"])
    bit = 1 << int(hpos)
    if not (joint_mask & bit):
        raise AssertionError("claimed collided target bit is absent at literal joint source")
    expected = "K0" if macro_mask & bit else "K5"
    if row["mechanism_family"] != expected:
        raise AssertionError("K0/K5 classification disagrees with exact masks")
    if row["engine_rejection"] != "exact_permutation_collision":
        raise AssertionError("foreign engine rejection semantics")
    if int(row["candidate_registration_mask_before"]) != 0 or row["candidate_previously_registered"]:
        raise AssertionError("C4 representative is not a fresh candidate registration")


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    classes = json.loads(CLASSES.read_text(encoding="utf-8"))
    touch = json.loads(TOUCH.read_text(encoding="utf-8"))
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    round59 = json.loads(ROUND59.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total = int(ledger["C4_attempts"])
    expected = sum(int(row["level_counts"]["C4"]) for row in round59["per_candidate"])
    if total != 253537 or total != expected:
        raise AssertionError("Round-59/C4 total conservation failed")
    if sum(int(row["C4_attempt_count"]) for row in ledger["candidate_rows"]) != total:
        raise AssertionError("candidate ledger does not conserve attempts")
    if sum(int(value) for value in ledger["mechanism_histogram"].values()) != total:
        raise AssertionError("mechanism taxonomy is not exhaustive")
    if sum(int(value) for value in touch["classification"].values()) != total:
        raise AssertionError("first-touch taxonomy is not exhaustive")
    exact_rows = classes["exact_signatures"]
    canonical_rows = classes["left_s6_canonical_signatures"]
    if len(exact_rows) != int(ledger["exact_collision_signatures"]):
        raise AssertionError("exact signature count mismatch")
    if len(canonical_rows) != int(ledger["left_s6_canonical_collision_signatures"]):
        raise AssertionError("canonical signature count mismatch")
    if sum(int(row["count"]) for row in exact_rows) != total:
        raise AssertionError("exact signature multiplicities do not conserve attempts")
    if sum(int(row["count"]) for row in canonical_rows) != total:
        raise AssertionError("canonical signature multiplicities do not conserve attempts")
    for row in exact_rows:
        verify_representative(row["representative"])
    for row in canonical_rows:
        verify_representative(row["representative"])
    root_histograms = {str(h): Counter() for h in (40, 82, 90, 91, 92)}
    for record in manifest["start_domain"]["records"]:
        sparse = {int(index): int(mask) for index, mask in record["state"]["hex_masks"]}
        for h in root_histograms:
            root_histograms[h][str(sparse.get(int(h), 0))] += 1
    normalized = {h: dict(sorted(values.items(), key=lambda item: int(item[0]))) for h, values in root_histograms.items()}
    if normalized != closure["root_hex_mask_histograms"]:
        raise AssertionError("root full-hex certificate mismatch")
    if closure["complete_finite_C4_prerequisite_closure"]:
        raise AssertionError("observed predecessor closure was improperly promoted to T2+")
    result = {
        "schema": "rr-short-ell2-r1-37-c4-collision-verified-v1",
        "verified": True,
        "verification_scope": [
            "count conservation against the independent Round-59 C4 ledger",
            "every exact and left-S6 representative's literal action/target/orbit/phase/hex bit",
            "K0/K5 exact mask classification and fresh-registration prerequisite",
            "all 84 root hex-mask rows and theorem-level non-promotion",
        ],
        "counts": {
            "C4_attempts": total, "exact_signatures": len(exact_rows),
            "left_s6_canonical_signatures": len(canonical_rows),
            "mechanism_histogram": ledger["mechanism_histogram"],
            "first_touch_histogram": touch["classification"],
        },
        "theorem_level": closure["theorem_level"],
        "input_sha256": {path.name: sha256_file(path) for path in (LEDGER, CLASSES, TOUCH, CLOSURE, ROUND59, MANIFEST)},
        "verifier_sha256": sha256_file(Path(__file__)),
    }
    atomic_json(VERIFIED, result)
    print(json.dumps(result["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
