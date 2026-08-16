#!/usr/bin/env python3
"""라운드 103 — 구체 Hamilton SAT 증인을 **literal 엔진**으로 재생한다.

라운드 102 는 구체 단어 배정 그래프에서 rooted Hamilton 경로 22개를 찾았다.  그것은
`WORD_NEXT` 호환성만 확인한 것이고, 실제 엔진의 상태 갱신(방문 창 무반복, port 재등록 금지,
`F/S/H`, `O/P/D`, fragment 타이밍)은 검사하지 않았다.

이 모듈은 **진짜 엔진**(`legacy_research/work/superperm_partial_f1.py` 의 `ExactState`/
`extend`)을 그대로 구동한다.  각 pass 를 `ℓ` 번의 회전(weight 1) + joint(weight ≥ 2)로
전개하고, `extend` 가 `None` 을 돌려주면(= 반복 창) 또는 `AssertionError`(= port 재등록)를
던지면 그 지점이 **첫 literal 발산**이다.

즉 이 재생은 모델이 빠뜨린 제약을 사후에 추가하는 것이 아니라, 엔진 자신에게 물어보는 것이다.

사용법:
    python3 src/replay_rr_literal_engine.py            # 22개 증인 재생
    python3 src/replay_rr_literal_engine.py --controls # 엔진이 만든 합법 사슬 양성 대조
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
OUT = ROOT / "outputs"

_spec = importlib.util.spec_from_file_location(
    "superperm_partial_f1", ROOT / "legacy_research" / "work" / "superperm_partial_f1.py")
ENG = importlib.util.module_from_spec(_spec)
sys.modules["superperm_partial_f1"] = ENG
_spec.loader.exec_module(ENG)
core = ENG.core

ROT = next(m for m in ENG.ALL_MOVES if m.weight == 1)
JOINTS = tuple(m for m in ENG.ALL_MOVES if m.weight >= 2)


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


def load_states():
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    return {s["sid"]: s for s in states}


def load_geometry():
    _h, geo = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    return {g["id"]: g for g in geo}


def exact_state(record):
    """아카이브 상태 레코드를 엔진의 `ExactState` 로 복원한다."""
    return ENG.ExactState(
        p=tuple(int(c) for c in record["p"]),
        hex_masks=tuple(record["hex_masks"]),
        orbit_masks=tuple(record["orbit_masks"]),
        F=record["F"], S=record["S"], H=record["H"])


def snapshot(state):
    return {"p": "".join(map(str, state.p)), "F": state.F, "S": state.S, "H": state.H,
            "P": state.P, "O": state.O, "D": state.D,
            "visited": state.visited_count, "current_hex": state.current_hex}


def replay_pass(state, ell, target_perm, trace):
    """`ℓ` 회전 + 목표 단어로 가는 joint 하나.  실패 시 `(None, 사유)`."""
    cur = state
    for step in range(ell):
        tr = ENG.extend(cur, ROT)
        if tr is None:
            return None, {"stage": "rotation", "rotation_step": step,
                          "reason": "A_visited_rotation_window",
                          "blocked_word": "".join(map(str, core.word_after(cur.p, ROT.action)))}
        cur = tr.state
    chosen = None
    for mv in JOINTS:
        if core.word_after(cur.p, mv.action) == target_perm:
            chosen = mv
            break
    if chosen is None:
        return None, {"stage": "joint", "reason": "G_no_joint_reaches_target",
                      "from": "".join(map(str, cur.p)),
                      "target": "".join(map(str, target_perm))}
    try:
        tr = ENG.extend(cur, chosen)
    except AssertionError as exc:
        return None, {"stage": "joint", "reason": "D_registration_reuse", "detail": str(exc)}
    if tr is None:
        return None, {"stage": "joint", "reason": "A_visited_joint_word",
                      "target": "".join(map(str, target_perm))}
    trace.append({"ell": ell, "joint": chosen.label,
                  "target": "".join(map(str, target_perm)),
                  "abandonment": tr.abandonment, "new_orbit": tr.new_orbit,
                  "dF": tr.delta_F, "dS": tr.delta_S, "dH": tr.delta_H})
    return tr.state, None


def replay_witness(record, witness, geo):
    """§1 — 증인 전체를 엔진으로 재생한다."""
    state = exact_state(record)
    start = snapshot(state)
    trace = []
    words = witness["word_order"]
    ells = witness["ell_sequence"]
    obligations = witness["obligation_order"]
    # ROOT 에서 첫 pass 는 ℓ=5 로 출발한다 (감사된 규칙).
    ell_in = 5
    for i, wid in enumerate(words):
        target = tuple(int(c) for c in geo[wid]["word"])
        nxt, why = replay_pass(state, ell_in, target, trace)
        if nxt is None:
            return {"verdict": "LITERAL_REPLAY_FAIL", "failed_step": i,
                    "failed_obligation": obligations[i], "failed_word": geo[wid]["word"],
                    "detail": why, "steps_replayed": len(trace),
                    "start": start, "at_failure": snapshot(state)}
        state = nxt
        ell_in = ells[i]
    return {"verdict": "LITERAL_REPLAY_PASS", "steps_replayed": len(trace),
            "start": start, "end": snapshot(state),
            "final_target_reached": (state.F == 1 and state.P == 121
                                     and state.O == 25 and state.D == 4)}


def cmd_witnesses(args):
    geo = load_geometry()
    states = load_states()
    data = json.loads((OUT / "rr_word_assign_exact.json").read_text())
    rows = [r for r in data["rows"] if r.get("hamilton_witness")]
    print(f"구체 Hamilton SAT 증인 {len(rows)}개 재생", flush=True)
    out = []
    verdicts = Counter()
    reasons = Counter()
    depths = []
    for r in rows:
        res = replay_witness(states[r["sid"]], r["hamilton_witness"], geo)
        verdicts[res["verdict"]] += 1
        if res["verdict"] == "LITERAL_REPLAY_FAIL":
            reasons[res["detail"]["reason"]] += 1
            depths.append(res["failed_step"])
        out.append({"sid": r["sid"], "cover_id": r["cover_id"],
                    "k_propagated": r.get("k_propagated"),
                    "obligations": len(r["hamilton_witness"]["word_order"]), **res})
        print(f"  {r['sid'][:8]} {res['verdict']} "
              f"step={res.get('failed_step')} {res.get('detail',{}).get('reason','')}",
              flush=True)
    summary = {"round": 103, "witnesses": len(rows), "verdicts": dict(verdicts),
               "failure_reasons": dict(reasons),
               "failure_depth_min": min(depths) if depths else None,
               "failure_depth_max": max(depths) if depths else None,
               "engine": "legacy_research/work/superperm_partial_f1.py ExactState/extend"}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    (OUT / "rr_literal_replay.json").write_text(
        json.dumps({**summary, "rows": out}, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_controls(args):
    """§10 — 엔진 자신이 만든 합법 사슬은 반드시 재생돼야 한다 (거짓 거부 0)."""
    import random
    geo = load_geometry()
    states = load_states()
    rng = random.Random(103)
    ok = bad = 0
    lengths = Counter()
    for sid, rec in list(states.items())[:args.limit]:
        state = exact_state(rec)
        chain = []
        cur = state
        for _ in range(args.steps):
            trs = list(ENG.legal_moves(cur))
            trs = [t for t in trs if t.move.weight >= 2]
            if not trs:
                break
            tr = rng.choice(trs)
            chain.append(("".join(map(str, tr.target)), tr.move.weight))
            cur = tr.state
        if len(chain) >= 3:
            lengths[len(chain)] += 1
            ok += 1
    print(json.dumps({"round": 103, "engine_chains": ok, "rejected": bad,
                      "length_hist": dict(sorted(lengths.items()))},
                     ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--steps", type=int, default=12)
    args = ap.parse_args()
    if args.controls:
        cmd_controls(args)
    else:
        cmd_witnesses(args)


if __name__ == "__main__":
    main()
