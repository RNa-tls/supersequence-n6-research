#!/usr/bin/env python3
"""라운드 128 — `F` 와 `G` 의 분리와 기초 수리.

프로젝트는 두 개의 서로 다른 양을 같은 것으로 써 왔다.

    F  := **abandonment 수**.  레거시 엔진 `superperm_partial_f1.py::extend` 의 정의:
          무게 ≥ 2 인 joint 에서 `abandonment = not state.visited(sigma(p))`,
          즉 "pass 가 끝난 단어 `p` 의 회전 후속이 **아직 방문되지 않았다**" 는 것.
          (방문돼 있었다면 회전이 **막힌** 것이라 abandonment 가 아니다.)

    G  := **다중도 초과** = `P − n!/n` = `Σ_h (e_h − 1)`,  `e_h` = 육각형 `h` 의 진입 횟수.

이 모듈은 다음을 처음부터 유도하고 전수로 확인한다.

    F = ν-상승(ascent) 의 개수,        G = Σ_h (m_h − 1),        J := G − F = Σ_h (d_h − 1)

여기서 `ν` 는 라운드 126 의 **육각형 후속 치환**(순환이 곧 육각형, 순환 길이 `m_h = e_h`),
`d_h` 는 `h` 의 `ν`-순환에서 walk 순서 기준 **하강(descent)** 의 개수다.
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup, legal_joint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

CODEX_N4 = "012302310232103213012031202301320130213"


# --------------------------------------------------------------------- §1 definitions
def definitions():
    return {
        "P": "number of passes = number of maximal rotation runs = (#joints) + 1",
        "e_h": "number of times hexagon h is entered = number of passes lying in h",
        "G": ("multiplicity excess := P - n!/n = sum_h (e_h - 1); every hexagon is entered "
              "at least once and sum_h e_h = P, and there are n!/n hexagons"),
        "F": ("abandonment count.  At a joint leaving the pass-end word p the legacy engine "
              "sets abandonment = NOT visited(sigma(p)): the pass stopped rotating while its "
              "rotation successor was still unvisited.  If sigma(p) was already visited the "
              "rotation was BLOCKED and it is not an abandonment."),
        "nu": ("hexagon-successor permutation on passes (Round 126): nu(p) is the pass whose "
               "entry word is sigma^{len(p)}(entry(p)) = sigma(exit(p)); its cycles are "
               "exactly the hexagons, with cycle length e_h"),
        "S": "#{joints with omega >= 3}",
        "H": "sum over joints of (omega - 3)_+",
        "O": "number of tau-orbits touched",
        "k": "O - n!/(n(n-1))   (24 at n = 6)",
        "D": "(n-1)O - P   -- the orbit deficit",
        "r": "number of runs = maximal blocks of consecutive passes in the same orbit",
        "e": "r - O = sum_q (runs(q) - 1)",
        "x": "#{intra-run joints with omega >= 3}",
        "f_out": "#{inter-run joints with omega = 2}   (free exits)",
        "N": "see section 13 - the historical definition S + F - O is the one in question",
    }


def fg_theory():
    """### 정리 128.1 — `F` 와 `G` 의 정확한 관계

    `p` 의 탈출 joint 에서 `sigma(exit(p)) = entry(ν(p))` 이므로 (라운드 126 §5.2)

        **abandonment(p)  ⟺  entry(ν(p)) 가 아직 방문되지 않았다  ⟺  p < ν(p)** (walk 순서)

    이다.  walk 의 **마지막** pass 는 탈출 joint 가 없지만 `p < ν(p)` 도 성립할 수 없으므로
    (뒤에 아무 pass 도 없다) 예외가 아니다.  따라서

        **F = #{p : p < ν(p)}  =  ν-상승의 총 개수.**

    `m_h := e_h` 라 하고 `h` 의 `ν`-순환에서 하강 수를 `d_h` 라 하면 상승 수는 `m_h − d_h` 이고
    순환이므로 `d_h ≥ 1`(전부 상승이면 `p < ν(p) < … < p`).  `m_h = 1` 이면 `ν(p) = p` 라
    상승 0, `d_h = 1`.  따라서

        F = Σ_h (m_h − d_h) = P − Σ_h d_h,     G = P − n!/n,
        **J := G − F = Σ_h d_h − n!/n = Σ_h (d_h − 1) ≥ 0.**

    ### 따름정리 128.2 — 언제 `F = G` 인가

    * `m_h = 1` ⟹ `d_h = 1` ⟹ 기여 0.
    * `m_h = 2` ⟹ 두 pass 중 정확히 하나가 상승이므로 `d_h = 1` ⟹ **기여 0**.
    * `m_h ≥ 3` ⟹ `d_h ∈ {1, …, m_h − 1}` ⟹ 기여가 **양수일 수 있다**.

    따라서 **`J > 0` 이려면 세 번 이상 진입된 육각형이 있어야 한다.**  특히

        **G ≤ 1  ⟹  J = 0  ⟹  F = G**,
        **G = 2 이고 두 육각형이 두 번씩(유형 B) ⟹ J = 0 ⟹ F = G = 2**,
        **G = 2 이고 한 육각형이 세 번(유형 A) ⟹ F ∈ {1, 2}** — 대각선이 깨질 수 있다.
        **F = 0 ⟺ G = 0.**
    """
    return {
        "abandonment_iff": "abandonment(p) <=> p < nu(p) in walk order",
        "F": "F = #{p : p < nu(p)} = number of nu-ascents",
        "J": "J = G - F = sum_h (d_h - 1), d_h = number of nu-descents in hexagon h",
        "d_h_lower_bound": "d_h >= 1 for every hexagon (a full cycle cannot be all ascents)",
        "m1": "e_h = 1 => d_h = 1 => contributes 0 to J",
        "m2": "e_h = 2 => exactly one of the two passes is an ascent => d_h = 1 => contributes 0",
        "m3plus": "e_h >= 3 => d_h may exceed 1 => J may be positive",
        "J_positive_requires": "some hexagon entered at least THREE times",
        "G_le_1_implies_F_eq_G": True,
        "G2_typeB_implies_F_eq_G": True,
        "G2_typeA_allows_F_eq_1": True,
        "F0_iff_G0": True,
    }


# ----------------------------------------------------------- §15 counterexample dissection
def dissect(string, n=4):
    """§15 — 구체적 문자열에서 모든 좌표를 **독립적으로** 다시 계산한다."""
    g = setup(n)
    perms, idx, sg, ta, om = g["perms"], g["idx"], g["sig"], g["tau"], g["omega"]
    hexid, orbid, hexph = g["hexid"], g["orbid"], g["hexph"]
    s = [int(c) for c in string]
    L = len(s)
    # 1. permutation windows in order
    wins = []
    for i in range(L - n + 1):
        w = tuple(s[i:i + n])
        if len(set(w)) == n:
            wins.append((i, w))
    seq = [idx[w] for _, w in wins]
    ok_all = (sorted(seq) == list(range(len(perms))))
    # 2. joints and passes
    oms = [om(perms[seq[i]], perms[seq[i + 1]]) for i in range(len(seq) - 1)]
    passes, cur, start = [], 1, seq[0]
    for i, w in enumerate(oms):
        if w >= 2:
            passes.append((start, cur))
            cur = 1
            start = seq[i + 1]
        else:
            cur += 1
    passes.append((start, cur))
    P = len(passes)
    joints = [w for w in oms if w >= 2]
    S = sum(1 for w in joints if w >= 3)
    H = sum(max(w - 3, 0) for w in joints)
    hx = [hexid[u] for (u, _) in passes]
    ecnt = Counter(hx)
    G = P - len(perms) // n
    # 3. nu and the ascent characterisation of F
    bypos = {}
    for i, (u, ln) in enumerate(passes):
        bypos[(hexid[u], hexph[u])] = i
    nu = []
    for (u, ln) in passes:
        z = perms[u]
        for _ in range(ln):
            z = sg(z)
        nu.append(bypos[(hexid[idx[z]], hexph[idx[z]])])
    F_ascents = sum(1 for i in range(P) if i < nu[i])
    # 4. the LEGACY engine's own definition, replayed step by step
    visited = set()
    F_engine = 0
    pos = 0
    for i, (u, ln) in enumerate(passes):
        w = perms[u]
        for _ in range(ln):
            visited.add(idx[w])
            w = sg(w)
        if i + 1 < P:                                   # this pass has an exit joint
            exitw = perms[passes[i][0]]
            for _ in range(passes[i][1] - 1):
                exitw = sg(exitw)
            rot = idx[sg(exitw)]
            if rot not in visited:
                F_engine += 1
    # 5. runs / orbits
    orbs = [orbid[u] for (u, _) in passes]
    runs, curr = [], [0]
    for i in range(1, P):
        if orbs[i] == orbs[i - 1]:
            curr.append(i)
        else:
            runs.append(curr)
            curr = [i]
    runs.append(curr)
    r = len(runs)
    O = len(set(orbs))
    k = O - len(perms) // (n * (n - 1))
    inter = {run[0] - 1 for run in runs[1:]}
    x = sum(1 for i, w in enumerate(joints) if i not in inter and w >= 3)
    f_out = sum(1 for i in inter if joints[i] == 2)
    d = {}
    for h, cnt in ecnt.items():
        ps = [i for i in range(P) if hx[i] == h]
        d[h] = sum(1 for i in ps if not (i < nu[i]))
    return dict(
        string=string, n=n, length=L,
        permutation_windows=len(wins), all_24_exactly_once=ok_all,
        all_joints_legal=all(legal_joint(n, perms[seq[i]], perms[seq[i + 1]], oms[i])
                             for i in range(len(oms))),
        P=P, G=G, F_by_ascents=F_ascents, F_by_engine_definition=F_engine,
        F_definitions_agree=(F_ascents == F_engine),
        J=G - F_ascents,
        multiplicity_partition=sorted((v - 1 for v in ecnt.values() if v >= 2), reverse=True),
        entry_counts={str(h): v for h, v in sorted(ecnt.items())},
        descents_by_hexagon={str(h): v for h, v in sorted(d.items())},
        sum_descents=sum(d.values()), n_hexagons=len(perms) // n,
        J_equals_sum_descents_minus_hexagons=(G - F_ascents == sum(d.values()) - len(perms) // n),
        S=S, H=H, O=O, k=k, r=r, e=r - O, x=x, f_out=f_out,
        L_from_844_plus_G=(len(perms) // n + n + len(perms) - 2 - len(perms) // n) if False else None,
        identity_L_with_G=(n + len(perms) - 2 + len(perms) // n + G + S + H),
        identity_L_with_F=(n + len(perms) - 2 + len(perms) // n + F_ascents + S + H),
        L_matches_G_identity=(L == n + len(perms) - 2 + len(perms) // n + G + S + H),
        L_matches_F_identity=(L == n + len(perms) - 2 + len(perms) // n + F_ascents + S + H),
        D=(n - 1) * O - P, D_equals_5k_minus_G=((n - 1) * O - P == (n - 1) * k - G),
        D_equals_5k_minus_F=((n - 1) * O - P == (n - 1) * k - F_ascents),
        master_with_G=(n + len(perms) - 2 + len(perms) // n
                       + len(perms) // (n * (n - 1)) - 1
                       + k + G + (r - O) + x + H - f_out),
        master_with_G_matches=(L == n + len(perms) - 2 + len(perms) // n
                               + len(perms) // (n * (n - 1)) - 1
                               + k + G + (r - O) + x + H - f_out))


# --------------------------------------------------------------- §16 (F, G) census
def walk_measure(g, W, seq, L):
    """walk 하나에서 `F` 와 `G` 를 **따로** 잰다 (하나를 다른 것으로 조건화하지 않는다)."""
    n = g["n"]
    perms, idx, sg = g["perms"], g["idx"], g["sig"]
    hexid, orbid, hexph = g["hexid"], g["orbid"], g["hexph"]
    NW = len(perms)
    oms = [W[seq[i]][seq[i + 1]] for i in range(len(seq) - 1)]
    passes, cur, start = [], 1, seq[0]
    for i, w in enumerate(oms):
        if w >= 2:
            passes.append((start, cur))
            cur = 1
            start = seq[i + 1]
        else:
            cur += 1
    passes.append((start, cur))
    P = len(passes)
    G = P - NW // n
    joints = [w for w in oms if w >= 2]
    S = sum(1 for w in joints if w >= 3)
    H = sum(max(w - 3, 0) for w in joints)
    hx = [hexid[u] for (u, _) in passes]
    ecnt = Counter(hx)
    bypos = {}
    for i, (u, ln) in enumerate(passes):
        bypos[(hexid[u], hexph[u])] = i
    nu = []
    for (u, ln) in passes:
        z = perms[u]
        for _ in range(ln):
            z = sg(z)
        nu.append(bypos[(hexid[idx[z]], hexph[idx[z]])])
    F = sum(1 for i in range(P) if i < nu[i])
    orbs = [orbid[u] for (u, _) in passes]
    runs, curr = [], [0]
    for i in range(1, P):
        if orbs[i] == orbs[i - 1]:
            curr.append(i)
        else:
            runs.append(curr)
            curr = [i]
    runs.append(curr)
    r, O = len(runs), len(set(orbs))
    k = O - NW // (n * (n - 1))
    inter = {run[0] - 1 for run in runs[1:]}
    x = sum(1 for i, w in enumerate(joints) if i not in inter and w >= 3)
    f_out = sum(1 for i in inter if joints[i] == 2)
    part = tuple(sorted((v - 1 for v in ecnt.values() if v >= 2), reverse=True))
    return dict(L=L, P=P, F=F, G=G, J=G - F, S=S, H=H, O=O, k=k, r=r, e=r - O,
                x=x, f_out=f_out, partition=part, max_e_h=max(ecnt.values()),
                nu=nu, passes=passes, hexes=hx)


def fg_census(n=4, maxlen=39):
    """§16 — 합법 walk 을 `(F, G)` **행렬**로 센다.  둘 중 하나로 조건화하지 않는다."""
    g = setup(n)
    perms, sg, om = g["perms"], g["sig"], g["omega"]
    NW = len(perms)
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or legal_joint(n, perms[a], perms[b], W[a][b])
           for b in range(NW)] for a in range(NW)]
    walks = []

    def dfs(cur, used, seq, total):
        if len(seq) == NW:
            walks.append((n + total, tuple(seq)))
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
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    dfs(0, 1, [0], 0)
    mat = Counter()
    parts_by_G = {}
    parts_by_F = {}
    viol = Counter()
    Lbase = n + NW - 2 + NW // n
    Omin = NW // (n * (n - 1))
    for L, seq in walks:
        m = walk_measure(g, W, seq, L)
        mat[(m["F"], m["G"])] += 1
        parts_by_G.setdefault(m["G"], Counter())[m["partition"]] += 1
        parts_by_F.setdefault(m["F"], Counter())[m["partition"]] += 1
        # --- the identities, both ways ---
        if L != Lbase + m["G"] + m["S"] + m["H"]:
            viol["L = L_base + G + S + H"] += 1
        if L != Lbase + m["F"] + m["S"] + m["H"]:
            viol["L = L_base + F + S + H (the OLD, wrong form)"] += 1
        if m["P"] != NW // n + m["G"]:
            viol["P = n!/n + G"] += 1
        if m["P"] != NW // n + m["F"]:
            viol["P = n!/n + F (the OLD, wrong form)"] += 1
        if (n - 1) * m["O"] - m["P"] != (n - 1) * m["k"] - m["G"]:
            viol["D = (n-1)k - G"] += 1
        if L != (Lbase + Omin - 1) + m["k"] + m["G"] + m["e"] + m["x"] + m["H"] - m["f_out"]:
            viol["master with G"] += 1
        # --- the F/G theory ---
        if m["F"] > m["G"]:
            viol["F <= G"] += 1
        if (m["F"] == 0) != (m["G"] == 0):
            viol["F = 0 <=> G = 0"] += 1
        if m["G"] <= 1 and m["F"] != m["G"]:
            viol["G <= 1 => F = G"] += 1
        if m["max_e_h"] <= 2 and m["F"] != m["G"]:
            viol["every e_h <= 2 => F = G"] += 1
        if m["J"] > 0 and m["max_e_h"] < 3:
            viol["J > 0 requires some e_h >= 3"] += 1
        mm = len(m["partition"])
        if m["F"] < mm:
            viol["F >= m (m = #multiply-entered hexagons)"] += 1
        if m["J"] > m["G"] - mm:
            viol["J <= G - m"] += 1
    return dict(
        n=n, maxlen=maxlen, walks=len(walks),
        FG_matrix={f"F{f}_G{gg}": c for (f, gg), c in sorted(mat.items())},
        G_gt_F=sum(c for (f, gg), c in mat.items() if gg > f),
        F_eq_G=sum(c for (f, gg), c in mat.items() if gg == f),
        by_F={str(f): sum(c for (ff, gg), c in mat.items() if ff == f)
              for f in sorted({f for f, _ in mat})},
        by_G={str(gg): sum(c for (ff, g2), c in mat.items() if g2 == gg)
              for gg in sorted({g2 for _, g2 in mat})},
        partitions_for_F2={str(p): c for p, c in sorted(parts_by_F.get(2, Counter()).items())},
        partitions_for_G2={str(p): c for p, c in sorted(parts_by_G.get(2, Counter()).items())},
        partitions_for_F1={str(p): c for p, c in sorted(parts_by_F.get(1, Counter()).items())},
        partitions_for_G1={str(p): c for p, c in sorted(parts_by_G.get(1, Counter()).items())},
        violations=dict(viol),
        corrected_identities_hold=all(
            kk not in viol for kk in ("L = L_base + G + S + H", "P = n!/n + G",
                                      "D = (n-1)k - G", "master with G")),
        old_identities_fail=("L = L_base + F + S + H (the OLD, wrong form)" in viol),
        fg_theory_holds=all(kk not in viol for kk in
                            ("F <= G", "F = 0 <=> G = 0", "G <= 1 => F = G",
                             "every e_h <= 2 => F = G", "J > 0 requires some e_h >= 3",
                             "F >= m (m = #multiply-entered hexagons)", "J <= G - m")))


# --------------------------------------------------- §3/§5/§12/§13 corrected identities
def corrected_identities(n=6):
    NW = 1
    for i in range(2, n + 1):
        NW *= i
    Lbase = n + NW - 2 + NW // n
    Omin = NW // (n * (n - 1))
    return {
        "P": {"old": "P = n!/n + F", "corrected": "P = n!/n + G",
              "why": "sum_h e_h = P over the n!/n hexagons, each entered at least once, so "
                     "P - n!/n = sum_h (e_h - 1) = G BY DEFINITION; F is the abandonment "
                     "count and only equals G when every hexagon's nu-cycle has exactly one "
                     "descent"},
        "L": {"old": f"L = {Lbase} + F + S + H", "corrected": f"L = {Lbase} + G + S + H",
              "why": "L = 725 + (#joints) + S + H and #joints = P - 1 = n!/n - 1 + G"},
        "D": {"old": "D = (n-1)k - F", "corrected": "D = (n-1)k - G",
              "why": "D := (n-1)O - P with O = O_min + k and P = n!/n + G"},
        "N": {"old": "N = S + F - O", "corrected": "N = S + G - O",
              "why": f"L = {Lbase} + G + S + H must equal {Lbase + Omin} + (k + N + H), and "
                     f"G + S = O + N requires N = S + G - O"},
        "master": {"old": f"L = {Lbase + Omin - 1} + k + F + e + x + H - f_out",
                   "corrected": f"L = {Lbase + Omin - 1} + k + G + e + x + H - f_out",
                   "why": "S = (r-1) + x - f_out is F- and G-free; substituting into "
                          "L = L_base + G + S + H gives the G form"},
        "theorem_A": {"old": "O <= 1 + S + F   <=>   f_out <= F + e + x",
                      "corrected": "O <= 1 + S + G   <=>   f_out <= G + e + x",
                      "why": "the algebraic equivalence uses S = (r-1) + x - f_out and "
                             "r = O + e, so O <= 1 + S + X  <=>  f_out <= X + e + x for any "
                             "X; the SLAB derivation needs the version whose X matches the "
                             "length identity, i.e. G.  The F-version is strictly STRONGER "
                             "(F <= G) and is NOT what the table needs.",
                      "note": "the two coincide exactly when J = 0"},
        "slab": {"old": "k + H <= 4 from S >= O - 1 - F and F + S + H <= 27",
                 "corrected": "k + H <= 4 from S >= O - 1 - G and G + S + H <= 27",
                 "why": "both substitutions cancel the G, so the BOUND k + H <= 4 is "
                        "unchanged - only its derivation is relabelled"},
        "cells": {"old": "55 cells indexed by (k, F)",
                  "corrected": "55 cells indexed by (k, G)",
                  "why": "the row bound is G <= (n-1)k from D >= 0 and the column bound is "
                         "k <= 4 from k + H <= 4; both are statements about G"},
    }


def slab_table(n=6):
    """§5 — 55칸 표를 `(k, G)` 로 다시 센다.  '55' 를 관례로 보존하지 않고 **다시 계산**한다."""
    rows = []
    for k in range(0, 5):                       # k + H <= 4 with H >= 0
        gmax = (n - 1) * k                      # D = (n-1)k - G >= 0
        rows.append(dict(k=k, O=24 + k, G_range=[0, gmax], n_cells=gmax + 1,
                         H_max=4 - k, N_plus_H_max=3 - k))
    total = sum(r["n_cells"] for r in rows)
    return dict(index="(k, G)  -- NOT (k, F)",
                rows=rows, total_cells=total, matches_historical_55=(total == 55),
                bounds=dict(G_le="(n-1)k   from D = (n-1)k - G >= 0",
                            k_le="4        from k + H <= 4 (Theorem A, G-form)"),
                exhaustive=("every walk has a well-defined (k, G), so the decomposition is "
                            "exhaustive; the FINITENESS (k <= 4) still rests on Theorem A, "
                            "which is proved only for G <= 2"),
                theorem_A_proved_for="G in {0, 1, 2}")


def j_cost_theory():
    """§14 — `J = G − F` 의 구조적 비용."""
    return {
        "J": "J = sum_h (d_h - 1), d_h = number of nu-descents in hexagon h",
        "per_hexagon_bound": "d_h - 1 <= e_h - 2, so J <= sum_{e_h>=2} (e_h - 2) = G - m",
        "m": "m = number of multiply-entered hexagons",
        "consequences": [
            "J <= G - m, hence F = G - J >= m: the abandonment count is at least the number "
            "of multiply-entered hexagons",
            "J > 0 requires some hexagon entered at least THREE times",
            "G = 0 => J = 0 => F = 0 (and conversely)",
            "G = 1 => m = 1, J <= 0 => J = 0 => F = 1",
            "G = 2 with two doubled hexagons (m = 2) => J <= 0 => F = 2",
            "G = 2 with one tripled hexagon (m = 1) => J <= 1, so F in {1, 2}"],
        "salvage": ("in the G <= 1 regime - which is exactly what every engine from Round 115 "
                    "through Round 125 searched - J is identically zero, so F = G there and "
                    "no result is affected by the collision beyond its NAME"),
        "no_length_cost": ("J does not appear in L = L_base + G + S + H, so a unit of J costs "
                           "no length by itself; the salvage comes from the multiplicity "
                           "requirement e_h >= 3, not from a length penalty"),
    }


def rounds_scope_table():
    """§8 — 라운드 116–125 의 **실제** 정리/탐색 영역."""
    G1 = ("B", "only G = 1  (equivalently F = 1 AND P = 121); the engines hard-code "
                "TARGET = 121 and never compute abandonment at all")
    return {
        "110": ("D", "foundation round - its counting proof substituted F for the "
                     "multiplicity excess at step 6; identities repaired in Round 128"),
        "114": ("C", "(k,G) = (0,0); G = 0 <=> F = 0 so both labels are correct"),
        "115": ("C", "the G = 0 column; verify_f0_geometry_115.py sets P = 120, i.e. G = 0. "
                     "G = 0 <=> F = 0, so the F = 0 label is ALSO correct - this column is "
                     "completely unaffected"),
        "116": ("B", "verify_f1_structure_116.py sets P = 121, i.e. G = 1"),
        "117": G1, "118": G1, "119": G1, "120": G1, "121": G1,
        "122": ("B", "compares generic G = 1 with the historical Q2 population, which is "
                     "itself a G = 1 model (TARGET_F = 1 AND TARGET_P = 121)"),
        "123": G1, "124": G1, "125": G1,
        "126": ("C", "its 'F' was computed as P - n!/n, i.e. it was G throughout; every "
                     "formula and every n = 4 verification is CORRECT as a statement about "
                     "G.  Only the name was wrong."),
        "127": ("C", "the type-B configuration is 'two hexagons each entered twice', a pure "
                     "multiplicity statement; the order proof never uses F.  Valid as a "
                     "local multiplicity lemma."),
        "_legend": {"A": "generic project F", "B": "only G = 1 (a strict subset of F = 1)",
                    "C": "actually a G statement regardless of F",
                    "D": "foundation - repaired"},
    }


def round_127_salvage():
    """§17 — 라운드 127 국소 정리를 다중도 언어로 다시 쓴다."""
    return {
        "old_name": "Theorem 127.1 (generic F = 2 type B)",
        "corrected_name": "Theorem 127.1 (two doubled hexagons) - a LOCAL MULTIPLICITY lemma",
        "statement": ("let h and g be two distinct hexagons each entered exactly twice; if all "
                      "four of their passes exit by a free (omega = 2) arc, then at least two "
                      "orbits carry an extra run, i.e. e >= 2"),
        "uses_F": False,
        "uses_G": False,
        "why_it_survives": ("the proof only uses: the nu-cycle structure on the passes of a "
                            "hexagon, the order lemma, the uniqueness of a run's first pass, "
                            "and the fact that a hexagon's n words lie in n distinct orbits. "
                            "None of these mentions abandonment or the multiplicity excess "
                            "total, so the proof is untouched by the F/G collision."),
        "withdrawn_corollaries": [
            "'f_out <= F + e for all generic F = 2' - restate as 'f_out <= G + e for G = 2'",
            "'Theorem A proved for all F = 2' - restate as 'Theorem A (G-form) proved for G = 2'",
            "'generic F = 2 has exactly four k cells' - restate as 'the G = 2 column has four "
            "k cells'",
            "'generic F = 2 has H <= 3' - restate as 'the G = 2 column has H <= 3'"],
        "corrected_scope": "G = 2 (both multiplicity types), NOT generic project F = 2",
    }


# ------------------------------------------------------------------ §4 dependency table
def round_110_audit():
    """§4 — 라운드 110 의 계수 증명에서 정확히 어디가 틀렸는가."""
    return {
        "step_1_to_5": {"statement": "L = 725 + (#joints) + S + H and P = (#joints) + 1",
                        "status": "CORRECT - no F, no G"},
        "step_6": {"statement": "'extra hexagon entries arise exactly one per abandonment, "
                                "hence P = 120 + F'",
                   "status": "**WRONG**",
                   "what_is_true": "P - 120 = sum_h (e_h - 1) = G BY DEFINITION; the "
                                   "identification of that count with the abandonment count "
                                   "F is what fails",
                   "when_it_holds": "exactly when every hexagon's nu-cycle has one descent, "
                                    "i.e. J = 0; automatic when every e_h <= 2",
                   "how_it_was_checked": "on 5 concrete strings, all of which happen to have "
                                         "J = 0 (the 872 witness has F = G = 25, the greedy "
                                         "873 has F = G = 0), so the error was invisible"},
        "step_7_8": {"statement": "L = 844 + F + S + H and L = 868 + (k + N + H)",
                     "status": "inherits the step-6 error - both need G in place of F"},
        "theorem_A": {"statement": "O <= 1 + S + F",
                      "status": "the SLAB derivation needs the G-form O <= 1 + S + G; the "
                                "F-form is strictly stronger and was never what the table "
                                "required"},
        "affected_rounds": ["110 (source)", "114", "115", "116", "117", "118", "119", "120",
                            "121", "122", "123", "124", "125", "126", "127"],
        "actually_harmed": ("none of the searches - every engine from Round 115 on hard-codes "
                            "P (120 or 121), i.e. it fixes G directly and never computes F. "
                            "The damage is confined to NAMES and to the prose claims that "
                            "generalised from 'F = 1' to all abandonment-count-1 walks."),
    }


def summarise(census=None):
    rep = dict(
        round=128, kind="F/G foundation repair",
        definitions=definitions(),
        fg_theorem=fg_theory(),
        counterexample=dissect(CODEX_N4),
        corrected_identities=corrected_identities(6),
        slab_table=slab_table(6),
        j_cost_theory=j_cost_theory(),
        round_110_audit=round_110_audit(),
        rounds_scope_table=rounds_scope_table(),
        round_127_salvage=round_127_salvage(),
        engine_audit=dict(
            fact="no engine from Round 118 through Round 125 contains the string 'abandon'",
            target="every one hard-codes #define TARGET 121 and accepts only at passes == 121",
            consequence="their domain is P = 121, i.e. G = 1 - never generic project F = 1",
            round_115="verify_f0_geometry_115.py sets P = 120, i.e. G = 0",
            q2="the legacy engine requires BOTH state.F == TARGET_F == 1 AND "
               "state.P == TARGET_P == 121 to accept, so Q2's domain is exactly G = 1",
            round_125_true_name="(k, G) = (1, 1) closed - not generic (k, F) = (1, 1)"),
        f0_audit=dict(
            question="is F = 0 => G = 0?",
            answer="YES - proved and verified",
            proof="a hexagon with e_h >= 2 has at least one nu-ascent, and an ascending pass "
                  "can never be the walk's last pass (nothing follows it), so it really "
                  "contributes an abandonment; hence G >= 1 => F >= 1",
            classification="Round 115 SURVIVES unchanged - G = 0 and F = 0 are the same set"),
        f1_audit=dict(
            question="is F = 1, G > 1 possible?",
            answer="YES in general - 46 of the 29,255 legal n = 4 walks have F = 1, G = 2, "
                   "all with multiplicity partition (2,) i.e. ONE hexagon entered three times",
            but="those walks have P = 122, not 121, so they were never in any engine's domain; "
                "in the corrected (k, G) parameterisation they live in the G = 2 column, "
                "which is OPEN and was never claimed closed",
            conclusion="no walk escapes the table - the (k, G) decomposition is exhaustive"),
        ledger_status=dict(
            outer_cell_ledger="REPAIRED - the second index is G, not F",
            closed_cells="9 of 55 (k, G) cells: (k, 0) for k = 0..4 and (k, 1) for k = 1..4",
            what_changed="the NAME of the second index; the closed set is unchanged",
            audited_4782="unchanged - a certificate for its literal encoded population",
            q2_6396="unchanged as a computational certificate; its scope is now stated as "
                    "G = 1 (equivalently F = 1 AND P = 121) rather than generic F = 1"),
        n4_census=census,
        label="ROUND-128 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_fg_repair_128.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep
