#!/usr/bin/env python3
"""라운드 85 — G5 생성 + 최대 2회 ell<5 예외 조건.

배경.  라운드 84에서 유도한 사실: F = 1이므로 앞으로 abandonment는 불가능하고, 따라서
새 육각형에 진입한 pass는 그 육각형을 끝까지 채워야 하며(ell = 5), pass 계수에 의해
부분 방문 육각형은 현재 육각형과 fragment 둘뿐이다.  그러므로

    앞으로의 매크로 간선 중 ell < 5 인 것은 최대 2개.

이 모듈은 그 예산을 궤도 집합 생성 문제에 적용한다.

관계 두 개(둘 다 위상을 전부 양화한 보수적 과대근사):

    G5      q -> r  :  ell = 5 인 Z3 매크로 간선으로 r 을 새로 열 수 있다
    Gshort  q -> r  :  ell < 5 인 Z3 매크로 간선으로 r 을 새로 열 수 있다

필요조건.  S 를 유효한 slack-cover 선택 집합이라 하면 S 는 어떤 순서 r1..rK 로 열려야 하고,
각 ri 는 A ∪ {r1..r(i-1)} 안에 선행자를 가져야 하며, 그 선행 간선 중 G5 에 속하지 않는 것은
**최대 2개**다.  라운드 84의 보조정리는 모든 매크로 간선에 대한 것이므로, 그중 opening
간선에만 예산 2를 쓰는 것은 안전한 완화다.

``min_exceptions`` 는 최소 예외 수를 계산한다.  이 값을 **과대평가하면 잘못 닫게 되어
UNSOUND** 이므로, G5 로 갈 수 있는 것은 언제나 먼저 무료로 닫고(단조이므로 미룰 이유가 없다)
예외 대상은 전수 분기한다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

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
SOLUTION_CAP = 200_000
NODE_CAP = 2_000_000


def build_relations():
    """G5 (ell = 5), Gshort (ell < 5), 그리고 합집합인 전체 Z3 관계."""
    w3 = [m for m in macro.NONROT_H0 if m.weight == 3]
    ports = [core.orbit(core.E_REPS[q], core.E) for q in range(NORB)]
    orbit_of = {w: exact.ORBIT_PHASE[w][0] for w in core.ALL_WORDS}

    def build(lengths):
        edges = [0] * NORB
        for q in range(NORB):
            for w in ports[q]:
                cursor = w
                for ell in range(6):
                    if ell in lengths:
                        for move in w3:
                            r = orbit_of[core.word_after(cursor, move.action)]
                            if r != q:
                                edges[q] |= 1 << r
                    cursor = core.word_after(cursor, core.SIGMA)
        return edges

    return build([5]), build(range(5)), build(range(6))


G5, GSHORT, GFULL = build_relations()


def min_exceptions(A: int, S, cap: int = 3) -> int:
    """S 를 A 에서 생성하는 데 필요한 최소 Gshort 예외 수 (cap 이상이면 cap)."""
    S = set(S)
    best = [cap]

    def close(R, remaining):
        changed = True
        while changed:
            changed = False
            for r in list(remaining):
                if any((G5[q] >> r & 1) for q in range(NORB) if R >> q & 1):
                    R |= 1 << r
                    remaining.discard(r)
                    changed = True
        return R, remaining

    def rec(R, remaining, used):
        R, remaining = close(R, set(remaining))
        if not remaining:
            best[0] = min(best[0], used)
            return
        if used >= cap or used + 1 >= best[0]:
            return
        for r in sorted(remaining):
            if any((GFULL[q] >> r & 1) for q in range(NORB) if R >> q & 1):
                rec(R | (1 << r), remaining - {r}, used + 1)

    rec(A, S, 0)
    return best[0]


def decide(U, K, b, A, candidates, max_exceptions, mrv=True):
    """cover 해를 열거하며 각각의 최소 예외 수를 검사한다.  캡 초과는 UNKNOWN."""
    by_hex = defaultdict(list)
    for q in candidates:
        m = BLOCKBITS[q] & U
        while m:
            low = m & -m
            by_hex[low.bit_length() - 1].append(q)
            m ^= low
    st = {"nodes": 0, "solutions": 0, "complete": True, "witness": None, "best": 99}

    def rec(remaining, k, chosen):
        if remaining == 0:
            st["solutions"] += 1
            e = min_exceptions(A, chosen, cap=max_exceptions + 1)
            st["best"] = min(st["best"], e)
            if e <= max_exceptions:
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
        if mrv:
            options, fewest = [], 99
            m = remaining
            while m:
                low = m & -m
                h = low.bit_length() - 1
                m ^= low
                ok = [q for q in by_hex[h]
                      if pc(BLOCKBITS[q] & remaining) >= 5 - slackness]
                if len(ok) < fewest:
                    options, fewest = ok, len(ok)
                    if not fewest:
                        break
        else:
            h = (remaining & -remaining).bit_length() - 1
            options = [q for q in by_hex[h]
                       if pc(BLOCKBITS[q] & remaining) >= 5 - slackness]
        if not options:
            return False
        for q in options:
            chosen.append(q)
            if rec(remaining & ~BLOCKBITS[q], k - 1, chosen):
                return True
            chosen.pop()
        return False

    rec(U, K, [])
    if st["witness"] is not None:
        verdict = "SAT"
    elif not st["complete"]:
        verdict = "UNKNOWN"
    else:
        verdict = "UNSAT"
    return dict(verdict=verdict, witness=st["witness"], min_exceptions=st["best"],
                cover_solutions=st["solutions"], nodes=st["nodes"],
                complete=st["complete"])


def relation_report() -> dict:
    def stats(e):
        return dict(edges=sum(pc(x) for x in e),
                    out_degree=dict(Counter(pc(x) for x in e)))
    return dict(
        G5=stats(G5), Gshort=stats(GSHORT), full_Z3=stats(GFULL),
        G5_subset_of_full=all((G5[q] & ~GFULL[q]) == 0 for q in range(NORB)),
        Gshort_equals_full=all(GSHORT[q] == GFULL[q] for q in range(NORB)),
        G5_union_Gshort_equals_full=all((G5[q] | GSHORT[q]) == GFULL[q]
                                        for q in range(NORB)),
        Gshort_beyond_G5=sum(pc(GSHORT[q] & ~G5[q]) for q in range(NORB)),
    )


def census(max_exceptions=2) -> dict:
    rows = po.load_residual()
    agg = Counter()
    exceptions_hist = Counter()
    by_band = defaultdict(Counter)
    closed_rows = []
    for n, r in enumerate(rows):
        A, U, K, b = r["open_orbits"], r["U"], r["K"], r["b"]
        candidates = r["candidates"]
        one = 0
        for q in range(NORB):
            if A >> q & 1:
                one |= G5[q]
        reachable = {q for q in candidates if one >> q & 1}
        saved = BLOCKBITS[:]
        try:
            for q in range(NORB):
                if q not in reachable:
                    BLOCKBITS[q] = 0
            quick = slack.decide(U, K, b)["verdict"]
        finally:
            BLOCKBITS[:] = saved
        if quick == "SAT":
            agg["zero_exception_SAT"] += 1
            exceptions_hist[0] += 1
            by_band[r["c"]]["zero_SAT"] += 1
            continue
        zero = decide(U, K, b, A, candidates, 0)
        if zero["verdict"] == "SAT":
            agg["zero_exception_SAT"] += 1
            exceptions_hist[0] += 1
            by_band[r["c"]]["zero_SAT"] += 1
            continue
        res = decide(U, K, b, A, candidates, max_exceptions)
        agg[f"two_exception_{res['verdict']}"] += 1
        by_band[r["c"]][f"two_{res['verdict']}"] += 1
        exceptions_hist[min(res["min_exceptions"], max_exceptions + 1)] += 1
        if res["verdict"] == "UNSAT":
            closed_rows.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=K, b=b,
                                    candidates=len(candidates),
                                    cover_solutions=res["cover_solutions"],
                                    min_exceptions=res["min_exceptions"],
                                    nodes=res["nodes"]))
        if (n + 1) % 1000 == 0:
            print(f"  {n+1}/{len(rows)} {dict(agg)}", flush=True)
    return dict(input_states=len(rows), aggregate=dict(agg),
                min_exception_histogram=dict(sorted(exceptions_hist.items())),
                by_collision_band={str(k): dict(v) for k, v in sorted(by_band.items())},
                closed=closed_rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("relations", "census"))
    ap.add_argument("--out")
    args = ap.parse_args()
    result = relation_report() if args.command == "relations" else census()
    print(json.dumps({k: v for k, v in result.items() if k != "closed"}, indent=1)[:4000])
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
