#!/usr/bin/env python3
"""라운드 131 — `(k, G) = (4, 2)` 남은 하위경우의 구조 정리.

라운드 130 은 `A/e=0` 과 `B/e=0` 을 닫았다.  남은 셋은 `A/e=1`, `B/e=1`, `B/e=2` 이다.
이 모듈은 **탐색 전에** 세 하위경우를 강제하는 정리를 유도하고 `n = 4` 전수로 검사한다.

핵심은 다섯 하위경우 전부에 동시에 적용되는 하나의 정리이다 (정리 131.1).
`F` 는 내부 좌표일 뿐이고 바깥 좌표는 `(k, G)` 이다 — 라운드 128 의 수리를 지킨다.

용어 (라운드 126·128 에서 그대로)
--------------------------------
* pass `p` : 진입 단어 `u`, 길이 `len`.  `entry(p) = u`, `exit(p) = σ^{len−1}(u)`.
* `ν(p)`   : 같은 육각형에서 순환적으로 다음 pass — `entry(ν(p)) = σ^{len}(u)` (정리 128.1).
* `F = #{p : p < ν(p)}` (walk 순서의 `ν`-상승 수),  `G = P − n!/n = Σ_h (e_h − 1)`.
* 자유 후속 (라운드 126 §5) :  `free(p) = τ(σ^{len}(u)) = τ(entry(ν(p)))`.
  - `len = n` (full pass) ⇒ `free(p) = τ(u)` — **같은 궤도** (intra-run).
  - `len < n` (short pass) ⇒ `orb(σ^{len}(u)) ≠ orb(u)` — **반드시 궤도를 바꾼다** (inter-run).
* 따라서 `f_out` (= `ω = 2` inter-run joint 수) = **`ω = 2` 로 나가는 짧은 pass 의 수**.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


# ------------------------------------------------------------------ §1 (4,2) 재유도
def cell_42():
    """§1 — `(k, G) = (4, 2)` 의 정확한 수치를 처음부터 다시 유도한다."""
    n, k, G = 6, 4, 2
    P = n * n * n * n * n // 1  # placeholder, replaced below
    P = 720 // n + G                       # 122
    O = 720 // (n * (n - 1)) + k           # 28
    D = (n - 1) * O - P                    # 18
    # 마스터: L = (n + n!/n·? ) — 라운드 129 의 형태를 그대로 다시 쓴다.
    #   L = 844 + G + S + H,   S = 23 + k + e + x − f_out   (n = 6)
    #   L = 867 + k + G + e + x + H − f_out ≤ 871
    #   ⇒ f_out ≥ k + G + e + x + H − 4 = e + x + H + 2
    # 정리 129.1 (재증명은 §3): f_out ≤ F + e ≤ G + e = e + 2
    #   ⇒ x = H = 0,  F = 2,  f_out = e + 2,  S = 23 + k + e − f_out = 25
    x = H = 0
    F = 2
    S = 23 + k + 0 + x - 0        # e 와 f_out 이 상쇄된다: S = 23 + k = 27? -> 아래에서 정확히
    S = 25
    N = S + G - O                 # −1
    L = 844 + G + S + H           # 871
    subcases = []
    for typ, mshort in (("A", 3), ("B", 4)):
        # f_out = e + 2 ≤ #짧은 pass = mshort  ⇒ e ≤ mshort − 2
        for e in range(0, mshort - 2 + 1):
            subcases.append(dict(type=typ, e=e, f_out=e + 2, m=mshort - 2))
    return dict(n=n, k=k, G=G, P=P, O=O, D=D, x=x, H=H, F=F, S=S, N=N, L=L,
                runs_by_e={str(s["e"]): O + s["e"] for s in subcases},
                subcases=[f"{s['type']}/e={s['e']}" for s in subcases],
                n_subcases=len(subcases),
                remaining_after_130=["A/e=1", "B/e=1", "B/e=2"])


# ------------------------------------------------------- §2·§3 정리 131.1 (통일 정리)
def theorem_131_1():
    """§2·§3·§5 — 다섯 하위경우 전부를 강제하는 **하나의** 정리.

    ### 보조정리 131.L1 (자유 탈출의 목표 궤도)
    짧은 pass `p` 가 `ω = 2` 로 나가면 후속은 `τ(entry(ν(p)))` 이므로 새 run 은
    궤도 `Q(p) := orb(entry(ν(p)))` 안에서 열리고, 그 run 의 τ-사슬에서 `ν(p)` 는
    **시작 슬롯 +(n−2)** 즉 τ-순환의 바로 앞 칸에 있다.

    ### 보조정리 131.L2 (경우 (ii) ⇒ 반복 run)
    `p` 의 자유 탈출 시점에 `ν(p)` 가 **이미 놓였으면** (즉 `p > ν(p)`, `ν`-하강)
    `ν(p) ∈ Q(p)` 이므로 `Q(p)` 는 이미 방문된 궤도이고 새 run 은 **반복 run** 이다.
    서로 다른 하강 pass 는 서로 다른 run 을 열므로

        #(자유 하강) ≤ #(반복 run) = e.

    ### 보조정리 131.L3 (경우 (i) 의 lock — 자명하지만 정확)
    `p` 가 `ν`-상승이고 자유 탈출하면 `ν(p)` 는 아직 안 놓였다.  `p` 의 후속이 여는
    run 이 `ν(p)` 를 **담지 못하면** `ν(p)` 는 `Q(p)` 의 **뒤 run** 에 놓이므로
    `Q(p)` 는 run 을 둘 이상 갖는다 — 즉 `+1` 의 `e` 를 쓴다.

    ### 정리 131.1
    `f_out = #(자유 상승) + #(자유 하강) ≤ F + e` (상승은 전부 짧은 pass 이고 `F` 개뿐).
    **`(k,G) = (4,2)` 에서는 `f_out = e + 2 = F + e` 로 등호**이므로

      (a) `ν`-상승인 짧은 pass 는 **전부** 자유 탈출한다;
      (b) 자유 하강은 **정확히 `e` 개**, 즉 반복 run 은 전부 자유 하강이 연다 —
          **비싼(ω≥3) joint 가 반복 run 을 열 수 없고**, 반복 run 의 궤도는
          `Q(p) = orb(entry(ν(p)))` 로 **핀**된다;
      (c) 경우 (i) 의 lock 은 **하나도 깨지지 않는다** — 상승 `p` 의 자유 후속이 연 run 은
          `ν(p)` 에서 끝난다 (`e` 예산이 (b) 로 이미 전부 소진되었기 때문).

    등호의 계산:  `e ≥ #(자유 하강) ≥ f_out − F = e`, 그리고 깨진 lock 이나 비싼 반복 run 이
    하나라도 있으면 `e ≥ #(자유 하강) + 1 = f_out − F + 1 = e + 1` 로 모순.
    """
    return dict(
        name="Theorem 131.1",
        lemmas=["131.L1 target orbit", "131.L2 descent => repeat run",
                "131.L3 broken lock => repeat run"],
        hypothesis="f_out = F + e  (forced in every (k,G)=(4,2) subcase)",
        conclusions=["every nu-ascent short pass exits freely",
                     "#free descents = e exactly",
                     "every repeat run is opened by a free descent exit",
                     "no repeat run is opened by an omega>=3 joint",
                     "every case-(i) lock holds (run ends exactly at nu(p))"],
        reproves="Theorem 129.1 (f_out <= F + e)",
        applies_to=["A/e=0", "A/e=1", "B/e=0", "B/e=1", "B/e=2"])


def ascent_descent_pattern():
    """§2·§13 — 다섯 하위경우의 자유/lock/revisit 패턴 표 (정리 131.1 의 따름정리).

    * 유형 A (`F = 2`) : arc 은 walk 순서 `arc0 < arc1 < arc2` 이고 `ν` 는 순환 회전
      `arc0 → arc1 → arc2 → arc0` (라운드 129 의 내부-`F` 규칙).  상승은 `arc0, arc1`,
      하강은 `arc2` — **유일**.
    * 유형 B : 각 2-순환에서 여는 pass 가 상승, 닫는 pass 가 하강.  상승 둘, 하강 둘.
    """
    sids = {"A": {"ascent": [0, 1], "descent": [2], "n_short": 3},
            "B": {"ascent": [0, 2], "descent": [1, 3], "n_short": 4}}
    table = []
    for typ in ("A", "B"):
        a, d = sids[typ]["ascent"], sids[typ]["descent"]
        for e in range(0, sids[typ]["n_short"] - 2 + 1):
            fout = e + 2
            # (a) 상승은 전부 자유;  (b) 하강 중 정확히 e 개가 자유.
            branches = []
            from itertools import combinations
            for ds in combinations(d, e):
                free = sorted(a + list(ds))
                branches.append(dict(
                    free_sids=free,
                    freespec=sum(1 << s for s in free),
                    lockspec=sum(1 << s for s in a),
                    revspec=sum(1 << s for s in ds)))
            table.append(dict(type=typ, e=e, f_out=fout, ascents=a, descents=d,
                              n_branches=len(branches), branches=branches))
    return table


def round130_comparison():
    """§13·§16 — 라운드 130 이 쓴 스펙과 정리 131.1 이 강제하는 스펙의 차이."""
    tbl = {t["type"] + "/e=" + str(t["e"]): t for t in ascent_descent_pattern()}
    r130 = {
        "A/e=0": dict(branches=1, lockspec=0b011, revspec=None),
        "A/e=1": dict(branches=1, lockspec=0b011, revspec=None),
        "B/e=0": dict(branches=1, lockspec=0b0101, revspec=None),
        "B/e=1": dict(branches=4, lockspec=0, revspec=None),
        "B/e=2": dict(branches=1, lockspec=0, revspec=None),
    }
    out = {}
    for key, t in tbl.items():
        new_lock = t["branches"][0]["lockspec"]
        out[key] = dict(
            round130_branches=r130[key]["branches"], round131_branches=t["n_branches"],
            round130_lockspec=r130[key]["lockspec"], round131_lockspec=new_lock,
            lock_is_new=(r130[key]["lockspec"] != new_lock),
            revisit_pin_is_new=True,
            branch_reduction=r130[key]["branches"] / t["n_branches"])
    return out


# ------------------------------------------------------------ §3·§4 A/e=1 의 완전 강제
def ae1_forcing():
    """§3·§4·§6·§7 — `A/e=1` 의 순서·궤도 구조를 끝까지 못박는다.

    정리 131.1 로 `arc0, arc1` 은 자유 상승(lock 유지), `arc2` 는 유일한 자유 하강이다.

    **§3 분열 궤도의 핀.**  `arc2` 의 자유 탈출이 여는 반복 run 의 궤도는
    `Q₂ = orb(entry(ν(arc2))) = orb(entry(arc0))` 이고, `e = 1` 이므로 **이것이 유일한
    분열 궤도**이다.  `entry(arc0), entry(arc1), entry(arc2)` 는 같은 육각형 `h*` 의 서로
    다른 세 단어이고 한 육각형의 `n` 개 단어는 `n` 개의 **서로 다른 궤도**에 있으므로
    `Q₀ = orb(entry(arc1))`, `Q₁ = orb(entry(arc2))`, `Q₂` 는 셋 다 다르다.  따라서
    `Q₀, Q₁` 은 분열되지 않고 lock 이 정확히 성립한다.

    **§4 순서.**  `arc0` 의 lock 은 `Q₀` 의 **유일한** run 을 열고 그 run 은 `arc1` 에서
    끝난다.  run 은 τ-사슬이고 `entry(arc1)` 은 시작 슬롯의 τ-이전 칸이므로 그 run 은
    **정확히 5 pass** 이다 (`x = 0` 이라 run 안의 joint 는 전부 `ω = 2` = τ).  같은 논법이
    `arc1 → arc2` 에도 걸린다.  그러므로 walk 위치로

        pos(arc1) = pos(arc0) + 5,   pos(arc2) = pos(arc0) + 10,

    이고 `arc0` 직후 10 pass 는 **완전히 결정**된다 (전부 `ω = 2`, 비용 0).  `arc2` 의
    자유 탈출은 그 다음 자리에서 `Q₂` 의 두 번째 run `R₂` 를 연다.

    **§6 유일 재방문의 기하.**  `R₁` (arc0 을 담은 run) 은 `Q₂` 의 슬롯
    `[s₀−a+1 … s₀]` (s₀ = orbph(entry(arc0)), a = |R₁|), `R₂` 는 `[s₀+1 … s₀+b]`.
    둘은 겹칠 수 없으므로 `a + b ≤ n−1 = 5` 이고 합쳐서 τ-순환의 **연속 구간**이다.

    **§7 order type.**  위로부터 `A/e=1` 의 order type 은 **정확히 하나**이다:
    `… R₁(arc0 끝) │ S₁(4 full + arc1) │ S₂(4 full + arc2) │ R₂ …`.
    """
    n = 6
    return dict(
        n=n,
        ascents=["arc0", "arc1"], descent="arc2",
        split_orbit="orb(entry(arc0))", n_split_orbits=1,
        three_arc_orbits_distinct=True,
        pos_arc1_minus_arc0=n - 1,
        pos_arc2_minus_arc0=2 * (n - 1),
        forced_block_after_arc0=2 * (n - 1),
        forced_block_all_omega2=True,
        run_S1="[tau(entry(arc1)) .. arc1] = 4 full + arc1, exactly 5 passes",
        run_S2="[tau(entry(arc2)) .. arc2] = 4 full + arc2, exactly 5 passes",
        R1_R2_slots="R1 = [s0-a+1 .. s0], R2 = [s0+1 .. s0+b], a + b <= 5",
        n_order_types=1,
        orbits_with_zero_deficit=["Q0 = orb(entry(arc1))", "Q1 = orb(entry(arc2))"])


# ------------------------------------------------------------------ §14·§15 유형 B
def b_structure():
    """§14·§15 — `B/e=1`, `B/e=2` 의 구조.

    두 육각형 `g, h` 가 각각 두 번 진입.  walk 순서로 `g1 < g2`, `h1 < h2` 이고
    `ν` 는 각 쌍을 맞바꾸므로 상승은 `g1, h1` (opener), 하강은 `g2, h2` (closer),
    `F = 2` 는 항상 성립한다.

    **B/e=1.**  `f_out = 3`.  정리 131.1 (a) 로 두 opener 는 **반드시** 자유이고,
    (b) 로 closer 중 **정확히 하나**가 자유이다.  따라서 라운드 130 이 돌린 네 갈래
    (“어느 짧은 pass 가 자유가 아닌가”) 중 **opener 를 비자유로 둔 두 갈래는 공집합**이고
    실제 갈래는 **둘뿐**이다.  두 opener 에는 lock 이 걸린다 (라운드 130 은 안 썼다).
    유일한 분열 궤도는 자유 closer `c` 의 `orb(entry(ν(c)))` = 그 짝 opener 의 진입 궤도.

    **B/e=2.**  `f_out = 4` — 넷 다 자유.  두 opener 에 lock, 두 closer 가 각각 반복 run 을
    연다.  `orb(entry(g1))` 과 `orb(entry(h1))` 이 같을 수도 있다 (그 궤도가 run 셋).
    그래도 정리 131.1 (c) 로 lock 은 **무조건** 성립한다 — `e` 예산이 이미 소진되므로.
    """
    return dict(
        ascents="openers g1, h1", descents="closers g2, h2", F=2,
        b_e1=dict(f_out=3, free="both openers + exactly one closer",
                  round130_branches=4, round131_branches=2,
                  empty_branches=["opener g1 not free", "opener h1 not free"],
                  lockspec="0b0101 (both openers) - NEW in round 131",
                  split_orbit="orb(entry(nu(free closer))) = that closer's opener orbit"),
        b_e2=dict(f_out=4, free="all four", branches=1,
                  lockspec="0b0101 (both openers) - NEW in round 131",
                  split_orbits="orb(entry(g1)) and orb(entry(h1)); may coincide "
                               "(then that orbit carries three runs)",
                  locks_hold_unconditionally=True))


# -------------------------------------------------------------- §11 n = 4 전수 검증
def n4_theorem_check(maxlen=39):
    """§11 — **모든** 합법 `n = 4` walk 에서 보조정리 131.L1–L3 과 정리 131.1 을 검사한다.

    `G` 로 조건화하지 않는다.  등호 `f_out = F + e` 를 만족하는 walk 위에서 결론
    (a)(b)(c) 가 **한 번도 깨지지 않아야** 한다 — 이것이 새 가지치기의 건전성 근거이다.
    """
    from verify_f2_structure_126 import setup, legal_joint
    n = 4
    g = setup(n)
    perms, idx, sg, ta, om = g["perms"], g["idx"], g["sig"], g["tau"], g["omega"]
    hexid, orbid, hexph, orbph = g["hexid"], g["orbid"], g["hexph"], g["orbph"]
    NW = len(perms)
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or legal_joint(n, perms[a], perms[b], W[a][b])
           for b in range(NW)] for a in range(NW)]
    walks = []

    def rec(cur, used, seq, total):
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
            rec(j, used | (1 << j), seq, total + w)
            seq.pop()

    rec(0, 1, [0], 0)

    viol = Counter()
    stat = Counter()
    eqstat = Counter()
    for L, seq in walks:
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
        joints = [w for w in oms if w >= 2]
        bypos = {(hexid[u], hexph[u]): i for i, (u, _) in enumerate(passes)}
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
        e = r - O
        inter = {run[0] - 1 for run in runs[1:]}
        f_out = sum(1 for i in inter if joints[i] == 2)
        stat["walks"] += 1

        # --- run index of each pass, and first-run-of-orbit bookkeeping --------
        runof = [0] * P
        for ri, run in enumerate(runs):
            for p in run:
                runof[p] = ri
        seen = set()
        repeat_runs = []
        for ri, run in enumerate(runs):
            o = orbs[run[0]]
            if o in seen:
                repeat_runs.append(ri)
            seen.add(o)
        if len(repeat_runs) != e:
            viol["#repeat runs = e"] += 1

        # --- L1: free exit target orbit ---------------------------------------
        free_short = []
        for ri, run in enumerate(runs[1:], start=1):
            j = run[0] - 1                      # joint index into `joints`
            if joints[j] != 2:
                continue
            p = run[0] - 1                      # previous pass index
            # previous pass is runs[ri-1][-1]
            p = runs[ri - 1][-1]
            free_short.append((p, ri))
            u, ln = passes[p]
            if ln >= n:
                viol["L0: free inter-run exit is short"] += 1
            tgt = ta(perms[passes[nu[p]][0]])
            if idx[tgt] != passes[run[0]][0]:
                viol["L1: free successor = tau(entry(nu(p)))"] += 1
            if orbid[passes[run[0]][0]] != orbid[passes[nu[p]][0]]:
                viol["L1: target orbit = orb(entry(nu(p)))"] += 1
        if len(free_short) != f_out:
            viol["f_out = #free short exits"] += 1

        # --- L2 / L3 -----------------------------------------------------------
        ndesc = nasc = nbroken = 0
        for (p, ri) in free_short:
            if nu[p] < p:                       # descent  -> case (ii)
                ndesc += 1
                if ri not in repeat_runs:
                    viol["L2: descent free exit opens a repeat run"] += 1
            else:                               # ascent   -> case (i)
                nasc += 1
                if runof[nu[p]] != ri:
                    nbroken += 1
        if nasc > F:
            viol["#free ascents <= F"] += 1
        if ndesc > e:
            viol["#free descents <= e"] += 1
        if f_out > F + e:
            viol["f_out <= F + e"] += 1
        ncostly = sum(1 for ri in repeat_runs if joints[runs[ri][0] - 1] != 2)
        if ndesc + nbroken + ncostly > e:
            viol["L3: descents + broken locks + costly repeats <= e"] += 1

        # --- Theorem 131.1 under equality --------------------------------------
        if f_out == F + e:
            eqstat["equality_walks"] += 1
            asc_short = [i for i in range(P) if i < nu[i]]
            if nasc != F:
                viol["131.1(a): every ascent exits freely"] += 1
            if not all(any(p == q for (q, _) in free_short) for p in asc_short):
                viol["131.1(a): ascent set = free ascent set"] += 1
            if ndesc != e:
                viol["131.1(b): #free descents = e"] += 1
            if ncostly != 0:
                viol["131.1(b): no costly repeat run"] += 1
            if nbroken != 0:
                viol["131.1(c): no broken lock"] += 1
            eqstat[f"F{F}_e{e}"] += 1
    return dict(n=n, maxlen=maxlen, walks=stat["walks"],
                equality_walks=eqstat["equality_walks"],
                equality_by_F_e={k: v for k, v in sorted(eqstat.items())
                                 if k != "equality_walks"},
                violations=dict(viol), clean=(len(viol) == 0))


def summarise(n4=None):
    d = dict(round=131, cell=cell_42(), theorem=theorem_131_1(),
             pattern=ascent_descent_pattern(), comparison=round130_comparison(),
             ae1=ae1_forcing(), b=b_structure())
    if n4 is not None:
        d["n4_check"] = n4
    return d


if __name__ == "__main__":
    import sys
    n4 = n4_theorem_check() if "--fast" not in sys.argv else None
    d = summarise(n4)
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_g2_ae1_131.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(d, ensure_ascii=False, indent=1))
