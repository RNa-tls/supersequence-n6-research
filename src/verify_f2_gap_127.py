#!/usr/bin/env python3
"""라운드 127 — `F = 2` 유형 B 의 **유일한 구멍** `f_out = 4, e = 1` 을 해결한다.

라운드 126 이 남긴 것은 정확히 하나였다:

    유형 B (육각형 둘을 각각 두 번 진입),  f_out = 4,  e = 1  가 가능한가?

이 모듈은 그것이 **불가능함을 증명**하고, 증명의 모든 단계를 계산으로 확인한다.

--------------------------------------------------------------------------------
### 정리 127.1 (유형 B 자유 탈출)

`F = 2` 유형 B walk 에서 `f_out = 4` 이면 **`e ≥ 2`** 다.

**증명.**  `q*` 를 run 이 둘 이상인 궤도라 하자.  `e = Σ_q (runs(q) − 1) = 1` 이면 그런 궤도는
**정확히 하나**이고 run 이 **정확히 둘**이다.  반복 육각형을 `h`, `g` 라 하고 각각의 두 pass 를
`ν`-순환 순서로 `h1, h2` (`ν(h1) = h2`), `g1, g2` 라 하자.  `f_out = 4` 이므로 네 pass 가
**전부** 자유 후속으로 나간다.

1. **경우 (ii) 는 육각형마다 정확히 하나.**  `p` 가 자유로 나갈 때
   경우 (i) = "후속이 시작하는 run 이 `ν(p)` 를 담는다", 경우 (ii) = "담지 않는다".
   경우 (ii) 는 `orb(ν(p))` 에 run 이 둘 이상임을 증명하므로 `orb(ν(p)) = q*` 다.
   `h1`, `h2` 가 **둘 다** 경우 (ii) 이면 `orb(h2) = orb(h1) = q*` 인데 육각형의 여섯 단어는
   서로 다른 여섯 궤도에 있으므로 모순.  보조정리 E′ 로 둘 다 경우 (i) 일 수도 없다.
   따라서 **정확히 하나**가 경우 (ii) 다.  `h1` 을 그것이라 이름 붙이면
   **`orb(h2) = q*`** 이고, `h2` 는 경우 (i) 이므로 순서 보조정리로 **`h2 < h1`**.
   `g` 도 같게 이름 붙이면 **`orb(g2) = q*`**, **`g2 < g1`**.

2. **`h2` 와 `g2` 는 `q*` 의 서로 다른 run 에 있다.**  `A_h` := `h1` 의 자유 후속
   `τ(entry(h2))` 가 시작하는 run.  이것은 `q*` 의 run 이고 경우 (ii) 이므로
   `A_h ≠ run(h2)`.  마찬가지로 `A_g ≠ run(g2)`.  만약 `run(h2) = run(g2)` 라면 `q*` 의 run 이
   둘뿐이므로 `A_h = A_g` 이고, run 의 첫 pass 는 유일하므로
   `τ(entry(h2)) = τ(entry(g2))`, 즉 `entry(h2) = entry(g2)` — 한 단어가 서로 다른 두 육각형에
   있을 수 없으므로 모순.

3. **교차와 순서 모순.**  따라서 `R := run(h2)`, `R' := run(g2)` 는 `q*` 의 두 run 이고
   `A_h = R'`, `A_g = R` 다.  `h1` 의 **바로 다음** pass 는 `R'` 의 첫 pass 이므로
   `h1 < start(R') ≤ g2`, 즉 **`h1 < g2`**.  대칭으로 **`g1 < h2`**.  1 과 합치면

       g2 < g1 < h2 < h1 < g2

   — 선형 순서에서의 순환.  모순. ∎

--------------------------------------------------------------------------------
### 따름정리 127.2

모든 일반 `F = 2` walk 에서 **`f_out ≤ F + e = 2 + e`**.
(유형 A 는 라운드 126 에서 증명됨; 유형 B 는 `e = 0 ⟹ f_out ≤ 2`, `e = 1 ⟹ f_out ≤ 3`
(정리 127.1), `e ≥ 2 ⟹ f_out ≤ 4` 로 완결.)

### 따름정리 127.3 (정리 A 가 `F = 2` 에서 성립한다)

`O ≤ 1 + S + F  ⟺  f_out ≤ F + e + x` 이므로 따름정리 127.2 에서 **`F = 2` 에서 정리 A 가
증명된다.**  그리고 `L ≤ 871 ⟺ k + e + x + H − f_out ≤ 2` 에 넣으면 **`k + x + H ≤ 4`**,
`k ∈ {1,2,3,4}`, `H ≤ 3`.
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import (  # noqa: E402
    setup, legal_joint, n4_walks, measure, constants)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


# --------------------------------------------------------------- §9 order types
def order_type_elimination():
    """§9 — 네 짧은 pass 의 상대 순서를 전부 열거하고 제약으로 지운다.

    이름 붙이기는 육각형마다 두 가지(어느 pass 가 경우 (ii) 인가)이고, `ν` 가 2-순환이라
    이름 교환은 대칭이다.  정리 127.1 단계 1·3 이 주는 제약은

        case_i(h) < case_ii(h),   case_i(g) < case_ii(g),
        case_ii(h) < case_i(g),   case_ii(g) < case_i(h)

    이고, `4! = 24` 개 순서 × `2 × 2` 이름 붙이기 = **96 개 조합이 전부 모순**이어야 한다.
    """
    names = ["h1", "h2", "g1", "g2"]
    total = survived = 0
    per_label = {}
    for cii_h in ("h1", "h2"):
        ci_h = "h2" if cii_h == "h1" else "h1"
        for cii_g in ("g1", "g2"):
            ci_g = "g2" if cii_g == "g1" else "g1"
            cons = [(ci_h, cii_h), (ci_g, cii_g), (cii_h, ci_g), (cii_g, ci_h)]
            ok = 0
            for perm in itertools.permutations(names):
                pos = {p: i for i, p in enumerate(perm)}
                total += 1
                if all(pos[a] < pos[b] for a, b in cons):
                    ok += 1
                    survived += 1
            per_label[f"caseII({cii_h},{cii_g})"] = dict(
                constraints=[f"{a} < {b}" for a, b in cons], orders_surviving=ok)
    return dict(labellings=4, orders_per_labelling=24, combinations_checked=total,
                orders_surviving=survived, all_eliminated=(survived == 0),
                detail=per_label,
                cycle="g2 < g1 < h2 < h1 < g2 for the canonical labelling")


# ------------------------------------------------- §7/§8 shared-orbit geometry census
def shared_orbit_geometry(n):
    """§7·§8 — `q*` 가 서로 다른 두 육각형의 단어를 **동시에** 담을 수 있는가?

    담을 수 있다.  기하는 이 경우를 막지 않는다 — 막는 것은 **순서**다.
    이 census 가 그것을 정량화한다."""
    g = setup(n)
    nh, no = g["n_hex"], g["n_orb"]
    words_of_hex = [[] for _ in range(nh)]
    words_of_orb = [[] for _ in range(no)]
    for w in range(len(g["perms"])):
        words_of_hex[g["hexid"][w]].append(w)
        words_of_orb[g["orbid"][w]].append(w)
    hex_pairs_sharing = Counter()
    orbit_hexagons = []
    for q in range(no):
        hs = sorted({g["hexid"][w] for w in words_of_orb[q]})
        orbit_hexagons.append(hs)
        for a, b in itertools.combinations(hs, 2):
            hex_pairs_sharing[(a, b)] += 1
    shareable = sum(1 for v in hex_pairs_sharing.values() if v >= 1)
    return dict(
        n=n, n_hexagons=nh, n_orbits=no,
        orbit_meets_hexagons=sorted({len(hs) for hs in orbit_hexagons}),
        words_per_orbit_per_hexagon=sorted(
            {len([w for w in words_of_orb[q] if g["hexid"][w] == h])
             for q in range(no) for h in orbit_hexagons[q]}),
        distinct_hexagon_pairs=nh * (nh - 1) // 2,
        hexagon_pairs_sharing_an_orbit=shareable,
        max_orbits_shared_by_a_pair=max(hex_pairs_sharing.values()),
        geometry_forbids_sharing=False,
        note=("an orbit's n words lie in n DISTINCT hexagons, so it holds at most one word "
              "of each; two distinct hexagons CAN share an orbit, hence the geometry alone "
              "does not rule out the exceptional configuration - the order argument does"))


# ---------------------------------------------------- §12 exact local enumerator
def local_enumerator(n=6, verbose=False):
    """§12 — 예외 설정의 **국소** 구성을 전부 소진한다.

    122-pass walk 을 열거하지 않는다.  국소 상태는

        육각형 h 와 그 두 pass 의 진입 단어 (u_h1, u_h2 = σ^{b_h}(u_h1))
        육각형 g ≠ h 와 그 두 pass (u_g1, u_g2 = σ^{b_g}(u_g1))
        어느 pass 가 경우 (ii) 인가 (육각형마다 두 가지)
        유일한 분열 궤도 q*

    뿐이다.  `S_n` 좌곱이 단순추이적이므로 `u_h1` 을 한 단어로 고정하는 것은 완전 축약이다.

    단계별로 거르며 **각 단계가 몇 개를 남기는지** 보고한다.
    """
    g = setup(n)
    perms, idx, sg, ta = g["perms"], g["idx"], g["sig"], g["tau"]
    hexid, orbid = g["hexid"], g["orbid"]
    NW = len(perms)
    u_h1 = 0                                  # S_n reduction: fix the first entry word
    h = hexid[u_h1]
    stage = Counter()
    survivors = []
    for b_h in range(1, n):                   # h's split: pass lengths (b_h, n - b_h)
        w = perms[u_h1]
        for _ in range(b_h):
            w = sg(w)
        u_h2 = idx[w]
        for u_g1 in range(NW):
            gg = hexid[u_g1]
            if gg == h:
                continue                      # g must be a DIFFERENT hexagon
            for b_g in range(1, n):
                w2 = perms[u_g1]
                for _ in range(b_g):
                    w2 = sg(w2)
                u_g2 = idx[w2]
                if len({u_h1, u_h2, u_g1, u_g2}) != 4:
                    continue                  # four distinct entry words
                stage["0_raw_local_states"] += 1
                for cii_h in (1, 2):          # which pass of h is case (ii)
                    ci_h = 2 if cii_h == 1 else 1
                    for cii_g in (1, 2):
                        ci_g = 2 if cii_g == 1 else 1
                        stage["1_with_case_labelling"] += 1
                        uh = {1: u_h1, 2: u_h2}
                        ug = {1: u_g1, 2: u_g2}
                        # step 1: q* = orb(case-(i) pass) for BOTH hexagons
                        if orbid[uh[ci_h]] != orbid[ug[ci_g]]:
                            continue
                        stage["2_shared_split_orbit_q*"] += 1
                        qs = orbid[uh[ci_h]]
                        # the case-(ii) pass certifies q* has >= 2 runs; with e = 1 it has
                        # exactly 2.  The free successors that start runs of q*:
                        s_h = idx[ta(perms[uh[ci_h]])]   # h's case-(ii) free successor
                        s_g = idx[ta(perms[ug[ci_g]])]   # g's case-(ii) free successor
                        if orbid[s_h] != qs or orbid[s_g] != qs:
                            continue          # tau preserves the orbit - sanity
                        stage["3_free_successors_land_in_q*"] += 1
                        # step 2: run(h_ci) = run(g_ci) would force s_h == s_g
                        same_run_forces = (s_h == s_g)
                        if same_run_forces:
                            # then entry(h_ci) == entry(g_ci): impossible, different hexagons
                            stage["4a_same_run_case_killed_by_word_identity"] += 1
                            continue
                        stage["4b_two_distinct_runs_of_q*"] += 1
                        # step 3: the order constraints
                        cons = [("ci_h", "cii_h"), ("ci_g", "cii_g"),
                                ("cii_h", "ci_g"), ("cii_g", "ci_h")]
                        feasible = False
                        for perm in itertools.permutations(["ci_h", "cii_h", "ci_g", "cii_g"]):
                            pos = {p: i for i, p in enumerate(perm)}
                            if all(pos[a] < pos[b] for a, b in cons):
                                feasible = True
                                break
                        if feasible:
                            stage["5_order_feasible"] += 1
                            survivors.append(dict(b_h=b_h, u_g1=u_g1, b_g=b_g,
                                                  cii_h=cii_h, cii_g=cii_g, q=qs))
    return dict(n=n, fixed_entry_word=u_h1, hexagon_h=h,
                stages={kk: vv for kk, vv in sorted(stage.items())},
                survivors=len(survivors),
                exceptional_configuration_exists=(len(survivors) > 0),
                geometry_alone_allows=stage.get("3_free_successors_land_in_q*", 0),
                killed_by_word_identity=stage.get("4a_same_run_case_killed_by_word_identity", 0),
                killed_by_order=stage.get("4b_two_distinct_runs_of_q*", 0)
                - stage.get("5_order_feasible", 0))


# ------------------------------------------------- §10/§11 dependency digraph, tightness
def dependency_digraph(n_split_tokens):
    """§10·§11 — 두 개의 분리된 2-순환에 대해 **필요한 최소 분열 run 수**를 정확히 잰다.

    정점 = 네 짧은 pass.  자유 탈출이 강제하는 간선:

      * 경우 (i) 인 pass `p` 는 `p < ν(p)` 를 강제한다 (순서 보조정리);
      * 경우 (ii) 인 pass `p` 는 `orb(ν(p))` 를 분열 궤도로 **소비**한다.

    `e` 개의 분열 토큰이 있으면 경우 (ii) 는 **서로 다른 궤도**를 최대 `e` 개까지 쓸 수 있다.
    육각형 하나는 두 pass 가 모두 경우 (i) 일 수 없으므로(보조정리 E′) 최소 하나가 경우 (ii) 다.
    그리고 두 pass 가 **모두** 경우 (ii) 이면 `orb(h1) = orb(h2)` 가 되어 불가능하므로
    육각형마다 경우 (ii) 는 **정확히 하나**다.  따라서 토큰 수요는 육각형당 정확히 1 이다.

    토큰이 하나뿐이면 두 육각형이 **같은** 궤도를 써야 하고, 그때 정리 127.1 단계 3 의
    교차 제약이 추가로 붙는다.  이 함수는 그 조합이 만족 가능한지 정확히 센다.
    """
    names = ["h1", "h2", "g1", "g2"]
    nu = {"h1": "h2", "h2": "h1", "g1": "g2", "g2": "g1"}
    feasible = []
    for cii_h in ("h1", "h2"):
        ci_h = nu[cii_h]
        for cii_g in ("g1", "g2"):
            ci_g = nu[cii_g]
            cons = [(ci_h, cii_h), (ci_g, cii_g)]        # order lemma, both hexagons
            if n_split_tokens == 1:
                # both case-(ii) passes must charge the SAME orbit q*, and then the two
                # runs of q* are run(ci_h) and run(ci_g); the free exits cross them.
                cons += [(cii_h, ci_g), (cii_g, ci_h)]
            for perm in itertools.permutations(names):
                pos = {p: i for i, p in enumerate(perm)}
                if all(pos[a] < pos[b] for a, b in cons):
                    feasible.append(dict(case_ii=(cii_h, cii_g), order=list(perm)))
    return dict(split_tokens=n_split_tokens,
                feasible_orders=len(feasible),
                satisfiable=(len(feasible) > 0),
                example=feasible[0] if feasible else None)


def minimum_split_tokens():
    """두 개의 분리된 2-순환에 필요한 최소 분열 run 수 = **2**."""
    one = dependency_digraph(1)
    two = dependency_digraph(2)
    return dict(with_one_token=one, with_two_tokens=two,
                minimum_required=(1 if one["satisfiable"] else 2),
                theorem="type B with f_out = 4 requires e >= 2",
                bound_is_tight=two["satisfiable"])


# ------------------------------------------------------------------ §13 small-n controls
def walks(n, maxlen, legal_only=True):
    """일반 `n` 의 합법 비반복 walk 전수 (시작 단어 고정 = 완전 축약)."""
    g = setup(n)
    perms, sg, om = g["perms"], g["sig"], g["omega"]
    NW = len(perms)
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or (not legal_only)
           or legal_joint(n, perms[a], perms[b], W[a][b])
           for b in range(NW)] for a in range(NW)]
    out = []

    def dfs(cur, used, seq, total):
        if len(seq) == NW:
            out.append((n + total, tuple(seq)))
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
    return g, W, out


def exception_control(n, maxlen):
    """§13 — 예외 설정(유형 B, `f_out = 4`, `e = 1`)이 실제로 나타나는지 전수로 확인한다.

    아울러 정리 127.1 의 **중간 단계**도 실제 walk 에서 검사한다:
      * 완전 자유 반복 육각형은 경우 (ii) 를 **정확히 하나** 갖는가 (`e = 1` 일 때);
      * `f_out ≤ F + e`.
    """
    g, W, ws = walks(n, maxlen)
    perms, idx, ta, hexid, orbid = g["perms"], g["idx"], g["tau"], g["hexid"], g["orbid"]
    stat = Counter()
    viol = Counter()
    typeB_f4 = Counter()
    for L, seq in ws:
        r = measure(g, W, seq, L)
        stat["walks"] += 1
        stat[f"F={r['F']}"] += 1
        if r["f_out"] > r["F"] + r["e"]:
            viol["f_out <= F + e"] += 1
        parts = sorted((v - 1 for v in r["entry_counts"].values() if v >= 2), reverse=True)
        # per-hexagon case (i)/(ii) analysis
        P = r["P"]
        interset = set(r["inter"])
        free = {i for i in range(P - 1) if r["joints"][i] == 2 and i in interset}
        runof, nu = r["runof"], r["nu"]
        for h, cnt in r["entry_counts"].items():
            if cnt < 2:
                continue
            ps = [i for i in range(P) if r["hexes"][i] == h]
            if not all(i in free for i in ps):
                continue
            stat["all_free_repeated_hexagons"] += 1
            caseii = 0
            for i in ps:
                succ = i + 1                      # the free arc lands on pass i+1
                if runof[succ] != runof[nu[i]]:
                    caseii += 1
            if caseii == 0:
                viol["Lemma E': at least one case (ii)"] += 1
            if r["e"] == 1 and caseii != 1:
                viol["e = 1 => exactly one case (ii) per all-free hexagon"] += 1
        if r["F"] == 2 and parts == [1, 1] and r["f_out"] == 4:
            typeB_f4[r["e"]] += 1
            if r["e"] == 1:
                viol["EXCEPTIONAL CONFIGURATION type B f_out=4 e=1"] += 1
    return dict(n=n, maxlen=maxlen, legal_only=True, walks=len(ws),
                F_distribution={kk: vv for kk, vv in sorted(stat.items())
                                if kk.startswith("F=")},
                all_free_repeated_hexagons=stat["all_free_repeated_hexagons"],
                typeB_fout4_by_e={str(kk): vv for kk, vv in sorted(typeB_f4.items())},
                typeB_fout4_total=sum(typeB_f4.values()),
                exceptional_instances=typeB_f4.get(1, 0),
                violations=dict(viol), clean=(len(viol) == 0))


# --------------------------------------------------------- §15 consequences of the theorem
def consequences(LCAP=871):
    """§15 — 정리 127.1 이 성립할 때의 `F = 2` 귀결을 정확히 다시 센다.

    `f_out ≤ F + e = 2 + e` 와 `L = 869 + k + e + x + H − f_out ≤ 871` 에서

        k + e + x + H − f_out ≤ 2   그리고   f_out − e ≤ 2
        ⟹  **k + x + H ≤ 4**

    이고 `F ≤ 5k` 에서 `k ≥ 1` 이므로 `k ∈ {1,2,3,4}`, `H ≤ 3`.
    정리 A `O ≤ 1 + S + F ⟺ f_out ≤ F + e + x` 도 `f_out ≤ F + e` 에서 즉시 따라 나온다.
    """
    rows = []
    for typ, smax in (("A", 3), ("B", 4)):
        for f in range(0, smax + 1):
            for e in range(0, 6):
                if f > 2 + e:                      # Theorem 127.1 + Round 126 type A
                    continue
                for x in range(0, 6):
                    for H in range(0, 7):
                        for k in range(1, 8):
                            if k + e + x + H - f > LCAP - 869:
                                continue
                            rows.append(dict(type=typ, f_out=f, e=e, x=x, H=H, k=k,
                                             D=5 * k - 2, O=24 + k,
                                             S=23 + k + e + x - f,
                                             L=869 + k + e + x + H - f))
    ks = sorted({r["k"] for r in rows})
    return dict(
        assumption="f_out <= F + e = 2 + e (Round 126 type A + Theorem 127.1 type B)",
        theorem_A="O <= 1 + S + F holds at F = 2, since f_out <= F + e <= F + e + x",
        k_feasible=ks, n_cells=len(ks),
        max_H=max(r["H"] for r in rows),
        max_x=max(r["x"] for r in rows),
        max_k_plus_x_plus_H=max(r["k"] + r["x"] + r["H"] for r in rows),
        n_rows=len(rows),
        cells=[f"(k,F) = ({k},2)" for k in ks],
        matches_the_55_cell_table=(ks == [1, 2, 3, 4]),
        note=("these are the F = 2 cells that a later round would have to close; "
              "Round 127 does NOT start closing them"))


def theorem_A_status():
    """§17 — 정리 A 의 증명 범위를 정직하게 갱신한다."""
    return {
        "statement": "O <= 1 + S + F   (equivalently f_out <= F + e + x)",
        "F=0": "trivial - no short pass, so f_out = 0",
        "F=1": "PROVED (Round 117, Lemma E: f_out <= 1 + e)",
        "F=2 type A": "PROVED (Round 126)",
        "F=2 type B": "PROVED (Round 127, Theorem 127.1) - the last gap is closed",
        "F=2 overall": "PROVED",
        "F>=3": "NOT PROVED - still empirical (5 strings + exhaustive small-n)",
        "consequence": ("the project's 55-cell slab table rests on Theorem A; it is now "
                        "proved for the F = 0, 1, 2 columns and remains conditional for F >= 3"),
    }


def summarise(n4_maxlen=39, n5=None):
    rep = dict(
        round=127, target="F = 2 type B, f_out = 4, e = 1",
        theorem=dict(
            name="Theorem 127.1",
            statement="in a generic F = 2 type B walk, f_out = 4 implies e >= 2",
            proof_steps=[
                "e = 1 means exactly one orbit q* carries exactly two runs and every other "
                "orbit carries one",
                "for each repeated hexagon, not both passes are case (i) (Lemma E') and not "
                "both are case (ii) (that would force orb(h1) = orb(h2), impossible since a "
                "hexagon's n words lie in n distinct orbits), so EXACTLY one is case (ii); "
                "label it h1, so orb(h2) = q* and the order lemma gives h2 < h1",
                "run(h2) = run(g2) would force the two case-(ii) free successors to be the "
                "same first pass, i.e. entry(h2) = entry(g2) - impossible for distinct "
                "hexagons; so run(h2) and run(g2) are the two distinct runs of q*",
                "h1's immediate successor is the first pass of run(g2), so h1 < g2; "
                "symmetrically g1 < h2; with h2 < h1 and g2 < g1 this gives the cycle "
                "g2 < g1 < h2 < h1 < g2 in a linear order - contradiction"],
            corollary_1="f_out <= F + e for ALL generic F = 2 (type A: Round 126)",
            corollary_2="Theorem A (O <= 1 + S + F) holds at F = 2",
            corollary_3="k + x + H <= 4, k in {1,2,3,4}, H <= 3"),
        order_type_elimination=order_type_elimination(),
        dependency_digraph=minimum_split_tokens(),
        shared_orbit_geometry={str(n): shared_orbit_geometry(n) for n in (4, 5, 6)},
        local_enumeration={str(n): local_enumerator(n) for n in (4, 5, 6)},
        n4_control=exception_control(4, n4_maxlen),
        n5_control=n5,
        consequences=consequences(),
        theorem_A_status=theorem_A_status(),
        geometry_is_not_the_obstruction=(
            "two distinct hexagons CAN share an orbit (1,080 of the 7,140 hexagon pairs at "
            "n = 6 do), and 400 of the 71,400 labelled local states pass every geometric "
            "test; all 400 die on the ORDER constraints, so the obstruction is "
            "order-theoretic, not geometric"),
        round_126_correction=(
            "the Round-126 document said 79 type-B f_out=4 walks were observed at n = 4; the "
            "artifact rr_f2_structure_126.json recorded 56 all along (34 with e = 2, 20 with "
            "e = 3, 2 with e = 4). 56 is correct; 79 was a transcription error in the prose. "
            "The substantive claims (min e = 2, zero exceptional instances) are unaffected."),
        no_cells_closed=True,
        cell_status=dict(claude_closed_outer_cells="9/55 (unchanged)",
                         F2_column="OPEN - Round 127 only proves the free-exit bound",
                         F2_cells_now_well_defined=4),
        label="ROUND-127 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f2_gap_127.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep
