#!/usr/bin/env python3
"""라운드 89 — forced core 의 source Hall 검사와 동적 유일 cover 추출.

`probe_rr_forced_core.py` 가 만든 census (`c1_census_<N>.json` 의 `forced_states`) 를 입력으로
받아 두 가지를 계산한다.

hall (§3).  각 상태의 FORCED 궤도만을 target 으로 놓고, source 우주는 **가장 관대하게**
    현재 열린 궤도 `A` 와 **모든 candidate(OPTIONAL 포함)** 의 5개 port 전부로 잡아 매칭
    결손을 잰다.  optional 궤도가 중간 source 로 쓰일 가능성을 배제하지 않기 위한
    의도적 과대근사이며, 따라서 결손 > 0 만이 폐쇄 근거가 될 수 있다 (§3 의 요구).

unique (§8, §9).  cover 해가 20개 이하인 tight 상태에 대해 라운드 88 의 결합 필요조건
    (`uc.cover_feasible`: 공유 short-edge 예산 2 아래의 G5 induced-reachability +
    source-port 매칭) 을 모든 cover 에 적용해 **동적으로 허용되는 cover** 를 전부 모은다.
    0개면 폐쇄, 1개면 최종 궤도 집합이 유일하게 결정된 상태다.  열거가 캡에 닿으면
    그 상태는 건너뛰고 INCOMPLETE 로 보고한다 — 캡 도달은 UNSAT 이 아니다.

사용법: `python3 src/probe_rr_forced_core_dynamics.py {hall,unique} --census <census.json>`
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.setrecursionlimit(10000)
ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "probe_rr_universal_cover", ROOT / "src" / "probe_rr_universal_cover.py")
uc = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = uc
_SPEC.loader.exec_module(uc)

po = uc.po
slack = uc.slack
NORB = uc.NORB
SRC = uc.SRC
BB = slack.BLOCKBITS
pc = int.bit_count
COVER_CAP = 5000
NODE_CAP = 1_500_000


def hall_deficit(targets, pool):
    """관대한 source 시스템 (pool 의 모든 궤도 x 5 port) 에서 targets 의 매칭 결손."""
    adjacency = {t: [] for t in targets}
    for q in pool:
        for f in range(5):
            for t in SRC[(q, f)]:
                if t in adjacency:
                    adjacency[t].append((q, f))
    matched = {}
    size = 0

    def augment(x, seen):
        for p in adjacency[x]:
            if p in seen:
                continue
            seen.add(p)
            if p not in matched or augment(matched[p], seen):
                matched[p] = x
                return True
        return False

    for t in sorted(targets):
        if augment(t, set()):
            size += 1
    return len(targets) - size


def admissible_covers(row):
    """모든 valid cover 를 열거하고 동적으로 허용되는 것만 반환. (해 목록, 완전 여부)."""
    U, K, b, cand, a_bits = (row["U"], row["K"], row["b"],
                             row["candidates"], row["open_orbits"])
    by_hex = defaultdict(list)
    for q in cand:
        m = BB[q] & U
        while m:
            low = m & -m
            by_hex[low.bit_length() - 1].append(q)
            m ^= low
    st = {"nodes": 0, "solutions": 0, "complete": True, "admissible": []}

    def rec(remaining, k, chosen):
        if remaining == 0:
            st["solutions"] += 1
            ok, t = uc.cover_feasible(chosen, a_bits)
            if ok:
                st["admissible"].append((sorted(chosen), t))
            if st["solutions"] >= COVER_CAP:
                st["complete"] = False
                return True
            return False
        st["nodes"] += 1
        if st["nodes"] > NODE_CAP:
            st["complete"] = False
            return True
        slackness = 5 * k - pc(remaining)
        if slackness < 0:
            return False
        options, fewest = [], 99
        m = remaining
        while m:
            low = m & -m
            h = low.bit_length() - 1
            m ^= low
            ok2 = [q for q in by_hex[h] if pc(BB[q] & remaining) >= 5 - slackness]
            if len(ok2) < fewest:
                options, fewest = ok2, len(ok2)
                if not fewest:
                    break
        if not fewest:
            return False
        for q in options:
            chosen.append(q)
            if rec(remaining & ~BB[q], k - 1, chosen):
                return True
            chosen.pop()
        return False

    rec(U, K, [])
    return st["admissible"], st["complete"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("hall", "unique"))
    ap.add_argument("--census", required=True, help="probe_rr_forced_core.py 가 쓴 census JSON")
    ap.add_argument("--out")
    args = ap.parse_args()
    forced_states = json.load(open(args.census))["forced_states"]
    rows = {r["sid"]: r for r in po.load_residual()}
    t0 = time.time()

    if args.command == "hall":
        distribution, positive = Counter(), []
        for sid, info in forced_states.items():
            r = rows[sid]
            pool = {q for q in range(NORB) if r["open_orbits"] >> q & 1} | set(r["candidates"])
            d = hall_deficit(set(info["forced"]), pool)
            distribution[d] += 1
            if d > 0:
                positive.append(dict(sid=sid, root=info["root"], c=info["c"],
                                     forced=len(info["forced"]), deficit=d))
        result = dict(states=len(forced_states),
                      deficit_distribution=dict(sorted(distribution.items())),
                      positive=positive,
                      note="가장 관대한 source 우주이므로 결손 > 0 만 폐쇄 근거가 된다")
    else:
        tight = [rows[sid] for sid, i in forced_states.items() if i["covers"] <= 20]
        histogram, unique, zero, incomplete = Counter(), [], [], []
        for j, r in enumerate(tight):
            covers, complete = admissible_covers(r)
            if not complete:
                incomplete.append(r["sid"])
                continue
            d = len(covers)
            histogram["0" if d == 0 else "1" if d == 1 else "2-5" if d <= 5
                      else "6-20" if d <= 20 else ">20"] += 1
            if d == 0:
                zero.append(r["sid"])
            elif d == 1:
                cover, t = covers[0]
                unique.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=r["K"], b=r["b"],
                                   covers=forced_states[r["sid"]]["covers"],
                                   forced=forced_states[r["sid"]]["forced"],
                                   unique_cover=cover, short_edges=t))
            if (j + 1) % 400 == 0:
                print(f"  {j+1}/{len(tight)} {time.time()-t0:.0f}s "
                      f"unique={len(unique)} zero={len(zero)}", flush=True)
        result = dict(tight_states=len(tight), histogram=dict(histogram),
                      zero_sids=zero, unique=unique, incomplete=incomplete)
    result["seconds"] = round(time.time() - t0)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("unique", "zero_sids")}, ensure_ascii=False, indent=1)[:3000])
    if args.out:
        json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
