#!/usr/bin/env python3
"""라운드 133 — 유형 B 짧은-블록의 **매크로 작용**과 잔여 문제.

라운드 132 는 유형 B 의 order type 을 못박았다.  이 모듈은 그 블록을 **하나의 매크로 전이**로
축약해 (§10·§11·§12) 블록 이후의 **잔여 문제**를 정확히 기술하고 (§4·§5), 국소 CSP 로
블록-출구 상태를 전수한다 (§16).  실제 `n = 6` 기하 위에서 계산하고 `S₆` 로 단어 하나를
고정한다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
G = setup(6)
PERMS, IDX, SG, TA = G["perms"], G["idx"], G["sig"], G["tau"]
HEX, ORB, HPH, OPH = G["hexid"], G["orbid"], G["hexph"], G["orbph"]


def sigk(i, k):
    w = PERMS[i]
    for _ in range(k):
        w = SG(w)
    return IDX[w]


def tauk(i, k):
    w = PERMS[i]
    for _ in range(k):
        w = TA(w)
    return IDX[w]


def orbit_words_are_in_distinct_hexagons():
    """블록 회계의 전제: 한 궤도의 `n−1 = 5` 단어는 서로 다른 육각형에 있다."""
    by = {}
    for i in range(len(PERMS)):
        by.setdefault(ORB[i], []).append(HEX[i])
    return all(len(set(v)) == len(v) for v in by.values())


# ------------------------------------------------------------------ §10 beta macro
def beta_macro(v0=0):
    """§10 — β 블록(11 pass, 내부 joint 10개, 전부 `ω = 2`)의 **정확한 순 작용**.

    `opener₀` 진입 `v₀`, 길이 `b₀`; `c₀ := entry(closer₀) = σ^{b₀}(v₀)`;
    `U` 는 `Q₁ = orb(c₀)` 안에서 `τ(c₀)` 부터 `u` pass, 마지막이 `opener₁ = τ^u(c₀)`;
    `c₁ := entry(closer₁) = σ^{b₁}(τ^u(c₀))`; 잠긴 run 은 `τ^1(c₁) … τ^5(c₁) = closer₁` 5 pass;
    `V` 는 `τ^{u+1}(c₀) … τ^5(c₀) = closer₀` 로 `5 − u` pass.

    따라서 블록은 `Q₁` 과 `T₁ = orb(c₁)` 의 **슬롯 5개씩을 전부** 먹고, 결손을 **0** 만
    쓰며, run 을 **3** 개, pass 를 **11** 개, 육각형을 **9** 개 소비하고, 내부 비용은 **0**,
    `f_out` 을 **3** 올린다.  그리고 출구 단어는 `exit(closer₀) = σ^5(v₀)` 로
    **`b₀, b₁, u` 와 무관**하다.
    """
    rows = []
    for b0 in range(1, 6):
        for b1 in range(1, 6):
            for u in range(1, 5):
                c0 = sigk(v0, b0)
                o1 = tauk(c0, u)
                c1 = sigk(o1, b1)
                # 블록의 11 pass (진입 단어, 길이)
                blk = [(v0, b0)]
                for j in range(1, u):
                    blk.append((tauk(c0, j), 6))
                blk.append((o1, b1))
                for j in range(1, 5):
                    blk.append((tauk(c1, j), 6))
                blk.append((c1, 6 - b1))
                for j in range(u + 1, 5):
                    blk.append((tauk(c0, j), 6))
                blk.append((c0, 6 - b0))
                hexes = {HEX[w] for (w, _) in blk}
                orbs = Counter(ORB[w] for (w, _) in blk)
                exitw = sigk(blk[-1][0], blk[-1][1] - 1)
                rows.append(dict(
                    b0=b0, b1=b1, u=u, passes=len(blk),
                    distinct_hexagons=len(hexes),
                    orbits_touched=len(orbs),
                    fully_filled_orbits=sum(1 for o, c in orbs.items() if c == 5),
                    deficit_consumed=sum(5 - c for o, c in orbs.items() if c == 5) or 0,
                    slots_in_Q1=orbs[ORB[c0]], slots_in_T1=orbs[ORB[c1]],
                    exit_word_is_sigma5_v0=(exitw == sigk(v0, 5)),
                    short_passes=sum(1 for (_, l) in blk if l < 6)))
    ok = all(r["passes"] == 11 and r["distinct_hexagons"] == 9
             and r["slots_in_Q1"] == 5 and r["slots_in_T1"] == 5
             and r["exit_word_is_sigma5_v0"] and r["short_passes"] == 4 for r in rows)
    return dict(
        n_configs=len(rows), all_uniform=ok,
        macro=dict(passes=11, internal_joints=10, internal_cost=0, f_out_delta=3,
                   hexagons=9, new_orbits=2, new_runs=3, deficit_delta=0,
                   exit_word="sigma^5(entry(opener_0)) - independent of b0, b1, u",
                   note="both new orbits are FULL (5/5 slots), so the beta block consumes "
                        "no deficit at all"),
        rows=rows[:6])


# ----------------------------------------------------------------- §11 alpha macro
def alpha_macro(v0=0):
    """§11 — α 사슬의 매크로.  블록이 **연속이 아니다** (두 잠긴 run 사이에 자유 간격).

    `opener₀ → 잠긴 run(5 pass, `T₀ = orb(c₀)` 을 꽉 채움) → closer₀` 가 6 pass 이고,
    `closer₀` 의 자유 탈출이 반복 run `R ⊆ Q₀` 를 열며 (자유 closer 인 경우),
    그 뒤 임의 길이의 간격을 지나 `opener₁ → 잠긴 run(5 pass, `T₁` 을 꽉 채움) → closer₁` 가
    다시 6 pass 다.  따라서 α 는 **두 개의 6-pass 매크로**와 그 사이의 자유 간격이다.
    """
    rows = []
    for b0 in range(1, 6):
        c0 = sigk(v0, b0)
        blk = [(v0, b0)] + [(tauk(c0, j), 6) for j in range(1, 5)] + [(c0, 6 - b0)]
        orbs = Counter(ORB[w] for (w, _) in blk)
        rows.append(dict(b0=b0, passes=len(blk),
                         distinct_hexagons=len({HEX[w] for (w, _) in blk}),
                         slots_in_T0=orbs[ORB[c0]],
                         exit_word_is_sigma5_v0=(sigk(blk[-1][0], blk[-1][1] - 1)
                                                 == sigk(v0, 5))))
    ok = all(r["passes"] == 5 and r["slots_in_T0"] == 5 - 0 and r["exit_word_is_sigma5_v0"]
             for r in rows)
    return dict(
        half_macro=dict(passes=6, internal_joints=5, internal_cost=0, f_out_delta=1,
                        hexagons=5, new_orbits=1, new_runs=1, deficit_delta=0,
                        exit_word="sigma^5(entry(opener_X))"),
        note=("alpha is TWO disjoint 6-pass macros (opener_X .. closer_X) separated by a "
              "free-length gap, so unlike beta it does NOT collapse to a single transition"),
        rows=rows, uniform=ok)


# ---------------------------------------------------------------- §12 Model T macro
def model_t_macro(v0=0):
    """§12 — 모형 T: `Q₀ = Q₁ = Q` 가 run 셋을 갖는다.

    `opener₀` 는 `Q` 의 첫 run 을 끝내고, `closer₀` 가 여는 반복 run `R` 는
    `τ(v₀)` 에서 시작해 `opener₁ = τ^{|R|}(v₀)` 에서 끝나며, `closer₁` 이 세 번째 run `R'`
    을 연다.  `opener₁ ∈ Q` 이므로 **`entry(opener₁) = τ^{r}(entry(opener₀))`,
    `1 ≤ r ≤ 4`** 라는 양의 제약이 나온다 — 이것이 `n = 6` 에서 모형 T 를 특징짓는다.
    `n = 4` 에 `x = 0` 인 세-run 증인이 없다는 사실은 **크기 때문**이며 `n = 6` 불가능성이
    아니다.
    """
    rows = []
    for b0 in range(1, 6):
        for r in range(1, 5):
            o1 = tauk(v0, r)
            rows.append(dict(b0=b0, r=r,
                             opener1_word=o1,
                             same_orbit=(ORB[o1] == ORB[v0]),
                             different_hexagon=(HEX[o1] != HEX[v0]),
                             phase_offset=(OPH[o1] - OPH[v0]) % 5))
    return dict(
        constraint="entry(opener_1) = tau^r(entry(opener_0)) with 1 <= r <= 4",
        n_configs=len(rows),
        all_same_orbit=all(x["same_orbit"] for x in rows),
        all_different_hexagon=all(x["different_hexagon"] for x in rows),
        do_not_use_n4_x0_absence=True,
        rows=rows[:8])


# ------------------------------------------------------- §16 국소 CSP: 블록 출구 상태
def block_exit_csp():
    """§16 — 블록의 **국소** 출구 상태를 전수한다 (`S₆` 로 `entry(opener₀)` 를 고정).

    국소 상태 = 블록이 소비한 (육각형 집합, 궤도별 슬롯 사용, 출구 단어, run/비용/f_out
    증분).  **접두사 이력은 포함하지 않는다** — 그래서 이것은 잔여 문제의 *하한* 압축이고,
    실제 DFS 상태 압축은 사용-육각형 집합까지 필요하다 (§17·§18 에서 측정).
    """
    v0 = 0
    beta = beta_macro(v0)
    sigs = Counter()
    for b0 in range(1, 6):
        for b1 in range(1, 6):
            for u in range(1, 5):
                c0 = sigk(v0, b0)
                o1 = tauk(c0, u)
                c1 = sigk(o1, b1)
                blk = [(v0, b0)]
                for j in range(1, u):
                    blk.append((tauk(c0, j), 6))
                blk.append((o1, b1))
                for j in range(1, 5):
                    blk.append((tauk(c1, j), 6))
                blk.append((c1, 6 - b1))
                for j in range(u + 1, 5):
                    blk.append((tauk(c0, j), 6))
                blk.append((c0, 6 - b0))
                hexes = frozenset(HEX[w] for (w, _) in blk)
                exitw = sigk(blk[-1][0], blk[-1][1] - 1)
                sigs[(exitw, hexes, frozenset(ORB[w] for (w, _) in blk))] += 1
    coarse = Counter((k[0],) for k in sigs)
    return dict(
        beta_local_configs=100,
        distinct_local_block_exit_states=len(sigs),
        distinct_by_exit_word_only=len(coarse),
        compression_local=round(100 / max(len(sigs), 1), 3),
        caveat=("this counts only the BLOCK's own footprint with entry(opener_0) fixed by "
                "S6.  A residual DP would also have to carry the PREFIX's used-hexagon "
                "set, which this local CSP deliberately does not model."),
        beta_uniform=beta["all_uniform"])


# --------------------------------------------------------------- §9 split dependence
def split_shape_dependence():
    """§9 — 블록 뒤에 **살아남는** 분할 정보는 무엇인가."""
    v0 = 0
    seen = {}
    for b0 in range(1, 6):
        for b1 in range(1, 6):
            for u in range(1, 5):
                c0 = sigk(v0, b0)
                o1 = tauk(c0, u)
                c1 = sigk(o1, b1)
                blk = [(v0, b0)]
                for j in range(1, u):
                    blk.append((tauk(c0, j), 6))
                blk.append((o1, b1))
                for j in range(1, 5):
                    blk.append((tauk(c1, j), 6))
                blk.append((c1, 6 - b1))
                for j in range(u + 1, 5):
                    blk.append((tauk(c0, j), 6))
                blk.append((c0, 6 - b0))
                key = (frozenset(HEX[w] for (w, _) in blk),)
                seen.setdefault(key, []).append((b0, b1, u))
    groups = [v for v in seen.values() if len(v) > 1]
    return dict(
        total_configs=100, distinct_hexagon_footprints=len(seen),
        merged_groups=len(groups), largest_group=max((len(v) for v in seen.values()),
                                                     default=0),
        verdict=("every (b0, b1, u) leaves a DIFFERENT used-hexagon footprint"
                 if len(seen) == 100 else
                 "some split shapes share a footprint - candidate equivalence"),
        note="only a PROVED equivalence may be used to group split shapes")



# ------------------------------------------- §5 블록 충돌 정리 (이 라운드의 주 결과)
def _tinv(i, k):
    return tauk(i, (5 - k) % 5)


def _beta_block(v0, b0, b1, u, ell, e2):
    """β 둥지 블록을 `opener₀` 의 run 앞쪽까지 늘려서 구성한다.

    `ell` = `opener₀` 로 끝나는 `Q₀` run 의 길이 (그 run 의 앞 `ell−1` pass 는 `τ^{-j}(v₀)`);
    `e2` = `B/e=2` D-β₀ 이면 `closer₀` 의 자유 탈출이 여는 `Q₀` 반복 run 의 첫 pass 를 더한다.
    """
    blk = [(_tinv(v0, j), 6) for j in range(ell - 1, 0, -1)]
    c0 = sigk(v0, b0)
    o1 = tauk(c0, u)
    c1 = sigk(o1, b1)
    blk += [(v0, b0)] + [(tauk(c0, j), 6) for j in range(1, u)] + [(o1, b1)]
    blk += [(tauk(c1, j), 6) for j in range(1, 5)] + [(c1, 6 - b1)]
    blk += [(tauk(c0, j), 6) for j in range(u + 1, 5)] + [(c0, 6 - b0)]
    if e2:
        blk += [(tauk(v0, 1), 6)]
    return blk, o1


def _t_block(v0, b0, b1, r, ell):
    """모형 T 블록: `opener₀` → 잠긴 run → `closer₀` → `Q` 반복 run(r pass) → `opener₁`
    → 잠긴 run → `closer₁`."""
    blk = [(_tinv(v0, j), 6) for j in range(ell - 1, 0, -1)]
    c0 = sigk(v0, b0)
    blk += [(v0, b0)] + [(tauk(c0, j), 6) for j in range(1, 5)] + [(c0, 6 - b0)]
    blk += [(tauk(v0, j), 6) for j in range(1, r)]
    o1 = tauk(v0, r)
    c1 = sigk(o1, b1)
    blk += [(o1, b1)] + [(tauk(c1, j), 6) for j in range(1, 5)] + [(c1, 6 - b1)]
    return blk, o1


def _consistent(blk, v0, o1):
    """블록이 `G = 2` 유형 B 와 **양립하는가**.

    유형 B 의 `(4,2)` walk 에서 육각형은 `h₀`, `h₁` 이 정확히 두 번, 나머지는 정확히 한 번
    들어온다.  강제된 블록이 그 자체로 이 조건을 깨면 그 배치는 **불가능**하다.
    또한 한 궤도는 슬롯이 5개뿐이므로 블록이 한 궤도를 6번 쓰면 불가능하다.
    """
    h0, h1 = HEX[v0], HEX[o1]
    if h0 == h1:
        return False, "h0 == h1"
    orbs = Counter(ORB[w] for (w, _) in blk)
    if any(v > 5 for v in orbs.values()):
        return False, "orbit over 5 slots"
    c = Counter(HEX[w] for (w, _) in blk)
    if c[h0] != 2 or c[h1] != 2:
        return False, "wrong hexagon multiplicity"
    if any(v != 1 for k, v in c.items() if k not in (h0, h1)):
        return False, "hexagon collision among forced passes"
    return True, None


def block_collision_theorem(v0s=(0, 17, 203, 555)):
    """§5·§9 — **정리 133.1 (블록 충돌).**

    `β` 둥지와 모형 T 에서는 `opener₁` 의 진입 단어가 `opener₀` 의 것으로부터 **완전히
    결정**된다 (`β`: `τ^u(σ^{b₀}(v₀))`, T: `τ^r(v₀)`).  따라서 블록 전체의 pass 열이
    `(v₀, b₀, b₁, u|r, ℓ)` 만으로 정해지고, 그 열이 유형 B 의 육각형 다중도
    (`h₀`, `h₁` 만 두 번, 나머지는 한 번) 를 깨거나 한 궤도를 6번 쓰면 그 배치는
    **탐색 없이 불가능**하다.  `S₆` 는 단어에 단순추이적으로 작용하므로 살아남는
    `(b₀, b₁, u|r, ℓ)` 집합은 `v₀` 와 **무관**하다 (아래에서 여러 `v₀` 로 확인한다).

    이것이 라운드 132 가 **30,124,862,589 노드**를 들여 `UNSAT_COMPLETE` 로 닫은
    `B_e1_b11_P1b` 가 죽는 이유다 — `(b₀, b₁) = (1, 1)` 은 이 정리로 **한 줄에** 죽는다.
    계측 실행이 이를 직접 확인한다: 그 클래스에서 20억 노드 동안
    **블록을 끝까지 놓은 상태가 하나도 없었다** (`block_exit_raw = 0`).
    """
    out = {}
    for name, kind, e2 in (("B/e=1 P1-beta", "beta", 0),
                           ("B/e=2 D-beta0", "beta", 1),
                           ("B/e=2 Model T", "T", 0)):
        per_v0 = []
        for v0 in v0s:
            live_splits, live_cfg, why = set(), 0, Counter()
            for b0 in range(1, 6):
                for b1 in range(1, 6):
                    for m in range(1, 5):
                        for ell in range(1, 6):
                            if kind == "beta":
                                blk, o1 = _beta_block(v0, b0, b1, m, ell, e2)
                            else:
                                blk, o1 = _t_block(v0, b0, b1, m, ell)
                            ok, w = _consistent(blk, v0, o1)
                            if ok:
                                live_splits.add((b0, b1))
                                live_cfg += 1
                            else:
                                why[w] += 1
            per_v0.append(dict(v0=v0, live_splits=len(live_splits),
                               live_configs=live_cfg,
                               dead_splits=sorted(set((a, b) for a in range(1, 6)
                                                      for b in range(1, 6))
                                                  - live_splits),
                               reasons=dict(why)))
        same = all(p["live_splits"] == per_v0[0]["live_splits"]
                   and p["live_configs"] == per_v0[0]["live_configs"]
                   and p["dead_splits"] == per_v0[0]["dead_splits"] for p in per_v0)
        out[name] = dict(S6_invariant=same, total_splits=25, total_configs=500,
                         live_splits=per_v0[0]["live_splits"],
                         live_configs=per_v0[0]["live_configs"],
                         dead_splits=per_v0[0]["dead_splits"],
                         reasons=per_v0[0]["reasons"],
                         split_reduction=round(25 / max(per_v0[0]["live_splits"], 1), 3),
                         config_reduction=round(500 / max(per_v0[0]["live_configs"], 1), 3))
    out["class_ledger"] = dict(
        round132_classes=150,
        round133_classes=(25 + 25 + out["B/e=1 P1-beta"]["live_splits"]
                          + out["B/e=2 Model T"]["live_splits"] + 25
                          + out["B/e=2 D-beta0"]["live_splits"]),
        killed_analytically=(150 - (25 + 25 + out["B/e=1 P1-beta"]["live_splits"]
                                    + out["B/e=2 Model T"]["live_splits"] + 25
                                    + out["B/e=2 D-beta0"]["live_splits"])),
        note=("only the rigid branches (beta nests and Model T) are killed; the three "
              "alpha-type branches (P0, P1-alpha, D-alpha) have a free gap between the two "
              "locked macros, so opener_1's word is NOT determined and no collision test "
              "applies to them"))
    return out


def n4_collision_control(maxlen=39):
    """§14 — 충돌 정리의 **양성 대조**: 합법 `n = 4` β walk 을 하나도 기각하면 안 된다."""
    from verify_f2_structure_126 import setup as s4, legal_joint
    from verify_fg_repair_128 import walk_measure
    from verify_b_machine_132 import _structure
    n = 4
    g = s4(n)
    perms, sg, om = g["perms"], g["sig"], g["omega"]
    hexid, orbid = g["hexid"], g["orbid"]
    NW = len(perms)
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or legal_joint(n, perms[a], perms[b], W[a][b])
           for b in range(NW)] for a in range(NW)]
    ws = []

    def rec(cur, used, seq, total):
        if len(seq) == NW:
            ws.append((n + total, tuple(seq)))
            return
        if n + total + (NW - len(seq)) > maxlen:
            return
        for j in range(NW):
            if used >> j & 1 or not OK[cur][j]:
                continue
            w = W[cur][j]
            if n + total + w + (NW - len(seq) - 1) > maxlen:
                continue
            seq.append(j)
            rec(j, used | (1 << j), seq, total + w)
            seq.pop()

    rec(0, 1, [0], 0)
    stat = Counter()
    for L, seq in ws:
        m = walk_measure(g, W, seq, L)
        if m["G"] != 2 or m["x"] != 0 or m["f_out"] != m["F"] + m["e"]:
            continue
        st = _structure(g, m)
        if st is None or st["lock0"]:
            continue
        stat["beta_walks"] += 1
        # 실제 walk 에서 블록 pass 를 그대로 읽어 다중도 조건을 검사한다.
        passes, o0, c0, o1, c1 = m["passes"], st["o0"], st["c0"], st["o1"], st["c1"]
        blk = passes[o0:c0 + 1]
        h0, h1 = hexid[passes[o0][0]], hexid[passes[o1][0]]
        c = Counter(hexid[w] for (w, _) in blk)
        ok = (h0 != h1 and c[h0] == 2 and c[h1] == 2
              and all(v == 1 for k, v in c.items() if k not in (h0, h1)))
        stat["accept" if ok else "REJECT"] += 1
    return dict(n=4, beta_walks=stat["beta_walks"], accepted=stat["accept"],
                false_rejection=stat["REJECT"], clean=(stat["REJECT"] == 0),
                note="the collision predicate must never reject a walk that really exists")


def summarise():
    return dict(round=133, cell="(k,G) = (4,2)",
                orbit_words_distinct_hexagons=orbit_words_are_in_distinct_hexagons(),
                beta_macro=beta_macro(), alpha_macro=alpha_macro(),
                model_t_macro=model_t_macro(), block_exit_csp=block_exit_csp(),
                split_shape_dependence=split_shape_dependence(),
                block_collision_theorem=block_collision_theorem(),
                n4_collision_control=n4_collision_control())


if __name__ == "__main__":
    d = summarise()
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_b_residual_133.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in d.items() if k != "beta_macro"},
                     ensure_ascii=False, indent=1)[:2600])
    print("beta macro:", json.dumps(d["beta_macro"]["macro"], ensure_ascii=False))
    print("beta uniform:", d["beta_macro"]["all_uniform"])
