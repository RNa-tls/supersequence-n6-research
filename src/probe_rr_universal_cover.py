#!/usr/bin/env python3
"""라운드 88 — UNIVERSAL COVER CORE 와 예산 공유 결합 판정.

라운드 81~87 은 모두 같은 이유로 실패했다: 국소 제약은 진짜였지만 **다른** valid
slack-cover 해가 병목을 피해갔다.  이 모듈은 한 상태의 **모든** valid cover 가 공유하는
구조를 본다.

두 부분으로 이루어진다.

BACKBONE (§2, §6).  cover 가족 Covers(s) 를 완전 열거하고, 각 닫힌 궤도를
    FORCED    = 모든 valid cover 에 속함  (q 를 금지했을 때 UNSAT 이면 확정)
    FORBIDDEN = 어떤 valid cover 에도 속하지 않음  (q 를 강제했을 때 UNSAT 이면 확정)
    OPTIONAL  = 그 외
로 분류한다.  §10 에 따라 두 판정 모두 완전 유한 판정이며 표본 추출이 아니다.

결합 판정 (§5).  라운드 85 는 generation 예외만, 라운드 87 은 capacity 결손만 검사하면서
`ell < 5` short-edge 예산 2 를 **각각 따로** 썼다.  두 검사를 통과하는 cover 가 서로 다를 수
있으므로, 예산을 공유시키면 더 강한 필요조건이 된다:

    cover S 가 실현 가능하려면 |T| <= 2 인 T ⊆ S 가 존재하여
      (a) S∖T 가 A ∪ S 안에서 G5 로 induced-reachable  (T 는 어디서든 열린다고 관대 가정)
      (b) S∖T 가 G5 source-port 매칭 가능 (각 port 는 1회만 발사)
    를 **동시에** 만족해야 한다.

(a) 만 보면 라운드 85, (b) 만 보면 라운드 87 로 각각 환원되므로 결합은 둘 다보다 약하지 않다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.setrecursionlimit(10000)
ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "probe_rr_source_capacity", ROOT / "src" / "probe_rr_source_capacity.py")
cap = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = cap
_SPEC.loader.exec_module(cap)

po = cap.po
slack = cap.slack
macro = cap.macro
core = cap.core
exact = cap.exact
NORB = cap.NORB
BLOCKBITS = slack.BLOCKBITS
SRC = cap.SRC
pc = int.bit_count
SHORT_EDGE_BUDGET = 2
NODE_CAP = 3_000_000
SOLUTION_CAP = 200_000


def g5_relation():
    """G5[q] = ell=5 Z3 로 q 에서 새로 열 수 있는 궤도들의 비트마스크."""
    w3 = [m for m in macro.NONROT_H0 if m.weight == 3]
    ports = [core.orbit(core.E_REPS[q], core.E) for q in range(NORB)]
    edges = [0] * NORB
    for q in range(NORB):
        for w in ports[q]:
            cursor = w
            for _ in range(5):
                cursor = core.word_after(cursor, core.SIGMA)
            for move in w3:
                r = exact.ORBIT_PHASE[core.word_after(cursor, move.action)][0]
                if r != q:
                    edges[q] |= 1 << r
    return edges


G5 = g5_relation()


# ------------------------------------------------------------------ backbone


def count_covers(U, K, b, candidates, cap_count=2000):
    by_hex = defaultdict(list)
    for q in candidates:
        m = BLOCKBITS[q] & U
        while m:
            low = m & -m
            by_hex[low.bit_length() - 1].append(q)
            m ^= low
    st = {"nodes": 0, "solutions": 0, "complete": True}

    def rec(remaining, k):
        if remaining == 0:
            st["solutions"] += 1
            if st["solutions"] >= cap_count:
                st["complete"] = False
                return True
            return False
        st["nodes"] += 1
        if st["nodes"] > 400_000:
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
            if rec(remaining & ~BLOCKBITS[q], k - 1):
                return True
        return False

    rec(U, K)
    return st["solutions"], st["complete"]


def classify_orbit(U, K, b, q):
    """(FORCED?, FORBIDDEN?) -- 두 판정 모두 완전 유한 판정."""
    saved = BLOCKBITS[q]
    BLOCKBITS[q] = 0
    try:
        forced = slack.decide(U, K, b)["verdict"] != "SAT"
    finally:
        BLOCKBITS[q] = saved
    forbidden = not cap_sat_with(U, K, b, q)
    return forced, forbidden


def cap_sat_with(U, K, b, q):
    in_u = pc(BLOCKBITS[q] & U)
    waste = 5 - in_u
    if waste > b:
        return False
    u2, k2, b2 = U & ~BLOCKBITS[q], K - 1, b - waste
    if k2 == 0:
        return u2 == 0
    if pc(u2) != 5 * k2 - b2:
        return False
    return slack.decide(u2, k2, b2)["verdict"] == "SAT"


# ------------------------------------------------------------- joint decision


def g5_induced_reachable(a_bits, targets):
    reached = a_bits
    remaining = set(targets)
    changed = True
    while changed:
        changed = False
        for r in list(remaining):
            if any((G5[q] >> r & 1) for q in range(NORB) if reached >> q & 1):
                reached |= 1 << r
                remaining.discard(r)
                changed = True
    return not remaining


def port_matchable(targets, pool_orbits):
    adjacency = {t: [] for t in targets}
    for q in pool_orbits:
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
    return size == len(targets)


def cover_feasible(S, a_bits):
    """예산을 공유하는 결합 필요조건.  (성공 여부, 사용한 short edge 수)."""
    S = set(S)
    pool = {q for q in range(NORB) if a_bits >> q & 1} | S
    for t in range(SHORT_EDGE_BUDGET + 1):
        for T in combinations(sorted(S), t):
            rest = S - set(T)
            a_eff = a_bits
            for q in T:
                a_eff |= 1 << q
            if not g5_induced_reachable(a_eff, rest):
                continue
            if port_matchable(rest, pool):
                return True, t
    return False, None


def decide_state(U, K, b, a_bits, candidates):
    by_hex = defaultdict(list)
    for q in candidates:
        m = BLOCKBITS[q] & U
        while m:
            low = m & -m
            by_hex[low.bit_length() - 1].append(q)
            m ^= low
    st = {"nodes": 0, "solutions": 0, "complete": True, "witness": None, "t": None}

    def rec(remaining, k, chosen):
        if remaining == 0:
            st["solutions"] += 1
            ok, t = cover_feasible(chosen, a_bits)
            if ok:
                st["witness"] = list(chosen)
                st["t"] = t
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
    return verdict, st


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("backbone", "joint"))
    ap.add_argument("--sample", type=int, default=1000)
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = po.load_residual()
    result = {}
    if args.command == "backbone":
        import random
        random.seed(1)
        sample = random.sample(rows, min(args.sample, len(rows)))
        counts, forced_h, forbid_h = Counter(), Counter(), Counter()
        for r in sample:
            n, done = count_covers(r["U"], r["K"], r["b"], r["candidates"])
            counts[">=2000" if not done else
                   "<=10" if n <= 10 else "<=100" if n <= 100 else
                   "<=1000" if n <= 1000 else "<=2000"] += 1
            forced = forbidden = 0
            for q in r["candidates"]:
                fo, fb = classify_orbit(r["U"], r["K"], r["b"], q)
                forced += fo
                forbidden += fb
            forced_h[forced] += 1
            forbid_h[min(forbidden, 20)] += 1
        result = dict(sample=len(sample), cover_counts=dict(counts),
                      forced=dict(sorted(forced_h.items())),
                      forbidden=dict(sorted(forbid_h.items())),
                      note="표본 기반 진단이며 폐쇄 근거가 아니다 (§10)")
    else:
        agg, band, tdist, closed = Counter(), defaultdict(Counter), Counter(), []
        for i, r in enumerate(rows):
            v, st = decide_state(r["U"], r["K"], r["b"], r["open_orbits"], r["candidates"])
            agg[v] += 1
            band[r["c"]][v] += 1
            if v == "SAT":
                tdist[st["t"]] += 1
            elif v == "UNSAT":
                closed.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=r["K"],
                                   cover_solutions=st["solutions"]))
            if (i + 1) % 1000 == 0:
                print(f"  {i+1}/{len(rows)} {dict(agg)}", flush=True)
        result = dict(input_states=len(rows), aggregate=dict(agg),
                      short_edges_used=dict(sorted(tdist.items())),
                      by_collision_band={str(k): dict(v) for k, v in sorted(band.items())},
                      closed=closed)
    print(json.dumps({k: v for k, v in result.items() if k != "closed"}, indent=1)[:3000])
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
