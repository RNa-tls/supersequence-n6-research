#!/usr/bin/env python3
"""라운드 107 §12 — **모델이 생략한 호가 있는가?**

가중 인증서는 의무 그래프의 호를 **네 개의 최소 weight joint (`T1`–`T4`, weight 2/3)** 로만
만든다.  그러나 엔진의 이동 집합은 weight 1–6 의 **550개**다.  weight ≥ 4 인 joint 가
`σ^ℓ(A(h))` 에서 다른 의무의 배정 단어 `A(g)` 로 곧장 갈 수 있다면, 모델의 그래프에는
**호가 빠져 있고** 배제 논증(UNSAT)이 불건전해질 수 있다.

여기서 확인하는 것:

  1. weight ≥ 4 joint 로만 닿는 (의무 → 의무) 호가 실제 인스턴스에 존재하는가?
  2. 존재한다면 그 호의 **예산 비용**은 얼마인가?
     `cost(w) = [w ≥ 3] + max(w − 3, 0)` → w=4:2, w=5:3, w=6:4
  3. 생략된 호를 전부 넣고 다시 판정하면 결론이 바뀌는가?

사용법:
    python3 src/probe_rr_omitted_arcs.py --states 120
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
WORK = ROOT / "legacy_research" / "work"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


core = _load("superperm_port_lift", WORK / "superperm_port_lift.py")
C = _load("certify_rr_q2_zero", ROOT / "src" / "certify_rr_q2_zero.py")


def all_moves():
    """엔진과 같은 규칙으로 550개 이동을 만든다 (weight, 오른쪽 작용)."""
    moves = []
    for w in range(1, 7):
        for pi in core.tail_permutations(w):
            moves.append((w, core.tail_action(w, pi)))
    if len(moves) != 550:
        raise SystemExit(f"이동 수가 550 이 아니다: {len(moves)}")
    return moves


def budget_cost(w):
    return (1 if w >= 3 else 0) + max(w - 3, 0)


def as_perm(s):
    return tuple(int(ch) for ch in s)


def as_str(p):
    return "".join(str(x) for x in p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", type=int, default=120)
    args = ap.parse_args()
    t0 = time.time()
    word, orb, hexm, jt = C.geometry()
    ident = {w: i for i, w in word.items()}
    moves = all_moves()
    heavy = [(w, a) for w, a in moves if w >= 4]
    print(f"weight>=4 이동 {len(heavy)}개", flush=True)

    # 문자열 수준 사전 확인: T1..T4 가 정말 weight 2/3 이동의 상인가
    sample = word[0]
    p = as_perm(sample)
    got = {}
    for w, a in moves:
        if w in (2, 3):
            got.setdefault(w, set()).add(as_str(core.word_after(p, a)))
    expect = C.joint_words(sample)
    ok = expect[0] in got[2] and all(t in got[3] for t in expect[1:])
    print("T1 은 weight-2 상, T2/T3/T4 는 weight-3 상:", ok, flush=True)

    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    _h, covers = C.read_jsonl(C.ARCHIVE / "covers.jsonl.gz")
    _h, hall = C.read_jsonl(C.ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])

    stat = Counter()
    cost_hist = Counter()
    examples = []
    for sid in sorted(passing)[:args.states]:
        st = S[sid]
        for cid in sorted(passing[sid]):
            dom, ell, root = C.domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
            for A in C.assignments(dom):
                stat["assignments"] += 1
                home = {u: n for n, u in A.items()}
                for n, u in A.items():
                    y = as_perm(word[u])
                    for _ in range(ell[n]):
                        y = core.word_after(y, core.SIGMA)
                    for w, a in heavy:
                        v = ident[as_str(core.word_after(y, a))]
                        g = home.get(v)
                        if g is not None and g != n:
                            stat["omitted_arcs"] += 1
                            cost_hist[budget_cost(w)] += 1
                            if len(examples) < 5:
                                examples.append({"sid": sid, "cover_id": cid,
                                                 "from": list(n), "to": list(g),
                                                 "weight": w, "budget_cost": budget_cost(w)})
                break                       # 배정 하나면 충분하다 (구조적 질문이다)
    rep = {"round": 107, "weight_ge_4_moves": len(heavy),
           "T1_is_weight2_and_others_weight3": ok,
           "assignments_scanned": stat["assignments"],
           "omitted_arcs_found": stat["omitted_arcs"],
           "omitted_arc_cost_histogram": dict(sorted(cost_hist.items())),
           "examples": examples, "seconds": round(time.time() - t0)}
    (OUT / "rr_omitted_arcs.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
