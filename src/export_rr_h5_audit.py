#!/usr/bin/env python3
"""라운드 108 §17 — **H5 감사 패키지**를 내보낸다.

역사적 파이프라인 없이도 (H5) 를 독립 감사할 수 있는 최소 묶음:

    h5_manifest.json          (H5) 의 정확한 서술 · H 갱신 정리 · 비용표 · 재현 명령
    tail_generator.json       550개 indecomposable tail 전부 (weight, 오른쪽 작용, 비용)
    conditional_states.json   라운드-107 조건부 1,353 상태의 sid 목록
    robust_states.json        joint weight 무관하게 배제된 5,043 상태의 sid 목록

사용법:
    python3 src/export_rr_h5_audit.py
"""

from __future__ import annotations

import gzip
import importlib.util as iu
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "rr_h5_audit"


def _load(name, path):
    spec = iu.spec_from_file_location(name, path)
    mod = iu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FJ = _load("certify_rr_full_joint", ROOT / "src" / "certify_rr_full_joint.py")
C = FJ.C
core = FJ.core


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tails = [{"weight": w, "action": list(a), "budget_cost": FJ.cost_of(w)}
             for w, a in FJ.TAILS]
    rot = [{"weight": 1, "action": list(core.SIGMA), "budget_cost": 0,
            "note": "회전 — joint 가 아니다"}]
    (OUT / "tail_generator.json").write_text(json.dumps({
        "schema": "rr_h5_audit/tails/1",
        "count_by_weight": dict(sorted(Counter(t["weight"] for t in tails).items())),
        "total_including_rotation": len(tails) + 1,
        "cost_formula": "cost(w) = [w >= 3] + max(w - 3, 0)",
        "cost_by_weight": {str(w): FJ.cost_of(w) for w in range(1, 7)},
        "rotation": rot, "joints": tails,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    with gzip.open(ROOT / "outputs" / "rr_q2_no_hall_certificate.jsonl.gz", "rt") as fh:
        fh.readline()
        rows = [json.loads(line) for line in fh]
    per = defaultdict(list)
    for r in rows:
        per[r["sid"]].append(r["reason"])
    cond = sorted(s for s, v in per.items() if not all(x == "root_bound" for x in v))
    rob = sorted(s for s, v in per.items() if all(x == "root_bound" for x in v))
    (OUT / "conditional_states.json").write_text(json.dumps({
        "schema": "rr_h5_audit/conditional/1", "count": len(cond),
        "definition": ("라운드-107 인증서에서 적어도 하나의 cover 가 뿌리 성분 하한만으로는 "
                       "닫히지 않은 상태 — 이 블록의 배제만이 (H5) 에 의존했다"),
        "sids": cond}, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "robust_states.json").write_text(json.dumps({
        "schema": "rr_h5_audit/robust/1", "count": len(rob),
        "definition": ("모든 cover 가 뿌리 성분 하한만으로 닫힌 상태 — joint weight 와 "
                       "무관하게 배제된다 (정리 R)"),
        "sids": rob}, ensure_ascii=False, indent=1), encoding="utf-8")

    manifest = {
        "schema": "rr_h5_audit/manifest/1", "round": 108,
        "H5_statements": {
            "H5-local": "이 상태들에서 weight >= 4 joint 는 합법적으로 일어날 수 없다",
            "H5-target": ("weight >= 4 joint 가 합법일 수는 있으나 목표를 만족하는 어떤 완성도 "
                          "그것을 포함하지 않는다"),
            "H5-replacement": ("무거운 joint 를 쓰는 목표 완성마다 최소 weight 완성으로의 "
                               "치환이 존재한다"),
            "needed_by_the_round_107_certificate": "H5-target (또는 그보다 강한 H5-local)",
        },
        "H_update_theorem": {
            "definition": "H = Σ_joint max(weight − 3, 0)",
            "monotone": "dH = max(w − 3, 0) >= 0 이므로 H 는 감소하지 못한다",
            "current_value_on_every_archived_state": 0,
            "allowed_final_value": "Ndef + H <= 3 (TARGET_BUDGET); H 자체는 <= 3 까지 허용",
            "is_area_A_defined_by_H_equals_0": ("Target A 인식기가 경계의 자식에 H == 0 을 "
                                                "요구하므로 **경계까지의 탐색**은 H = 0 으로 "
                                                "제한된다. 그러나 `final_target` 은 H <= 3 을 "
                                                "허용하므로 **경계 이후의 완성**에는 그 제한이 "
                                                "적용되지 않는다"),
            "therefore": "단순 단조성 경로로는 (H5) 가 따라 나오지 않는다",
        },
        "heavy_arc_budget_lemma": {
            "statement": ("s := B − L2(ROOT) 라 하면 예산 안의 임의 완성에서 "
                          "Σ_{무거운 호} (cost − 1) <= s"),
            "proof": ("총비용 = (비-무료 호 개수) + Σ(cost−1) 이고 비-무료 호 개수 >= L2, "
                      "총비용 <= B 이므로"),
            "corollary": "s = 0 이면 무거운 joint 를 하나도 쓸 수 없다 — 그 인스턴스에서 H5 는 정리다",
        },
        "reproduce": [
            "python3 src/certify_rr_full_joint.py --conditional",
            "python3 src/probe_rr_heavy_joint_literal.py --states 40",
            "python3 src/probe_rr_heavy_dominance.py --states 60",
        ],
        "files": ["tail_generator.json", "conditional_states.json", "robust_states.json",
                  "../rr_full_joint_certificate.json", "../rr_full_joint_rows.jsonl.gz",
                  "../rr_heavy_joint_literal.json", "../rr_heavy_dominance.json"],
        "disclaimer": "This project has not proved L6 >= 872.",
    }
    (OUT / "h5_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
