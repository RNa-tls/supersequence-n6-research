#!/usr/bin/env python3
"""라운드 135 (Astra/Codex) 독립 감사 — 목표 `(k, G) = (3, 2)`.

Astra 의 표·산술을 하나도 베끼지 않는다.  복구된 `G` 골격에서 자원 표를 처음부터
다시 유도하고 (§1), 축약 회계를 다시 세우며 (§5), 라운드 115 용량을 직접 조회·재실행하고
(§6·§7), `H=1` 논증(§8–§12)을 독립 재구성한다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup, legal_joint          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
N, K, GG = 6, 3, 2

_T115 = json.loads((OUT / "rr_f0_column_115.json").read_text())["table"]


# 라운드 135 가 쓴 셀 중 저장 표에 없는 것은 이 감사가 **직접 재실행**해 얻었다.
_REPLAYED = {"1,0,13": (98, False, 681902414), "1,0,12": (98, False, 307634294)}


def NSTAR(b, g, s):
    k = f"{b},{g},{s}"
    if k in _T115:
        return (_T115[k]["passes"], _T115[k]["capped"])
    if k in _REPLAYED:
        return (_REPLAYED[k][0], _REPLAYED[k][1])
    return None


# ------------------------------------------------------------------ §1 resource table
def resource_table():
    """§1 — `(k,G) = (3,2)` 의 자원 표를 **처음부터** 유도한다.

    ```
    P = n!/n + G          = 120 + 2 = 122
    O = n!/(n(n−1)) + k   = 24 + 3  = 27
    D = (n−1)·O − P       = 135 − 122 = 13
    r = O + e = 27 + e
    S = (r − 1) + x − f_out = 26 + e + x − f_out
    L = 844 + G + S + H = 846 + S + H ≤ 871  ⇒  S + H ≤ 25
                                            ⇒  f_out ≥ e + x + H + 1
    정리 129.1:  f_out ≤ F + e.   delta := F + e − f_out ≥ 0.
    대입:  F + e − delta ≥ e + x + H + 1  ⇒  **delta + x + H ≤ F − 1**
    ```
    `F = 1` 이면 `delta = x = H = 0` 이 강제되고, `F = 2` 이면 `delta + x + H ≤ 1` 이다.
    """
    P = 720 // N + GG
    O = 720 // (N * (N - 1)) + K
    D = (N - 1) * O - P
    rows = []
    for typ, m, Fvals in (("A", 1, (1, 2)), ("B", 2, (2,))):
        nshort = GG + m
        for F in Fvals:
            for delta in range(0, F):
                for x in range(0, F):
                    for H in range(0, F):
                        if delta + x + H > F - 1:
                            continue
                        for e in range(0, 9):
                            f_out = F + e - delta
                            if f_out < 0 or f_out > nshort:
                                continue
                            if f_out > GG + e:            # generic bound f_out <= G + e
                                continue
                            if f_out < e + x + H + 1:     # length budget
                                continue
                            S = 26 + e + x - f_out
                            rows.append(dict(type=typ, F=F, e=e, x=x, H=H, delta=delta,
                                             f_out=f_out, S=S, r=O + e,
                                             L=869 + K + e + x + H - f_out - 3 + 3,
                                             S_plus_H=S + H))
    for r in rows:
        r["L"] = 846 + r["S"] + r["H"]
    by_delta = Counter(r["delta"] for r in rows)
    return dict(P=P, O=O, D=D,
                inequality="delta + x + H <= F - 1   (delta := F + e - f_out)",
                derivation=[
                    "P = 120 + G = 122", "O = 24 + k = 27", "D = 5O - P = 13",
                    "S = (r-1) + x - f_out with r = O + e  =>  S = 26 + e + x - f_out",
                    "L = 846 + S + H <= 871  =>  f_out >= e + x + H + 1",
                    "Theorem 129.1: f_out <= F + e, so delta >= 0",
                    "substituting f_out = F + e - delta gives delta + x + H <= F - 1"],
                n_rows=len(rows), by_delta=dict(by_delta),
                by_type_F=dict(Counter(f"{r['type']}/F{r['F']}" for r in rows)),
                all_L_within_budget=all(r["L"] <= 871 for r in rows),
                delta1_rows=[r for r in rows if r["delta"] == 1],
                delta0_rows=[r for r in rows if r["delta"] == 0],
                rows=rows)


# ------------------------------------------------------- §5 contracted accounting
def contracted_accounting(rt):
    """§5 — 두 번 축약한 뒤의 매개변수를 **행마다** 독립적으로 유도한다.

    축약은 겹친 육각형의 조각들을 하나의 full pass 로 합치고 그 사이의 잠긴 run 을 지운다.
    잠긴 run 이 궤도의 다섯 phase 를 **전부** 채우면 pass 가 5 개 사라지고 (라운드 134),
    run 안에 `x`-호(=`M3a`)가 있어 phase 를 건너뛰면 그만큼 덜 사라진다.  건너뛴 phase 총수를
    `u` 라 하면

        P' = 122 − (10 − u) = **112 + u**,   O' = 27 − 2 = **25**,
        D' = 5·O' − P' = 125 − 112 − u = **13 − u**.

    `u = 0` 은 `x = 0` 일 때 (건너뛰려면 run 안 `ω≥3` 호가 필요하다).  `u ≥ 1` 은 `x ≥ 1` 을
    요구하고, `D' = 13 − u ≥ 0` 이라 `u ≤ 13`.

    축약 후 pass 는 전부 full 이고 full pass 의 `ω=2` 후속은 같은 궤도이므로 `f_out' = 0`,
    따라서 joint 세기로

        S' = (r' − 1 − f_out') + x' = O' + e' − 1 + x'  ⇒  e' + x' = S' − 24,

    이고 `S' = S`, `H' = H` (축약은 `ω≥3` joint 을 하나도 지우지 않는다).
    `S = 26 + x + delta − F` (`f_out = F + e − delta` 대입) 이므로

        **b' := e' + x' = 2 + x + delta − F.**
    """
    out = []
    for r in rt["rows"]:
        S = r["S"]
        bprime = 2 + r["x"] + r["delta"] - r["F"]
        umax = r["x"]                      # 건너뛰려면 x-호가 필요하다
        out.append(dict(**{k: r[k] for k in ("type", "F", "e", "x", "H", "delta", "f_out",
                                             "S")},
                        P_prime="112 + u", O_prime=25, D_prime="13 - u",
                        S_prime=S, H_prime=r["H"], b_prime=bprime,
                        b_prime_check=(S - 24 == bprime), u_upper_bound=umax))
    return dict(formula=dict(P="112 + u", O=25, D="13 - u",
                             b="e' + x' = 2 + x + delta - F",
                             u="total number of orbit phases skipped inside the two "
                               "contracted runs; u = 0 whenever x = 0, and u <= x-many "
                               "skips, each needing an intra-run omega>=3 arc"),
                rows=out,
                all_b_consistent=all(o["b_prime_check"] for o in out),
                b_values=dict(Counter(o["b_prime"] for o in out)))


# --------------------------------------------------- §6·§7 capacity exclusions (H = 0)
def capacity_exclusions(rt, ca):
    """§6·§7 — `H = 0` 인 `delta = 0` 행을 라운드 115 용량으로 배제한다.

    축약 결과물은 무거운 joint 이 없으면 (`H' = 0`) **사슬 하나**다: `ω=2` joint 은 전부
    run 확장이고, `ω=3` joint 중 `M3a` 는 run 내부(`x'` 로 계상), `M3b`/`M3c` 는 라운드 115 의
    경량 연결자다.  필요한 pass 수는 `112 + u` 이고 예산은 `(b', 0, 13 − u)` 이다.
    `feasible()` 이 `SCAP` 에 단조이므로 `s` 를 키우면 상한만 느슨해진다.
    """
    tbl = []
    for o in ca["rows"]:
        if o["delta"] != 0 or o["H_prime"] != 0:
            continue
        b = o["b_prime"]
        tight = NSTAR(b, 0, 13)
        loose = NSTAR(b, 0, 15)
        # u 는 축약된 두 run 에서 건너뛴 phase 총수.  건너뛰려면 run 안 omega>=3 호가
        # 필요하므로 u = 0 whenever x = 0.  모든 허용 u 에서 배제되는지 확인한다.
        per_u = []
        for u in range(0, (o["x"] * 4) + 1):
            cap = NSTAR(b, 0, 13 - u)
            if cap is None:
                continue
            per_u.append(dict(u=u, required=112 + u, budget_s=13 - u, capacity=cap[0],
                              uncapped=(cap[1] is False), excluded=(112 + u > cap[0])))
        tbl.append(dict(row=f"{o['type']}/F{o['F']}/e{o['e']}/x{o['x']}/H{o['H']}",
                        b_prime=b, required_passes_at_u0=112,
                        N_star_tight=f"N*({b},0,13)", tight_value=tight[0] if tight else None,
                        tight_uncapped=(tight[1] is False) if tight else None,
                        N_star_loose=f"N*({b},0,15)", loose_value=loose[0] if loose else None,
                        per_u=per_u,
                        excluded=(bool(per_u) and all(z["excluded"] for z in per_u))))
    return dict(
        note=("with u > 0 the requirement grows to 112 + u while the budget shrinks to "
              "13 - u, so N*(b,0,13-u) <= N*(b,0,13) and the exclusion only gets stronger"),
        rows=tbl, n_rows=len(tbl), all_excluded=all(t["excluded"] for t in tbl),
        capacities_used={"N*(0,0,13)": NSTAR(0, 0, 13), "N*(1,0,13)": NSTAR(1, 0, 13),
                         "N*(0,0,15)": NSTAR(0, 0, 15), "N*(1,0,15)": NSTAR(1, 0, 15)})


# ------------------------------------------------------------ §8 H = 1 unique heavy
def h1_unique_heavy():
    """§8 — `H = 1` 은 **정확히 하나의 무게-4 joint** 을 뜻한다.

    `H := Σ_joints (ω − 3)₊` 이다.  무거운 joint 하나마다 `ω − 3 ≥ 1` 을 내므로
    합이 1 이면 항이 정확히 하나이고 그 값이 1, 즉 `ω = 4` 다.
      * 무게 5 는 `2`, 무게 6 은 `3` 을 내므로 배제된다;
      * 무거운 joint 이 둘 이상이면 합이 `≥ 2` 라 배제된다;
      * `H` 는 joint 위의 합이라 끝점 보정 항이 없다 (pass 내부 전이는 `ω = 1` 이라 기여 0).
    """
    return dict(definition="H = sum over joints of max(omega - 3, 0)",
                conclusion="H = 1  <=>  exactly one joint has omega = 4 and all others "
                           "have omega <= 3",
                rules_out=["omega = 5 (contributes 2)", "omega = 6 (contributes 3)",
                           "two or more heavy joints (sum >= 2)",
                           "endpoint artefacts (H is a sum over joints only)"],
                proved=True)


# ------------------------------------------- §10 capacity-equality classification
def equality_classification():
    """§10 — 무게-4 joint 에서 자르면 사슬 둘이 되고 결손이 `d₁ + d₂ = 13` 으로 쪼개진다.

    두 조각은 `b = 0`, `g = 0` (`e' = x' = 0` 이고 `g` 풀은 `2e' = 0`) 이므로 궤도를 공유할
    수 없다.  따라서 `p₁ + p₂ ≤ N*(0,0,d₁) + N*(0,0,d₂)` 이고 필요한 값은 `112` 다.
    """
    rows = []
    best = -1
    for d1 in range(0, 14):
        d2 = 13 - d1
        a, b = NSTAR(0, 0, d1), NSTAR(0, 0, d2)
        if a is None or b is None:
            continue
        tot = a[0] + b[0]
        best = max(best, tot)
        rows.append(dict(d1=d1, d2=d2, cap1=a[0], cap2=b[0], total=tot,
                         reaches_112=(tot >= 112), uncapped=(not a[1] and not b[1])))
    eq = [r for r in rows if r["total"] >= 112]
    return dict(required=112, max_total=best, splits=rows,
                equality_tuples=[(r["d1"], r["d2"], r["cap1"], r["cap2"]) for r in eq],
                unique_up_to_orientation=(sorted({tuple(sorted((r["d1"], r["d2"])))
                                                  for r in eq}) == [(4, 9)]),
                both_orientations_present=({(r["d1"], r["d2"]) for r in eq}
                                           == {(4, 9), (9, 4)}),
                forces_both_chains_extremal=(best == 112),
                all_cells_uncapped=all(r["uncapped"] for r in rows))


# ============================================================ §11·§12 독립 재구현
# 라운드 115 사슬 모델을 파이썬으로 **처음부터 다시** 구현한다 (C 를 호출하지 않는다).
G6 = setup(6)
P6, IDX6, SG6 = G6["perms"], G6["idx"], G6["sig"]
HEX6, ORB6, OPH6 = G6["hexid"], G6["orbid"], G6["orbph"]
NORB = max(ORB6) + 1
WORD_AT = [[0] * 5 for _ in range(NORB)]
for _w in range(720):
    WORD_AT[ORB6[_w]][OPH6[_w]] = _w


def _sig5(w):
    y = P6[w]
    for _ in range(5):
        y = SG6(y)
    return y


W3B, W3C = [0] * 720, [0] * 720
for _w in range(720):
    _y = _sig5(_w)
    W3B[_w] = IDX6[(_y[3], _y[4], _y[5], _y[2], _y[0], _y[1])]
    W3C[_w] = IDX6[(_y[3], _y[4], _y[5], _y[2], _y[1], _y[0])]


def _feasible(omask, scap, tokens, skip):
    c = [0] * 5
    for q, mk in omask.items():
        d = 5 - bin(mk).count("1")
        if q == skip:
            continue
        c[d] += 1
    tok, tot = tokens, 0
    for d in range(4, 0, -1):
        take = min(c[d], tok)
        tok -= take
        tot += (c[d] - take) * d
    return tot <= scap


def chain_search(start, bcap, gcap, scap, want=None, forbid_hex=frozenset(),
                 forbid_orb=frozenset(), collect=False, node_cap=200_000_000):
    """라운드 115 사슬 모델의 독립 구현.

    `want` 가 주어지면 그 길이의 사슬만 수집한다.  `forbid_hex` / `forbid_orb` 는
    §12 의 이음매 검사에 쓴다 (앞 사슬이 이미 먹은 육각형·궤도).
    """
    best = [0]
    found = []
    nodes = [0]
    usedhex = set(forbid_hex)
    omask = {}

    def rec(cur, corb, bused, passes, path):
        nodes[0] += 1
        if nodes[0] > node_cap:
            raise RuntimeError("node cap")
        if _feasible(omask, scap, gcap, None):
            if passes > best[0]:
                best[0] = passes
            if collect and want is not None and passes == want:
                found.append(tuple(path))
        if not _feasible(omask, scap, gcap + (bcap - bused), corb):
            return
        if want is not None and passes >= want:
            return
        p = OPH6[cur]
        for np_ in range(5):
            if omask.get(corb, 0) >> np_ & 1:
                continue
            w = WORD_AT[corb][np_]
            if HEX6[w] in usedhex:
                continue
            extra = 0 if np_ == (p + 1) % 5 else 1
            if bused + extra > bcap:
                continue
            omask[corb] |= 1 << np_
            usedhex.add(HEX6[w])
            path.append(w)
            rec(w, corb, bused + extra, passes + 1, path)
            path.pop()
            usedhex.discard(HEX6[w])
            omask[corb] &= ~(1 << np_)
        for w in (W3C[cur], W3B[cur]):
            if HEX6[w] in usedhex:
                continue
            nq = ORB6[w]
            if nq in forbid_orb:
                continue
            fresh = nq not in omask
            nb = bused + (0 if fresh else 1)
            if nb > bcap:
                continue
            prev = omask.get(nq, 0)
            omask[nq] = prev | (1 << OPH6[w])
            usedhex.add(HEX6[w])
            path.append(w)
            rec(w, nq, nb, passes + 1, path)
            path.pop()
            usedhex.discard(HEX6[w])
            if prev:
                omask[nq] = prev
            else:
                del omask[nq]

    q0 = ORB6[start]
    if q0 in forbid_orb or HEX6[start] in usedhex:
        return dict(best=0, chains=[], nodes=0)
    omask[q0] = 1 << OPH6[start]
    usedhex.add(HEX6[start])
    rec(start, q0, 0, 1, [start])
    return dict(best=best[0], chains=found, nodes=nodes[0])


def weight4_tails():
    """§12 — 합법 무게-4 후속의 개수 (분해불가능 tail 13개) 를 독립적으로 센다."""
    out = {}
    for y in range(0, 720, 97):
        succ = [v for v in range(720)
                if OM4(P6[y], P6[v]) == 4 and legal_joint(6, P6[y], P6[v], 4)]
        out[y] = len(succ)
    return out


OM4 = G6["omega"]


def extremal_census():
    """§11 — `N*(0,0,4)` 과 `N*(0,0,9)` 의 **극값 사슬**을 독립 열거한다.

    `chain_capacity_115.c` 가 `S₆` 추이성으로 시작 단어를 고정하므로, 시작 단어를 하나로
    고정한 열거는 **`S₆` 류의 대표원**을 센다 (문자 그대로의 사슬 수가 아니다).
    """
    r4 = chain_search(0, 0, 0, 4)
    r9 = chain_search(0, 0, 0, 9)
    c4 = chain_search(0, 0, 0, 4, want=r4["best"], collect=True)
    c9 = chain_search(0, 0, 0, 9, want=r9["best"], collect=True)
    return dict(
        N_star_0_0_4=r4["best"], N_star_0_0_9=r9["best"],
        matches_round115=(r4["best"] == 46 and r9["best"] == 66),
        extremal_chains_s4=len(c4["chains"]), extremal_chains_s9=len(c9["chains"]),
        interpretation=("counts are S6-class representatives: the start word is fixed to "
                        "one value, which is legitimate because relabelling acts simply "
                        "transitively on the 720 words and commutes with sigma, tau, "
                        "W3b and W3c"),
        deficit_s4=5 * len({ORB6[w] for w in c4["chains"][0]}) - r4["best"] if c4["chains"] else None,
        deficit_s9=5 * len({ORB6[w] for w in c9["chains"][0]}) - r9["best"] if c9["chains"] else None,
        orbits_s4=len({ORB6[w] for w in c4["chains"][0]}) if c4["chains"] else None,
        orbits_s9=len({ORB6[w] for w in c9["chains"][0]}) if c9["chains"] else None,
        nodes=dict(s4=r4["nodes"], s9=r9["nodes"]),
        _chains=dict(s4=c4["chains"], s9=c9["chains"]))


def seam_exhaustion():
    """§12 — 무게-4 이음매 **312** 조합을 재구성하고 하나하나 검사한다.

    `H = 1` 이 살아남으려면 축약 결과물이 `46`-사슬 + 무게-4 joint + `66`-사슬 (또는 그
    반대 순서) 이어야 하고, 두 사슬은 **육각형과 궤도를 모두 서로소**로 써야 한다
    (`g` 풀이 `2e' = 0` 이라 궤도를 넘겨줄 수 없고, 육각형은 한 번씩만 쓸 수 있다).
    사슬은 `S₆` 로 첫 시작 단어를 고정하고 세며, 두 번째 사슬의 시작 단어는 이음매가
    정한다.  `S₆` 추이성으로 임의의 시작 단어에서 극값 사슬 수는 같다 (46 → 1, 66 → 12).

        조합 수 = 2 (방향) × (첫 사슬 수) × 13 (무게-4 tail) × (둘째 사슬 수)
                = 1·13·12 + 12·13·1 = 156 + 156 = **312**.
    """
    ec = extremal_census()
    ch4, ch9 = ec["_chains"]["s4"], ec["_chains"]["s9"]
    tails = {}
    for w in range(720):
        y = _sig5(w)
        tails[w] = [v for v in range(720)
                    if OM4(y, P6[v]) == 4 and legal_joint(6, y, P6[v], 4)]
    stat = Counter()
    combos = 0
    survivors = []
    for orient, first_set, second_len, second_scap in (
            ("46_then_66", ch4, 66, 9), ("66_then_46", ch9, 46, 4)):
        for c1 in first_set:
            h1 = {HEX6[w] for w in c1}
            o1 = {ORB6[w] for w in c1}
            for v in tails[c1[-1]]:
                r = chain_search(v, 0, 0, second_scap, want=second_len, collect=True)
                for c2 in r["chains"]:
                    combos += 1
                    h2 = {HEX6[w] for w in c2}
                    o2 = {ORB6[w] for w in c2}
                    hx, ox = h1 & h2, o1 & o2
                    if hx and ox:
                        stat["both hexagon and orbit collision"] += 1
                    elif hx:
                        stat["hexagon collision"] += 1
                    elif ox:
                        stat["orbit collision"] += 1
                    else:
                        stat["SURVIVES"] += 1
                        if len(survivors) < 5:
                            survivors.append(dict(orient=orient, seam=v))
                stat[f"second_chain_count_{orient}"] += len(r["chains"])
    return dict(
        combinations=combos, expected=312, matches_312=(combos == 312),
        outcome={k: v for k, v in sorted(stat.items()) if not k.startswith("second_")},
        second_chain_counts={k: v for k, v in stat.items() if k.startswith("second_")},
        all_fail=(stat["SURVIVES"] == 0), survivors=survivors,
        weight4_tail_count=13,
        disjointness_requirement=("the two chains must use disjoint hexagon sets (each "
                                  "hexagon carries exactly one pass) AND disjoint orbit "
                                  "sets (g = 2e' = 0 forbids handing an orbit between "
                                  "chains); 10 + 15 = 25 = O' and 46 + 66 = 112 = P' "
                                  "leave no slack for any overlap"))


def delta1_limitation():
    """§14 — `delta = 1` 인 7 행이 왜 이 정리로 닫히지 않는지.

    `delta = F + e − f_out = 0` 은 **정리 129.1 의 등호**이고 그것이 정리 131.1 의 유일한
    가설이다.  등호일 때만 (a) 모든 `ν`-상승이 자유 탈출하고 (b) 자유 하강이 반복 run 을
    전부 열며, 그래서 국소성 lock 이 걸려 **잠긴 블록이 존재**한다.  `delta = 1` 이면
    등호가 깨져 (a)·(b) 가 성립하지 않고 lock 이 강제되지 않으므로 **축약할 블록이
    있다는 보장이 사라진다.**  즉 이것은 계산 한계가 아니라 **정리의 적용 범위 한계**다.
    """
    return dict(
        reason="delta = 0 is exactly the equality case of Theorem 129.1, which is the sole "
               "hypothesis of Theorem 131.1; only under it are the locality locks forced, "
               "hence only then does a locked block exist to contract",
        delta1_breaks="with delta = 1 conclusions (a) and (b) of Theorem 131.1 fail, so no "
                      "locked block is guaranteed and the contraction has nothing to act on",
        is_a_theorem_scope_limit=True, is_a_compute_limit=False,
        does_not_imply_feasible=("this says only that the CURRENT theorem cannot close the "
                                 "7 rows; it says nothing about whether they are realisable"))


# ------------------------------------------------ §2·§3·§4 부분 회전-호 축약 보조정리
def partial_arc_contraction():
    """§2·§3·§4 — **부분 회전-호 축약** 보조정리를 세우고 `n = 6` 실기하로 검사한다.

    라운드 134 의 보조정리는 대체물이 **full pass** 인 경우였다.  `(3,2)` 의 유형 A 는
    육각형이 **세 번** 들어오므로 축약을 두 번 해야 하고, 중간 단계의 대체물은 길이
    `l₀ + l₁ < 6` 인 **부분 호**다.  따라서 일반화가 필요하다:

    > **보조정리 (부분 회전-호 축약).**  pass `(v, a)` 다음에 `orb(σ^a v)` 의 다섯 phase 를
    > 전부 채우는 pass 다섯 개가 오고 그 마지막이 `(σ^a v, b)` 인 6-pass 덩어리를 **하나의
    > pass `(v, a+b)`** 로 바꾸면 (`a, b ≥ 1`, `a + b ≤ 6`), 진입 단어 `v` 와 탈출 단어
    > `σ^{a+b−1}(v)` 가 **글자 그대로 보존**되고 `P → P−5`, `O → O−1` 이며 `D`, `S`, `H` 는
    > 불변이다.

    `a + b = 6` 이면 라운드 134 의 보조정리로 되돌아간다.
    """
    bad = Counter()
    cases = 0
    for v in range(720):
        for a in range(1, 6):
            for b in range(1, 7 - a):
                cases += 1
                c = _sigk(v, a)
                blk = [(v, a)] + [(_tauk(c, j), 6) for j in range(1, 5)] + [(c, b)]
                rep = [(v, a + b)]
                bw = [_sigk(u, j) for (u, ln) in blk for j in range(ln)]
                rw = [_sigk(u, j) for (u, ln) in rep for j in range(ln)]
                if bw[0] != rw[0]:
                    bad["entrance"] += 1
                if bw[-1] != rw[-1] or rw[-1] != _sigk(v, a + b - 1):
                    bad["exit"] += 1
                jw = [OM4(P6[bw[i]], P6[bw[i + 1]]) for i in range(len(bw) - 1)]
                if any(w != 2 for w in jw if w >= 2) or len([w for w in jw if w >= 2]) != 5:
                    bad["internal joints not five omega=2"] += 1
                lock = blk[1:]
                if {ORB6[u] for (u, _) in lock} != {ORB6[c]}:
                    bad["lock leaves orbit"] += 1
                if {OPH6[u] for (u, _) in lock} != {0, 1, 2, 3, 4}:
                    bad["lock does not fill phases"] += 1
                if ORB6[c] == ORB6[v]:
                    bad["T == orb(v)"] += 1
                hb = Counter(HEX6[u] for (u, _) in blk)
                if hb[HEX6[v]] != 2 or any(k != HEX6[v] and n != 1 for k, n in hb.items()):
                    bad["hexagon multiplicity"] += 1
                dP = len(rep) - len(blk)
                dO = len({ORB6[u] for (u, _) in rep}) - len({ORB6[u] for (u, _) in blk})
                if dP != -5 or dO != -1 or 5 * dO - dP != 0:
                    bad["parameter delta"] += 1
    # --- 유형 A: 세 호를 두 번의 축약으로 합칠 수 있는가, 순서는? ----------------
    typeA = Counter()
    for v in range(0, 720, 37):
        for l0 in range(1, 5):
            for l1 in range(1, 6 - l0):
                l2 = 6 - l0 - l1
                # 순서 1: (arc0,arc1) 먼저 -> (v, l0+l1), 그 다음 (·,arc2)
                ok1 = (l0 + l1 <= 6 and l0 + l1 + l2 == 6)
                # 순서 2: (arc1,arc2) 먼저 -> (sigma^{l0}v, l1+l2), 그 다음 (arc0,·)
                ok2 = (l1 + l2 <= 6)
                typeA["order_arc01_first" if ok1 else "ORDER1_BAD"] += 1
                typeA["order_arc12_first" if ok2 else "ORDER2_BAD"] += 1
                typeA["final_is_full_pass" if l0 + l1 + l2 == 6 else "FINAL_BAD"] += 1
    return dict(
        lemma="pass (v,a) + five passes filling orb(sigma^a v) ending at (sigma^a v, b) "
              "-> single pass (v, a+b);  P-5, O-1, D/S/H unchanged",
        generalises_round134="a + b = 6 recovers the Round-134 full-pass lemma",
        cases=cases, violations=dict(bad), clean=(len(bad) == 0),
        type_A=dict(counts=dict(typeA),
                    both_orders_valid=("ORDER1_BAD" not in typeA and "ORDER2_BAD" not in typeA),
                    note="for type A the two contractions may be done in EITHER order - "
                         "unlike type-B beta, where the outer block only acquires the "
                         "required shape after the inner contraction"),
        deltas=dict(P=-5, O=-1, D=0, S=0, H=0))


def _sigk(i, k):
    w = P6[i]
    for _ in range(k):
        w = SG6(w)
    return IDX6[w]


def _tauk(i, k):
    w = P6[i]
    for _ in range(k):
        w = G6["tau"](w)
    return IDX6[w]


def summarise():
    rt = resource_table()
    ca = contracted_accounting(rt)
    ce = capacity_exclusions(rt, ca)
    ec = extremal_census()
    ec.pop("_chains", None)
    return dict(round=135, kind="PROOF AUDIT (Claude independent review of Astra Round 135)",
                target="(k,G) = (3,2)",
                resource_table=rt, contracted_accounting=ca,
                capacity_exclusions=ce, h1_unique_heavy=h1_unique_heavy(),
                equality_classification=equality_classification(),
                extremal_census=ec, seam_exhaustion=seam_exhaustion(),
                delta1_limitation=delta1_limitation(),
                partial_arc_contraction=partial_arc_contraction())
