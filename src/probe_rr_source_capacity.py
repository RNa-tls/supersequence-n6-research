#!/usr/bin/env python3
"""라운드 87 — 누적 출발-port 용량(cumulative source-port capacity).

`E^1` 은 적법할 때 위상을 자유롭게 옮기지만, no-repeat 가 이미 소비한 port/window 를
되돌리지는 못한다.  최종 cover 는 소수의 출발 궤도에서 여러 번의 fresh-orbit Z3 opening 을
요구할 수 있으므로, 유한한 출발 port 자원이 그것을 감당할 수 있는지가 이 라운드의 질문이다.

출발 port 의미론 (증명).
    모든 매크로 edge 는 walk 의 현재 endpoint 에서 출발하고, endpoint 는 언제나 직전 joint 의
    target, 즉 **등록된 port** 다(초기 endpoint 도 등록되어 있다).  no-repeat 에 의해 각
    window 는 정확히 한 번 방문되므로 각 port 는 정확히 한 번만 endpoint 가 되고, 따라서
    **최대 1개의 매크로 edge 를 발사한다.**  그러므로

        cap_s(q)   = (q 의 미방문 port 수) + [q 가 현재 endpoint 를 포함]
        cap_new(r) = (r 의 미방문 port 수)

    이며, 용량을 과대평가하는 것은 안전하고 과소평가하는 것은 UNSOUND 다.

라벨 G5 (검증된 기하).
    ell = 5 Z3 opening 은 (궤도 q, 위상 f) 마다 정확히 2개의 target 궤도를 준다.  같은 궤도의
    서로 다른 두 port 의 target 집합은 **전혀 겹치지 않으므로**(1,440쌍 모두 겹침 0), 궤도당
    10개의 서로 다른 target 이 나오고, 역으로 target 하나를 열 수 있는 것은 10개 궤도이며
    각 궤도에서 **정확히 1개의 특정 port** 뿐이다.

필요조건.
    S 의 각 target 은 A ∪ S 안 어떤 궤도의 어떤 port 에서 열려야 하고, 각 port 는 1회만
    발사한다.  이는 이분 매칭이다.  다만 `ell < 5` short edge 로도 opening 이 가능하고 그
    예산이 2 이므로(라운드 85), **최대 2개의 target 은 이 매칭을 우회할 수 있다.**  따라서
    건전한 폐쇄 기준은 매칭 결손 >= 3 이다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.setrecursionlimit(10000)
ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "probe_rr_cover_order", ROOT / "src" / "probe_rr_cover_order.py")
po = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = po
_SPEC.loader.exec_module(po)

slack = po.slack
macro = po.macro
exact = po.exact
core = po.core
NORB = po.NORB
BLOCKBITS = slack.BLOCKBITS
pc = int.bit_count
NODE_CAP = 3_000_000
SOLUTION_CAP = 300_000
SHORT_EDGE_BUDGET = 2


def source_port_table():
    """SRC[(q, f)] = 그 port 에서 ell=5 Z3 로 열 수 있는 target 궤도 집합."""
    w3 = [m for m in macro.NONROT_H0 if m.weight == 3]
    ports = [core.orbit(core.E_REPS[q], core.E) for q in range(NORB)]
    src = {}
    for q in range(NORB):
        for f, w in enumerate(ports[q]):
            cursor = w
            for _ in range(5):
                cursor = core.word_after(cursor, core.SIGMA)
            targets = set()
            for move in w3:
                r = exact.ORBIT_PHASE[core.word_after(cursor, move.action)][0]
                if r != q:
                    targets.add(r)
            src[(q, f)] = targets
    return src


SRC = source_port_table()


def table_report() -> dict:
    per_port = Counter(len(v) for v in SRC.values())
    per_orbit = Counter()
    overlap = Counter()
    for q in range(NORB):
        sets = [SRC[(q, f)] for f in range(5)]
        per_orbit[len(set().union(*sets))] += 1
        for i in range(5):
            for j in range(i + 1, 5):
                overlap[len(sets[i] & sets[j])] += 1
    suppliers = Counter()
    supplier_orbits = defaultdict(set)
    for (q, f), ts in SRC.items():
        for r in ts:
            suppliers[r] += 1
            supplier_orbits[r].add(q)
    return dict(targets_per_source_port=dict(per_port),
                distinct_targets_per_orbit=dict(per_orbit),
                same_orbit_port_target_overlap=dict(overlap),
                supplier_ports_per_target=dict(Counter(suppliers.values())),
                supplier_orbits_per_target=dict(Counter(len(v) for v in supplier_orbits.values())))


def matching_deficit(S, A) -> int:
    """S 의 각 target 을 A ∪ S 의 (궤도, port) 자원에 매칭했을 때의 결손."""
    pool = [(q, f) for q in (A | S) for f in range(5)]
    adjacency = {t: [] for t in S}
    for p in pool:
        for t in SRC[p]:
            if t in adjacency:
                adjacency[t].append(p)
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

    for t in sorted(S):
        if augment(t, set()):
            size += 1
    return len(S) - size


def decide(U, K, b, A, candidates, threshold=SHORT_EDGE_BUDGET + 1):
    """어떤 cover 라도 결손 < threshold 이면 SAT.  전부 >= threshold 여야 UNSAT."""
    by_hex = defaultdict(list)
    for q in candidates:
        m = BLOCKBITS[q] & U
        while m:
            low = m & -m
            by_hex[low.bit_length() - 1].append(q)
            m ^= low
    st = {"nodes": 0, "solutions": 0, "complete": True, "best": 99, "witness": None}

    def rec(remaining, k, chosen):
        if remaining == 0:
            st["solutions"] += 1
            d = matching_deficit(set(chosen), A)
            st["best"] = min(st["best"], d)
            if d < threshold:
                st["witness"] = list(chosen)
                return True
            if st["solutions"] >= SOLUTION_CAP:
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
            ok = [q for q in by_hex[h] if pc(BLOCKBITS[q] & remaining) >= 5 - slackness]
            if len(ok) < fewest:
                options, fewest = ok, len(ok)
                if not fewest:
                    break
        if not fewest:
            return False
        for q in options:
            chosen.append(q)
            if rec(remaining & ~BLOCKBITS[q], k - 1, chosen):
                return True
            chosen.pop()
        return False

    rec(U, K, [])
    verdict = ("SAT" if st["witness"] is not None
               else "UNKNOWN" if not st["complete"] else "UNSAT")
    return dict(verdict=verdict, min_deficit=st["best"],
                cover_solutions=st["solutions"], nodes=st["nodes"])


def census() -> dict:
    rows = po.load_residual()
    agg = Counter()
    by_band = defaultdict(Counter)
    deficits = Counter()
    closed = []
    for n, r in enumerate(rows):
        A = {q for q in range(NORB) if r["open_orbits"] >> q & 1}
        res = decide(r["U"], r["K"], r["b"], A, r["candidates"])
        agg[res["verdict"]] += 1
        by_band[r["c"]][res["verdict"]] += 1
        deficits[min(res["min_deficit"], 9)] += 1
        if res["verdict"] == "UNSAT":
            closed.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=r["K"],
                               cover_solutions=res["cover_solutions"],
                               min_deficit=res["min_deficit"]))
        if (n + 1) % 1000 == 0:
            print(f"  {n+1}/{len(rows)} {dict(agg)}", flush=True)
    return dict(input_states=len(rows), aggregate=dict(agg),
                min_deficit_over_all_covers=dict(sorted(deficits.items())),
                by_collision_band={str(k): dict(v) for k, v in sorted(by_band.items())},
                closed=closed, short_edge_budget=SHORT_EDGE_BUDGET)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("table", "census"))
    ap.add_argument("--out")
    args = ap.parse_args()
    result = table_report() if args.command == "table" else census()
    print(json.dumps({k: v for k, v in result.items() if k != "closed"}, indent=1)[:3000])
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
