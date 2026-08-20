#!/usr/bin/env python3
"""라운드 108 §5·§6·§14 — **리터럴 엔진으로 본 무거운 joint**.

  §5  550개 indecomposable tail 전부에 대해 `dS, dF, dH, dO, d(Ndef+H)` 를 엔진에서 직접
      읽어 `cost(w) = [w>=3] + max(w-3,0)` 가 **정확한지** (하한일 뿐인지) 확인한다.
  §6  1,353 조건부 상태 중 하나에서 **weight >= 4 joint 를 쓰는 합법 prefix** 를 실제로
      만든다.  성공하면 H5-local 은 거짓이다.
  §14 완전-joint 생성기의 양성 대조 — 엔진이 허용하는 전이를 모델도 전부 갖고 있어야 한다.

사용법:
    python3 src/probe_rr_heavy_joint_literal.py --states 40
"""

from __future__ import annotations

import argparse
import importlib.util as iu
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
WORK = ROOT / "legacy_research" / "work"


def _load(name, path):
    spec = iu.spec_from_file_location(name, path)
    mod = iu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


core = _load("superperm_port_lift", WORK / "superperm_port_lift.py")
exact = _load("superperm_partial_f1", WORK / "superperm_partial_f1.py")
C = _load("certify_rr_q2_zero", ROOT / "src" / "certify_rr_q2_zero.py")
FJ = _load("certify_rr_full_joint", ROOT / "src" / "certify_rr_full_joint.py")


def build(state):
    return exact.ExactState(tuple(int(ch) for ch in state["p"]),
                            tuple(state["hex_masks"]), tuple(state["orbit_masks"]),
                            F=state["F"], S=state["S"], H=state["H"])


def rotate_to(st, k):
    """회전 `k` 번 — 엔진의 weight-1 이동으로만 움직인다.  실패하면 None."""
    w1 = next(m for m in exact.ALL_MOVES if m.weight == 1)
    for _ in range(k):
        tr = exact.extend(st, w1)
        if tr is None:
            return None
        st = tr.state
    return st


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", type=int, default=40)
    args = ap.parse_args()
    t0 = time.time()
    word, orb, hexm, _jt = C.geometry()
    ident = {w: i for i, w in word.items()}
    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    _h, covers = C.read_jsonl(C.ARCHIVE / "covers.jsonl.gz")
    _h, hall = C.read_jsonl(C.ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        passing[h["sid"]].append(h["cover_id"])

    import gzip
    with gzip.open(OUT / "rr_q2_no_hall_certificate.jsonl.gz", "rt") as fh:
        fh.readline()
        rows = [json.loads(line) for line in fh]
    per = defaultdict(list)
    for r in rows:
        per[r["sid"]].append(r["reason"])
    conditional = sorted(s for s, v in per.items() if not all(x == "root_bound" for x in v))

    # ---------------- §5 사건표 --------------------------------------------------
    table = defaultdict(Counter)
    mismatches = 0
    checked = 0
    for sid in conditional[:args.states]:
        st = build(S[sid])
        for tr in exact.legal_moves(st):
            w = tr.move.weight
            if w < 2:
                continue
            checked += 1
            dN = (tr.delta_S + tr.delta_F - int(tr.new_orbit))
            table[w][(tr.delta_S, tr.delta_F, tr.delta_H, int(tr.new_orbit))] += 1
            # cost(w) 가 dS + dH 와 정확히 같은가
            if FJ.cost_of(w) != tr.delta_S + tr.delta_H:
                mismatches += 1
            table[w]["d(Ndef+H)=%d" % (dN + tr.delta_H)] += 1

    # ---------------- §6 무거운 joint 리터럴 prefix -------------------------------
    counterexample = None
    heavy_legal = Counter()
    for sid in conditional[:args.states]:
        stj = S[sid]
        st = build(stj)
        cid = sorted(passing[sid])[0]
        dom, ell, root = C.domains(stj, CV[(sid, cid)]["orbits"], orb, hexm)
        oblig_words = set()
        for n, ws in dom.items():
            oblig_words |= ws
        # 첫 pass: ROOT 에서 ell=5 회전한 뒤 joint
        y = rotate_to(st, 5)
        if y is None:
            continue
        for tr in exact.legal_moves(y):
            w = tr.move.weight
            if w < 4:
                continue
            heavy_legal[w] += 1
            tid = ident["".join(str(x) for x in tr.target)]
            if tid in oblig_words and counterexample is None:
                after = tr.state
                counterexample = {
                    "sid": sid, "cover_id": cid,
                    "root_word": stj["p"], "cursor_after_5_rotations":
                        "".join(str(x) for x in y.p),
                    "tail": tr.move.label, "weight": w,
                    "target_word": "".join(str(x) for x in tr.target),
                    "target_is_an_obligation_entry_word": True,
                    "delta": {"S": tr.delta_S, "F": tr.delta_F, "H": tr.delta_H,
                              "new_orbit": tr.new_orbit},
                    "after": {"F": after.F, "S": after.S, "H": after.H,
                              "O": after.O, "P": after.P, "D": after.D,
                              "Ndef": after.Ndef, "Ndef_plus_H": after.Ndef + after.H},
                    "engine_prune_reason_after": exact.f1_prune_reason(after),
                    "budget_cost": FJ.cost_of(w),
                }

    # ---------------- §14 양성 대조: 모델이 엔진의 전이를 빠뜨리지 않는가 ----------
    mc = FJ.min_cost_table(word, ident)
    missing = 0
    covered = 0
    for sid in conditional[:min(args.states, 12)]:
        st = build(S[sid])
        y = rotate_to(st, 5)
        if y is None:
            continue
        yid = ident["".join(str(x) for x in y.p)]
        for tr in exact.legal_moves(y):
            if tr.move.weight < 2:
                continue
            tid = ident["".join(str(x) for x in tr.target)]
            covered += 1
            if mc[yid * 720 + tid] > FJ.cost_of(tr.move.weight):
                missing += 1

    rep = {
        "round": 108,
        "event_table_transitions_checked": checked,
        "cost_formula_mismatches": mismatches,
        "cost_formula_is_exact_for_S_plus_H": mismatches == 0,
        "event_table": {str(w): {str(k): v for k, v in c.items()} for w, c in
                        sorted(table.items())},
        "heavy_legal_moves_by_weight": dict(sorted(heavy_legal.items())),
        "h5_local_counterexample": counterexample,
        "positive_control_engine_transitions": covered,
        "positive_control_missing_from_model": missing,
        "seconds": round(time.time() - t0),
    }
    (OUT / "rr_heavy_joint_literal.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main()
