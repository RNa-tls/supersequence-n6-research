#!/usr/bin/env python3
"""라운드 116 — **`F = 1` 열의 일반 구조**를 정의만으로 다시 세운다.

Q2 아카이브(`(k,F) = (1,1)` + Area-A)에서 물려받은 것은 하나도 쓰지 않는다.
모든 주장은 (a) 정의로부터의 계수 증명이거나 (b) 유한 전수 계산이다.

  §1  F=1 의 기본 항등식:  P, O, D, 길이, 결손 총량
  §2  pass 길이 분류
  §3  유일 재진입 구조 (다중도 정리)
  §4  일반 F=1 과 Q2 특유 가정의 분리
  §5  짧은 pass 국소성
  §6  entry 의무 모델 (occurrence 인덱스 명시)
  §7  F=1 에서의 경량 이동 기하 — F=0 육각형-서로소를 재사용하지 않는다
  §8  결손 예산 6 의 분할 분류
  §9  F=1 이 사는 (k,F) 칸
  §10 일반 F=1 불변량 후보
  §14 n=4 전수 F=1 walk 양성 대조
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
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

WORDS = ["".join(p) for p in itertools.permutations("012345")]
sig = lambda x: x[1:] + x[0]
tau = lambda x: x[1:5] + x[0] + x[5]


def _rep(x, f, n):
    y, b = x, x
    for _ in range(n - 1):
        y = f(y)
        b = min(b, y)
    return b


HEXR = {x: _rep(x, sig, 6) for x in WORDS}
ORBR = {x: _rep(x, tau, 5) for x in WORDS}
HEXES = sorted(set(HEXR.values()))
ORBS = sorted(set(ORBR.values()))
OHEX = defaultdict(set)
for _x in WORDS:
    OHEX[ORBR[_x]].add(HEXR[_x])


def as_p(s):
    return tuple(int(c) for c in s)


def as_s(p):
    return "".join(str(v) for v in p)


def light_tails():
    """무게 2 의 tail 1개 + 무게 3 의 tail 3개 — 엔진과 같은 규칙."""
    out = []
    for w in (2, 3):
        for pi in core.tail_permutations(w):
            out.append((w, core.tail_action(w, pi)))
    return out


# ------------------------------------------------------------------ §1
def s1_identities():
    rows = []
    for k in range(0, 6):
        P = 121                                  # P = 120 + F, F = 1
        O = 24 + k
        D = 5 * O - P                            # 역사적 정의 D = 5O - P
        S_min = 22 + k                      # from O <= 1 + S + F with F = 1
        H_max = 26 - S_min                  # from S + H <= 26 (i.e. L <= 871)
        rows.append(dict(k=k, P=P, O=O, D=D, D_equals_5k_minus_F=(D == 5 * k - 1),
                         S_min=S_min, H_max=H_max,
                         D_nonneg=(D >= 0), slab_ok=(H_max >= 0),
                         feasible=(D >= 0 and H_max >= 0)))
    return dict(
        P=121, P_rule="P = n!/n + F = 120 + F",
        O="O = 24 + k  (definition of k)",
        D="D = 5O - P = 5k - 1",
        k_lower_bound_from_D_ge_0=1,
        k_upper_bound_from_slab=4,
        length="L = 844 + F + S + H = 845 + S + H",
        L_le_871_iff="S + H <= 26",
        rotation_shortfall_total=6 * 1,
        rotation_shortfall_rule="sum over passes of (6 - passlen) = 6P - 720 = 6F = 6",
        per_hexagon_rule="sum over passes of h of (6 - passlen) = 6(e_h - 1)",
        sum_e_h_minus_1=1,
        rows=rows,
        feasible_k=[r["k"] for r in rows if r["feasible"]])


# ------------------------------------------------------------------ §2, §3, §8
def s2_s3_s8_pass_structure():
    """F=1 => 정확히 한 육각형이 두 번 진입되고 나머지 119개는 한 번씩.

    그 육각형의 두 pass 는 6-순환을 두 개의 호로 나누므로 길이는 (a, 6-a).
    다른 119개 pass 는 길이가 정확히 6 이다.
    """
    types = []
    for a in range(1, 6):
        types.append(dict(a=a, lengths=[a, 6 - a],
                          deficits=[6 - a, a],
                          deficit_partition=sorted([6 - a, a], reverse=True)))
    uniq = sorted({tuple(t["deficit_partition"]) for t in types}, reverse=True)
    # 6 의 모든 분할 중 실제로 실현 가능한 것만 남는다
    def partitions(n, mx=None):
        mx = n if mx is None else mx
        if n == 0:
            yield ()
            return
        for i in range(min(n, mx), 0, -1):
            for r in partitions(n - i, i):
                yield (i,) + r
    allp = list(partitions(6))
    realizable = [p for p in allp if p in uniq]
    return dict(
        multiplicity_theorem=("exactly one hexagon h* has e_{h*} = 2 and every other hexagon "
                              "has e_h = 1; there is no other option because "
                              "sum_h (e_h - 1) = F = 1 and e_h >= 1"),
        pass_length_multiset="6^119 together with (a, 6-a) for the two passes of h*",
        entry_words_of_h_star="v and sigma^a(v) — the two passes are complementary arcs of the 6-cycle",
        ordered_types=types,
        deficit_partitions_realizable=[list(p) for p in uniq],
        deficit_partitions_of_six_total=len(allp),
        deficit_partitions_excluded=[list(p) for p in allp if p not in uniq],
        short_pass_count=2,
        why_only_two=("a short pass must lie in a hexagon with e_h >= 2 (per-hexagon identity), "
                      "and F = 1 gives exactly one such hexagon carrying exactly two passes"))


# ------------------------------------------------------------------ §7
def s7_light_geometry():
    """pass 길이별(회전 수 ell = 0..5) 경량 이동 기하를 720 단어 전수로 다시 잰다."""
    tails = light_tails()
    assert len(tails) == 4, len(tails)
    names = {}
    # ell=5 에서의 상을 기준으로 이름을 붙인다 (F=0 라운드의 W2/W3a/W3b/W3c)
    u0 = WORDS[0]
    y0 = as_p(u0)
    for _ in range(5):
        y0 = core.word_after(y0, core.SIGMA)
    for w, act in tails:
        t = as_s(core.word_after(y0, act))
        if w == 2:
            names[(w, act)] = "W2"
        elif ORBR[t] == ORBR[u0]:
            names[(w, act)] = "W3a"
        elif OHEX[ORBR[u0]] & OHEX[ORBR[t]]:
            names[(w, act)] = "W3b"
        else:
            names[(w, act)] = "W3c"
    assert sorted(names.values()) == ["W2", "W3a", "W3b", "W3c"], names

    table = {}
    for ell in range(6):
        for (w, act) in tails:
            nm = names[(w, act)]
            same_orb = same_hex = 0
            shared = Counter()
            back_to_source_hex = 0
            for u in WORDS:
                y = as_p(u)
                for _ in range(ell):
                    y = core.word_after(y, core.SIGMA)
                t = as_s(core.word_after(y, act))
                if ORBR[t] == ORBR[u]:
                    same_orb += 1
                if HEXR[t] == HEXR[u]:
                    same_hex += 1
                shared[len(OHEX[ORBR[u]] & OHEX[ORBR[t]])] += 1
                if HEXR[t] == HEXR[u]:
                    back_to_source_hex += 1
            table[f"ell{ell}_{nm}"] = dict(
                ell=ell, name=nm, weight=w, cost=(0 if w == 2 else 1),
                same_orbit=same_orb, same_hexagon=same_hex,
                orbit_pair_shared_hexagons=dict(sorted(shared.items())))
    free_leaves_orbit = {ell: table[f"ell{ell}_W2"]["same_orbit"] for ell in range(6)}
    return dict(
        light_tail_count=len(tails),
        weight2_tails=1, weight3_tails=3,
        table=table,
        free_move_same_orbit_by_ell=free_leaves_orbit,
        free_move_is_tau_only_at_ell5=(free_leaves_orbit[5] == 720
                                       and all(free_leaves_orbit[e] == 0 for e in range(5))),
        headline=("at ell = 5 the free (weight-2) successor is tau and stays in the orbit; "
                  "for every ell < 5 it always leaves the orbit, so a SHORT pass can have a "
                  "FREE inter-run connector — impossible at F = 0"))


# ------------------------------------------------------------------ §14 n=4 controls
def n4_walks(max_len=36):
    """n=4 비반복 walk 을 길이 상한까지 전수로 만든다 (24개 순열을 각각 한 번씩)."""
    perms = ["".join(p) for p in itertools.permutations("1234")]
    idx = {p: i for i, p in enumerate(perms)}

    def omega(a, b):
        for k in range(1, 5):
            if a[k:] == b[:4 - k]:
                return k
        return 4

    W = [[omega(a, b) for b in perms] for a in perms]
    out = []
    n = len(perms)

    def dfs(cur, used, seq, total):
        if len(seq) == n:
            out.append((4 + total, list(seq)))
            return
        # 남은 스텝마다 최소 1 이므로 하한으로 자른다
        if 4 + total + (n - len(seq)) > max_len:
            return
        for j in range(n):
            if used >> j & 1:
                continue
            w = W[cur][j]
            if 4 + total + w + (n - len(seq) - 1) > max_len:
                continue
            seq.append(j)
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    # S4 재라벨 대칭으로 시작 순열 하나면 충분하다 (길이 분포는 같다)
    dfs(0, 1, [0], 0)
    return perms, W, out


def _n4_geo(perms):
    """n=4 의 육각형(sigma-류, 크기 4)과 E-궤도(tau-류, 크기 3)."""
    s4 = lambda w: w[1:] + w[0]
    t4 = lambda w: w[1] + w[2] + w[0] + w[3]
    hexr, orbr = {}, {}
    for p in perms:
        y, b = p, p
        for _ in range(3):
            y = s4(y); b = min(b, y)
        hexr[p] = b
        y, b = p, p
        for _ in range(2):
            y = t4(y); b = min(b, y)
        orbr[p] = b
    return hexr, orbr, s4, t4


def measure4(perms, W, L, seq):
    n4 = 4
    om = [W[seq[i]][seq[i + 1]] for i in range(len(seq) - 1)]
    J = sum(1 for w in om if w >= 2)
    S = sum(1 for w in om if w >= 3)
    H = sum(max(w - 3, 0) for w in om)
    P = J + 1
    F = P - 6
    hexr, orbr, _s4, _t4 = _n4_geo(perms)
    entries, plen, cur = [], [], 1
    entries.append(perms[seq[0]])
    for i, w in enumerate(om):
        if w >= 2:
            plen.append(cur)
            cur = 1
            entries.append(perms[seq[i + 1]])
        else:
            cur += 1
    plen.append(cur)
    eh = Counter(hexr[e] for e in entries)
    short = [i for i, l in enumerate(plen) if l < n4]
    joints = [w for w in om if w >= 2]
    # runs = maximal blocks of consecutive passes in one E-orbit
    orbs = [orbr[e] for e in entries]
    runs, cur_run = [], [0]
    for i in range(1, len(orbs)):
        if orbs[i] == orbs[i - 1]:
            cur_run.append(i)
        else:
            runs.append(cur_run); cur_run = [i]
    runs.append(cur_run)
    r = len(runs)
    O = len(set(orbs))
    inter = {run[0] - 1 for run in runs[1:]}
    x = sum(1 for i, w in enumerate(joints) if i not in inter and w >= 3)
    f_out = sum(1 for i in inter if joints[i] == 2)
    heavy_inter = sum(1 for i in inter if joints[i] >= 4)
    tt = heavy_inter + 1
    k4 = O - 2
    return dict(L=L, P=P, F=F, S=S, H=H, O=O, k=k4, D=3 * O - P,
                r=r, e=r - O, x=x, f_out=f_out, t=tt,
                S_identity_ok=(S == (r - 1) + x - f_out),
                D_nonneg=(3 * O - P >= 0),
                k_ge_1=(k4 >= 1),
                cost=S + H,
                cost_bound=22 - 22 + (O - 1) + (r - O) + x - f_out + (tt - 1),
                cost_bound_ok=(S + H >= (O - 1) + (r - O) + x - f_out + (tt - 1)),
                f_out_le_short_passes=(f_out <= len(short)),
                short_pass_separation=(abs(short[0] - short[1]) if len(short) == 2 else None),
                free_inter_run_shared_hexagons=[
                    len({hexr[w] for w in perms if orbr[w] == orbs[runs[j][0] - 1 + 1 - 1]}
                        & {hexr[w] for w in perms if orbr[w] == orbs[runs[j][0]]})
                    for j in range(1, len(runs)) if joints[runs[j][0] - 1] == 2],
                length_identity_ok=(L == 4 + 24 - 2 + 6 + F + S + H),
                pass_lengths=plen,
                rotation_shortfall=sum(n4 - l for l in plen),
                shortfall_equals_nF=(sum(n4 - l for l in plen) == n4 * F),
                hexagon_multiplicity=dict(sorted(Counter(eh.values()).items())),
                doubled_hexagons=[h for h, c in eh.items() if c >= 2],
                short_pass_indices=short,
                short_passes_in_doubled_hexagon=all(
                    eh[hexr[entries[i]]] >= 2 for i in short),
                short_passes_adjacent=(len(short) == 2 and abs(short[0] - short[1]) == 1),
                entries=entries)


def s14_controls():
    perms, W, walks = n4_walks(36)
    rows = [measure4(perms, W, L, s) for L, s in walks]
    byF = Counter(r["F"] for r in rows)
    f1 = [r for r in rows if r["F"] == 1]
    checks = dict(
        walks_enumerated=len(rows),
        max_len=36,
        F_histogram=dict(sorted(byF.items())),
        f1_count=len(f1),
        f1_length_identity_ok=all(r["length_identity_ok"] for r in f1),
        f1_shortfall_ok=all(r["shortfall_equals_nF"] for r in f1),
        f1_exactly_one_doubled_hexagon=all(len(r["doubled_hexagons"]) == 1 for r in f1),
        f1_multiplicity_pattern=sorted({json.dumps(r["hexagon_multiplicity"], sort_keys=True)
                                        for r in f1}),
        f1_short_pass_counts=dict(sorted(Counter(len(r["short_pass_indices"])
                                                 for r in f1).items())),
        f1_all_short_passes_live_in_the_doubled_hexagon=all(
            r["short_passes_in_doubled_hexagon"] for r in f1),
        f1_short_pass_length_pairs={str(list(k)): v for k, v in sorted(Counter(
            tuple(sorted(r["pass_lengths"][i] for i in r["short_pass_indices"]))
            for r in f1).items(), key=str)},
        f1_short_passes_adjacent_in_walk_order={str(k): v for k, v in sorted(Counter(
            r["short_passes_adjacent"] for r in f1).items(), key=str)},
        f1_S_identity_ok=all(r["S_identity_ok"] for r in f1),
        f1_D_nonneg=all(r["D_nonneg"] for r in f1),
        f1_k_ge_1=all(r["k_ge_1"] for r in f1),
        f1_k_histogram=dict(sorted(Counter(r["k"] for r in f1).items())),
        f1_f_out_histogram=dict(sorted(Counter(r["f_out"] for r in f1).items())),
        f1_f_out_never_exceeds_short_pass_count=all(
            r["f_out_le_short_passes"] for r in f1),
        f1_cost_bound_ok=all(r["cost_bound_ok"] for r in f1),
        f0_S_identity_ok=all(r["S_identity_ok"] for r in rows if r["F"] == 0),
        f0_f_out_histogram=dict(sorted(Counter(r["f_out"] for r in rows
                                               if r["F"] == 0).items())),
        f1_short_pass_separation=dict(sorted(Counter(r["short_pass_separation"]
                                                     for r in f1).items())),
        f1_min_short_pass_separation=min(r["short_pass_separation"] for r in f1),
        f1_f_out_vs_k={f"f_out={fo},k={kk}": v for (fo, kk), v in
                       sorted(Counter((r["f_out"], r["k"]) for r in f1).items())},
        f1_free_inter_run_arc_shared_hexagons=dict(sorted(Counter(
            v for r in f1 for v in r["free_inter_run_shared_hexagons"]).items())),
        f1_free_inter_run_arc_always_overlaps=all(
            v >= 1 for r in f1 for v in r["free_inter_run_shared_hexagons"]))
    non_adjacent = [r for r in f1 if not r["short_passes_adjacent"]]
    if non_adjacent:
        sm = min(non_adjacent, key=lambda r: (r["L"], r["short_pass_indices"]))
        checks["smallest_non_adjacent_counterexample"] = {
            q: sm[q] for q in ("L", "P", "F", "S", "H", "pass_lengths",
                               "short_pass_indices", "entries")}
    return checks


# ------------------------------------------------------------------ §4, §9, §10
def s4_q2_separation():
    return [
        dict(condition="P = 121", generic_at_F1=True,
             why="P = 120 + F is an identity"),
        dict(condition="Phi >= 0  (Phi = 5 + 6(121 - P) - (720 - visited))",
             generic_at_F1=True,
             why=("prefix capacity: the 121 - P remaining passes carry <= 6 permutations each "
                  "and the current pass can still gain <= 5; uses only P_final = 121 and "
                  "passlen <= 6, both generic at F = 1")),
        dict(condition="O = 25  (equivalently k = 1)", generic_at_F1=False,
             why="k in {1,2,3,4} is arithmetically feasible at F = 1; O = 25 is one cell of four"),
        dict(condition="D = 4", generic_at_F1=False, why="D = 5k - 1, so D = 4 only when k = 1"),
        dict(condition="Ndef + H <= 3 with O = 25", generic_at_F1=False,
             why=("Ndef = S + F - O = S - 24 at k = 1, so the engine's budget means S + H <= 27, "
                  "i.e. L <= 872 — one length wider than L <= 871, and it fixes k = 1")),
        dict(condition="every pass has a forced ell", generic_at_F1=False,
             why=("119 passes are forced to ell = 5, but the two passes of the doubled hexagon "
                  "have ell = a-1 and 5-a with a in 1..5 — five ordered choices")),
        dict(condition="fragment locality (Round 91)", generic_at_F1=False,
             why="proved inside Q2's state model; a generic F = 1 form is derived in section 5 instead"),
        dict(condition="Area-A boundary conditions / f1_prune_reason", generic_at_F1=False,
             why="engine-specific prune set, never re-derived from the definition of F = 1"),
        dict(condition="pass <-> hexagon bijection", generic_at_F1=False,
             why="F = 0 only; at F = 1 it is 121 passes onto 120 hexagons, exactly one doubled"),
        dict(condition="every free arc is intra-orbit", generic_at_F1=False,
             why="holds only for full passes; the two short passes have orbit-changing free successors"),
    ]


def s9_cell_table():
    """F=1 의 네 칸에 대해 산술만으로 강제되는 것들 (L <= 871 가정 아래)."""
    rows = []
    for k in range(1, 5):
        O = 24 + k
        D = 5 * k - 1
        S_min = 22 + k                      # O <= 1 + S + F  with F = 1
        H_max = 26 - S_min                  # S + H <= 26
        t_max = H_max + 1                   # H >= t - 1
        rows.append(dict(
            k=k, O=O, D=D, S_min=S_min, H_max=H_max, t_max=t_max,
            requirement="k + e + x + t - f_out <= 4",
            e_plus_x_plus_t_max=4 - k + 2,   # f_out <= 2
            note=("t = 1 is forced" if t_max == 1 else f"t <= {t_max}"),
            covered_by_Q2=(k == 1)))
    return dict(
        rows=rows,
        tightest_cell=4,
        why_k4_is_tightest=("H <= 0 forces H = 0 hence t = 1: the whole walk is a single "
                            "all-light chain, and f_out >= 1 + e + x is forced"),
        loosest_cell=1,
        why_k1_is_loosest="H <= 3 allows t <= 4, the widest chain budget of the column")


def s10_invariant():
    return dict(
        S_identity="S = (r - 1) + x - f_out",
        terms=dict(r="number of runs (maximal same-orbit blocks of passes)",
                   x="non-free intra-run joints",
                   f_out="free (weight-2) INTER-run joints"),
        f_out_bound=2,
        f_out_reason=("a free joint after a full pass is tau and stays in the orbit, so it is "
                      "intra-run; only a SHORT pass can have an orbit-changing free successor, "
                      "and F = 1 has exactly two short passes"),
        H_bound="H >= t - 1  (t = number of maximal all-light chains)",
        r_bound="r >= O = 24 + k",
        cost="cost = S + H >= 22 + k + e + x + t - f_out,   e = r - O",
        requirement="L <= 871  <=>  cost <= 26  <=>  k + e + x + t - f_out <= 4",
        target_theorem="k + e + x + t - f_out >= 5",
        comparison_with_F0=("at F = 0 the requirement was k + e + x + t <= 5 and the proved "
                            "bound was >= 6; at F = 1 the length budget is one tighter "
                            "(845 vs 844) and f_out <= 2 gives back up to two, so F = 1 with "
                            "f_out = 1 is exactly as hard as F = 0"),
        chain_capacity_note=("the F=0 capacity model needs exactly two perturbations: 121 passes "
                             "instead of 120 with one hexagon used twice, and two passes whose "
                             "exit word is sigma^(a-1)(u) instead of sigma^5(u)"),
        free_inter_run_arc_forces_overlap=("every light move out of a SHORT pass leaves the orbit "
                                           "and its target orbit shares 1 or 2 hexagons with the "
                                           "source (720/720 for every ell < 5), so a free "
                                           "inter-run arc always consumes orbit-overlap defect"),
        but_the_overlap_budget_is_not_binding=("the overlap pool is 5k >= 5 while f_out <= 2 "
                                               "consumes at most 4 — the n=4 exhaustive data "
                                               "confirms f_out = 2 occurs with k = 1, so there is "
                                               "NO law of the form f_out <= c*k"),
        next_round_target=("N*_{F=1}(b, g, s; a) — the R115 chain capacity with (i) one hexagon "
                           "allowed two used words at sigma-distance a, (ii) those two passes "
                           "exiting at sigma^(a-1) and sigma^(5-a), (iii) phase-shortfall pool "
                           "D = 5k - 1; then 121 <= sum_i N*_i must contradict "
                           "k + e + x + t - f_out <= 4"))


def main():
    rep = dict(round=116, type="F=1 structure round — no cell closure claimed",
               label="ROUND-116 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
               s1_identities=s1_identities(),
               s2_s3_s8_pass_structure=s2_s3_s8_pass_structure(),
               s7_light_geometry=s7_light_geometry(),
               s4_q2_separation=s4_q2_separation(),
               s9_cells=dict(feasible_k=[1, 2, 3, 4],
                             k0_excluded_because="D = 5k - 1 >= 0 forces k >= 1",
                             k_ge_5_excluded_because="slab bound k + H <= 4 with H >= 0",
                             covered_by_Q2=[[1, 1]],
                             never_touched=[[2, 1], [3, 1], [4, 1]]),
               s9_cell_table=s9_cell_table(),
               s10_invariant=s10_invariant(),
               s14_controls=s14_controls(),
               ledger=dict(INDEPENDENTLY_AUDITED_Q2_RESIDUAL=4782,
                           CLAUDE_FULL_JOINT_UNSAT_COMPLETE=6396,
                           unchanged_by_this_round=True),
               disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_structure_116.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    g = rep["s7_light_geometry"]
    print("free move same-orbit count by ell:", g["free_move_same_orbit_by_ell"])
    print("free is tau only at ell=5:", g["free_move_is_tau_only_at_ell5"])
    c = rep["s14_controls"]
    for q in ("walks_enumerated", "F_histogram", "f1_count",
              "f1_exactly_one_doubled_hexagon", "f1_multiplicity_pattern",
              "f1_short_pass_counts", "f1_all_short_passes_live_in_the_doubled_hexagon",
              "f1_short_pass_length_pairs", "f1_short_passes_adjacent_in_walk_order"):
        print(f"  {q}: {c.get(q)}")


if __name__ == "__main__":
    main()
