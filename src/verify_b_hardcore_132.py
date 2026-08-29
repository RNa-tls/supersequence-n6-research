#!/usr/bin/env python3
"""라운드 132 — `(k, G) = (4, 2)` 의 **유형 B hard core** (`B/e=1`, `B/e=2`) 구조.

라운드 131 이 `A/e=0`·`B/e=0`·`A/e=1` 을 닫았다.  남은 것은 유형 B 둘뿐이다.
이 모듈은 **탐색 전에** 두 하위경우의 order type·반복 궤도·lock 성립을 끝까지 유도한다.

바깥 좌표는 `(k, G)` 이다.  `F` 는 내부 좌표일 뿐이다.
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup, legal_joint          # noqa: E402
from verify_fg_repair_128 import walk_measure                   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


# ------------------------------------------------------------------ §1 표기 고정
def notation():
    """§1 — 유형 B 표기와 **정확한** 자유 후속 관계.

    두 겹친 육각형을 `h`, `g` 라 하고 각각 pass 둘을 갖는다.  `ν` 는 각 육각형의
    두 pass 를 맞바꾸는 2-순환이므로 walk 순서로 앞선 쪽이 `ν`-상승 = **opener**,
    뒤선 쪽이 `ν`-하강 = **closer** 이다.  내부 `F = 2` 는 자동이다 (상승이 정확히 둘).

    엔진의 slot 은 **walk 순서**로 붙는다: `opener₀` 가 walk 에서 먼저 나오는 opener 다.
    (그래서 `h ↔ g` 이름 바꾸기는 walk 을 바꾸지 않는다 — §3 참조.)

    정확한 관계 (라운드 126 §5, 라운드 128 정리 128.1):

        entry(closer_X) = σ^{b_X}(entry(opener_X))          b_X = opener_X 의 길이
        len(closer_X)   = n − b_X
        free(p)         = τ(entry(ν(p)))                    (짧은 pass 의 유일한 ω=2 후속)

    따라서

        free(opener_X) = τ(entry(closer_X)) = τ(σ^{b_X}(entry(opener_X)))
        free(closer_X) = τ(entry(opener_X))

    이고 `entry(opener_X)` 와 `entry(closer_X)` 는 **같은 육각형의 다른 두 단어**이므로
    (한 육각형의 `n` 개 단어는 `n` 개의 서로 다른 궤도에 있다)

        T_X := orb(entry(closer_X))  ≠  Q_X := orb(entry(opener_X)).
    """
    return dict(
        hexagons=["h", "g"], passes=["opener_h", "closer_h", "opener_g", "closer_g"],
        ascents="the two openers", descents="the two closers", internal_F=2,
        slot_rule="slot index follows WALK order: opener_0 is the walk-first opener",
        entry_closer="entry(closer_X) = sigma^{b_X}(entry(opener_X))",
        free_opener="free(opener_X) = tau(entry(closer_X))",
        free_closer="free(closer_X) = tau(entry(opener_X))",
        T_X="orb(entry(closer_X))  - the lock target orbit of opener_X",
        Q_X="orb(entry(opener_X))  - the repeat orbit charged by a free closer_X",
        T_ne_Q="T_X != Q_X always (distinct words of one hexagon lie in distinct orbits)")


# ------------------------------------------------------------ §2 B/e=1 자유 패턴
def be1_patterns():
    """§2 — `B/e=1` 의 자유-탈출 패턴은 **정확히 둘**이다.  다시 유도한다.

    `f_out = e + 2 = 3` 이고 짧은 pass 는 넷이다.  정리 131.1(a) 로 두 `ν`-상승
    (= 두 opener) 은 **반드시** 자유 탈출한다.  (b) 로 자유 하강은 정확히 `e = 1` 개다.
    따라서 자유인 셋은 `{opener₀, opener₁, closer_?}` 이고 비자유는 나머지 closer 하나 —
    **패턴은 “어느 closer 가 자유인가” 둘뿐**이다.  라운드 130 이 돌린 “opener 하나가
    비자유” 인 두 갈래는 정리로 **공집합**이다.
    """
    return dict(f_out=3, n_short=4,
                forced_free=["opener_0", "opener_1"],
                free_descents=1,
                patterns=[dict(name="P0", free_closer="closer_0", free_sids=[0, 1, 2],
                               freespec=0b0111, revspec=0b0010),
                          dict(name="P1", free_closer="closer_1", free_sids=[0, 2, 3],
                               freespec=0b1101, revspec=0b1000)],
                n_patterns=2,
                empty_by_theorem=["opener_0 non-free", "opener_1 non-free"])


# --------------------------------------------------------- §4·§5 반복 궤도와 lock
def repeat_orbit_formula():
    """§4 — 반복 궤도의 정확한 공식.

    정리 131.1(b): 반복 run 은 자유 하강 `d` 의 `ω = 2` 탈출이 열고, 그 run 은
    `orb(entry(ν(d)))` 안에 있다.  유형 B 에서 `ν(closer_X) = opener_X` 이므로

        **repeat orbit of a free closer_X  =  Q_X = orb(entry(opener_X))**,
        그 run 의 시작 슬롯 = orbph(entry(opener_X)) + 1.

    `B/e=1` 은 자유 closer 가 하나뿐이라 반복 궤도가 **하나**,
    `B/e=2` 는 둘 (`Q_0`, `Q_1`) 이고 **같을 수도 있다** (§10 모형 T).
    """
    return dict(
        formula="repeat orbit(free closer_X) = Q_X = orb(entry(opener_X))",
        start_slot="orbph(entry(opener_X)) + 1",
        be1="exactly one repeat orbit",
        be2="two repeat events; Q_0 and Q_1 are NOT assumed distinct")


def theorem_132_1():
    """§5 — **정리 132.1 (뒤 opener 의 lock 은 무조건 성립한다).**

    유형 B 의 `(4,2)` 하위경우 (`e ∈ {0,1,2}`) 에서 `opener₁` 의 국소성 lock 은
    **절대 깨지지 않는다.**

    증명.  깨진다고 하자.  정리 131.1(c) 로 `T₁ = orb(entry(closer₁))` 은 반복 궤도여야
    한다.  반복 궤도는 자유 closer 의 `Q_X` 뿐이고 `T₁ ≠ Q₁` 이므로 `T₁ = Q₀` 이고
    `Q₀ ≠ Q₁` 이다 (같으면 `T₁ = Q₁` 이 되어 모순).  lock 이 깨졌으므로 `opener₁` 의
    자유 후속이 연 run `W ⊆ Q₀` 는 `closer₁` 에 닿지 못한다.  `W` 는 walk 에서
    `opener₁` **뒤**에서 시작한다.  그런데 `Q₀` 의 run 은
      * `opener₀` 에서 끝나는 run — `opener₀ < opener₁` 이므로 `W` 가 아니다;
      * `closer₀` 의 자유 탈출이 여는 반복 run — run 하나는 joint 하나가 여는데
        `closer₀ ≠ opener₁` 이므로 `W` 가 아니다;
    뿐이다 (`e ≤ 2` 이고 `Q₀ ≠ Q₁` 이므로 `Q₀` 는 run 이 많아야 둘).  따라서 `W` 는
    `Q₀` 의 **세 번째** run 이고 `Q₀` 만으로 `e ≥ 2`, 거기에 `Q₁` 의 반복이 더해져
    `e ≥ 3` — `e ≤ 2` 에 모순. ∎

    **따름정리.**  `T₁` 이 이미 알려진 반복 궤도와 같아지는 가지는 **공집합**이므로
    엔진은 lock 을 포기하는 대신 **가지치기** 할 수 있다.  라운드 131 은 그 자리에서
    lock 만 포기했다 — 이번 라운드의 순증분이다.
    """
    return dict(name="Theorem 132.1",
                statement="in every type-B (4,2) subcase the later opener's locality lock "
                          "holds unconditionally",
                consequence="a branch where T_1 equals a known repeat orbit is EMPTY - the "
                            "engine may PRUNE there instead of merely dropping the lock",
                round131_behaviour="dropped the lock (sound but weaker)")


def lock_table():
    """§5 — `B/e=1` 의 정확한 lock 표 (갈래별 구현 추측을 대체한다)."""
    rows = []
    for pat, freec in (("P0", 0), ("P1", 1)):
        rep = f"Q_{freec} = orb(entry(opener_{freec}))"
        row = dict(pattern=pat, free_closer=f"closer_{freec}", repeat_orbit=rep,
                   opener0_target="T_0 = orb(entry(closer_0))",
                   opener1_target="T_1 = orb(entry(closer_1))",
                   opener1_lock="UNCONDITIONAL (Theorem 132.1)")
        if freec == 0:
            # T_0 != Q_0 always, and Q_0 is the only repeat orbit
            row["opener0_lock"] = "UNCONDITIONAL (T_0 != Q_0 and Q_0 is the only repeat orbit)"
            row["branches"] = 1
        else:
            row["opener0_lock"] = ("CONDITIONAL: may break only if T_0 = Q_1, which cannot "
                                   "be decided when opener_1 is still unplaced")
            row["branches"] = 2
        rows.append(row)
    return rows


# ------------------------------------------------------------ §6 궤도 일치 census
def orbit_coincidence_census(n=6):
    """§6 — `S₆` 안에서 세 궤도 (`T₀`, `T₁`, 반복 궤도) 가 겹칠 수 있는지 정확히 센다.

    두 육각형은 서로 다르지만 그 단어들의 궤도는 **독립적으로** 정해지므로,
    `opener₀` 의 진입 단어와 분할 `b₀` 를 고정하면 `T₀ = orb(σ^{b₀}(v₀))` 가 정해진다.
    `Q₁ = orb(v₁)` 는 `opener₁` 의 진입 단어 `v₁` 이 정한다.  `T₀ = Q₁` 을 만족하는 `v₁`
    은 그 궤도의 `n−1 = 5` 개 단어 중 **`opener₀` 의 육각형에 속하지 않는 것**이다.
    """
    g = setup(n)
    perms, idx, sg = g["perms"], g["idx"], g["sig"]
    orbid, hexid = g["orbid"], g["hexid"]
    NW = len(perms)
    rows = []
    for b0 in range(1, n):
        v0 = 0                                     # S6 대칭으로 한 단어 고정
        w = perms[v0]
        for _ in range(b0):
            w = sg(w)
        c0 = idx[w]
        T0, Q0 = orbid[c0], orbid[v0]
        # T0 = Q1 을 만족하는 v1 후보: T0 궤도의 단어들 중 h(=v0 의 육각형) 밖의 것
        cand = [u for u in range(NW) if orbid[u] == T0 and hexid[u] != hexid[v0]]
        # Q1 = Q0 (모형 T) 를 만족하는 후보
        candT = [u for u in range(NW) if orbid[u] == Q0 and hexid[u] != hexid[v0]]
        rows.append(dict(b0=b0, T0_ne_Q0=(T0 != Q0),
                         n_v1_with_T0_eq_Q1=len(cand),
                         n_v1_with_Q1_eq_Q0=len(candT),
                         orbit_size=sum(1 for u in range(NW) if orbid[u] == T0)))
    return dict(n=n, fixed_word="entry(opener_0) = perms[0] by S6 left-multiplication",
                rows=rows,
                note=("the coincidence T_0 = Q_1 is possible for every split b_0 and pins "
                      "entry(opener_1) into a 5-word orbit minus the 1 word shared with "
                      "opener_0's hexagon - a 4/720 fraction of placements, so the beta "
                      "branch is a genuinely narrow class, not an empty one"))


# ------------------------------------------------- §7·§13·§14 order type 열거
def order_types():
    """§7·§13·§14 — `B/e=1` 과 `B/e=2` 의 **정확한** order type.

    두 개의 도구만 쓴다.
    * **lock 이 성립하면** 그 run 은 `n−1 = 5` pass 이고 (`x = 0` 이라 run 안 joint 는
      전부 τ), 짧은 pass 는 언제나 run 의 마지막 pass 이므로 **lock 이 걸린 run 안에는
      다른 짧은 pass 가 들어갈 수 없다** ⇒ `closer_X = opener_X + 5`.
    * **lock 이 깨지면** (`opener₀` 만 가능, `T₀ = Q₁`) `opener₀` 의 자유 후속이 연 run
      `U ⊆ Q₁` 는 `Q₁` 의 **첫** run 이고 (`Q₁` 이 run 셋이면 `e ≥ 2` 초과) `opener₁` 에서
      끝난다.  `closer₀ ∈ Q₁` 는 그 다음 run `V` 에 있고 `V` 는 `closer₁` 의 자유 탈출이
      슬롯 `orbph(entry(opener₁)) + 1` 에서 연다.  `U = [s+1 … t]`, `V = [t+1 … s]`
      (`s = orbph(entry(closer₀))`, `t = orbph(entry(opener₁))`) 이므로 **`Q₁` 은 슬롯 5개가
      꽉 차고** `|U| + |V| = 5`, `closer₀` 는 `V` 의 마지막 pass 다.  따라서

          opener₀ < opener₁ = opener₀ + |U| < closer₁ = opener₁ + 5
                  < closer₀ = closer₁ + (5 − |U|) = **opener₀ + 10**,

      `|U| ∈ {1,2,3,4}` 이고 `opener₀ … closer₀` 의 11 pass 블록은 joint 가 **전부 ω = 2**
      (비용 0) 이다.
    """
    alpha = dict(
        name="alpha chain", shape="opener_0 < closer_0 = opener_0 + 5 < opener_1 "
                                  "< closer_1 = opener_1 + 5",
        gap="closer_0 < opener_1 is strict; the passes between are all full",
        free_parameter="the gap length (>= 1)")
    beta = dict(
        name="beta nest",
        shape="opener_0 < opener_1 = opener_0 + |U| < closer_1 = opener_1 + 5 "
              "< closer_0 = opener_0 + 10",
        U_range=[1, 2, 3, 4], forced_block_passes=11,
        forced_block_internal_joints=10,
        forced_block_all_omega2=True,
        joint_count_note="an 11-pass block has 10 INTERNAL joints (Round-132 audit "
                         "correction); all 10 carry omega = 2, so the block costs 0",
        extra="Q_1 is FULL (all 5 slots used, deficit 0); closer_0 is the last pass of V",
        requires="T_0 = orb(entry(closer_0)) = Q_1 = orb(entry(opener_1))")
    return dict(
        be1=[dict(pattern="P0 (closer_0 free)", locks="both unconditional",
                  order_type="alpha chain", n_order_types=1),
             dict(pattern="P1 (closer_1 free), alpha", locks="both hold",
                  order_type="alpha chain", n_order_types=1),
             dict(pattern="P1 (closer_1 free), beta", locks="opener_0 breaks",
                  order_type="beta nest", n_order_types=4,
                  note="four order types, one per |U| in {1,2,3,4}")],
        be2=[dict(model="T", order_type="alpha chain", n_order_types=1,
                  extra="opener_1 is the LAST pass of the repeat run opened by closer_0, "
                        "so orb(entry(opener_1)) = Q_0"),
             dict(model="D-alpha", order_type="alpha chain", n_order_types=1),
             dict(model="D-beta0", order_type="beta nest", n_order_types=4)],
        alpha=alpha, beta=beta,
        be1_total_order_types=6, be2_total_order_types=6)


# ------------------------------------------------- §9·§10·§11 B/e=2 분열 다중도
def split_multiplicity_models():
    """§9·§10·§11 — `B/e=2` 의 분열 궤도 다중도 분류.  **모형 T 를 지우지 않는다.**

    `e = r − O = Σ_orbit (#run − 1)` 이므로 한 궤도가 run 셋을 가져도 `e = 2` 이다.
    두 모형을 **따로** 다룬다.

    ### 모형 D — 두 궤도가 각각 run 둘 (`Q₀ ≠ Q₁`)
    ### 모형 T — 한 궤도가 run 셋 (`Q₀ = Q₁ =: Q`)

    **모형 T 는 실제로 가능하고, 모양이 하나로 확정된다.**
    `Q` 의 세 run 은: 첫 run `F`, `closer₀` 가 여는 반복 run `R` (슬롯
    `orbph(entry(opener₀))+1` 시작), `closer₁` 이 여는 반복 run `R'`.
    `opener₀` 와 `opener₁` 은 각각 `Q` 의 어떤 run 의 **마지막** pass 다.

    * `opener₀` 가 `R` 을 끝낼 수 없다 — `R` 은 `opener₀` 의 슬롯 바로 다음에서 시작하므로
      `opener₀` 에서 끝나려면 5 슬롯 전부를 먹어 `R'` 이 빈다.  같은 이유로 `opener₁` 은
      `R'` 을 끝낼 수 없다.
    * `opener₀ → R'`, `opener₁ → R` 도 불가능 — 두 arc `[a+1…t]` 와 `[t+1…a]` 가 5 슬롯을
      전부 덮어 첫 run `F` 가 빈다.
    * `opener₀ → R'`, `opener₁ → F` 도 불가능 — `R'` 은 `closer₁ > opener₁ > opener₀` 뒤에서
      열리는데 `opener₀` 가 그 안에 있을 수 없다.
    * 남는 것은 **`opener₀ → F`, `opener₁ → R`** 하나뿐이다.

    그리고 모형 T 에서는 `T₀ = orb(entry(closer₀)) ≠ Q` 이고 유일한 반복 궤도가 `Q` 이므로
    **두 opener lock 이 전부 무조건 성립한다** — 모형 T 는 통째로 α 갈래 안에 있다.

    **모형 D 의 하위 갈래.**
    * `D-α` — 두 lock 다 성립.
    * `D-β₀` — `opener₀` 의 lock 이 깨진다 (`T₀ = Q₁`).  §7 의 beta nest.
    * `D-β₁` — `opener₁` 의 lock 이 깨진다: **정리 132.1 로 불가능** (해석적 kill).
    """
    return dict(
        e_definition="e = r - O = sum over orbits of (#runs - 1); one orbit with three "
                     "runs contributes 2, so Model T is legal by definition",
        model_T_n4_witnesses=dict(
            Q0_eq_Q1_samples_total=72, e1=61, e2_genuine_three_run=11,
            e2_three_run_with_x0=0,
            do_not_use_x0_absence_as_a_theorem=True),
        model_T=dict(possible=True, shape="opener_0 ends the first run F; the repeat run R "
                                          "opened by closer_0 ends at opener_1; the repeat "
                                          "run R' opened by closer_1 is the third",
                     ruled_out=["opener_0 ends R", "opener_1 ends R'",
                                "opener_0 ends R' and opener_1 ends R",
                                "opener_0 ends R' and opener_1 ends F"],
                     n_shapes=1, both_locks="unconditional",
                     positive_constraint="orb(entry(opener_1)) = orb(entry(opener_0))"),
        model_D=dict(sub=["D-alpha", "D-beta0", "D-beta1"],
                     D_beta1="IMPOSSIBLE by Theorem 132.1 - analytic kill",
                     n_live_sub=2),
        do_not_assume_distinct=True)


# ------------------------------------------------------------------ §12 α/β 감사
def audit_alpha_beta():
    """§12 — 현재 **C 소스와 드라이버**에서 α/β 의 정확한 의미를 되읽는다 (JSON 불신)."""
    c = (ROOT / "src" / "g2_cell_131.c").read_text()
    d = (ROOT / "src" / "g2_k4_closure_131.py").read_text()
    have_prune = "if (risky) apply = 0" in c or "risky ? 0 :" in c
    return dict(
        source="src/g2_cell_131.c + src/g2_k4_closure_131.py (not the round-131 JSON)",
        lock0mode_2="apply the lock unless a KNOWN repeat orbit equals the target",
        lock0mode_1="alpha - assume opener_0's lock holds and apply it",
        lock0mode_0="beta - do not apply it and REQUIRE orb(entry(opener1)) == Q(opener0)",
        risky_branch_currently="drops the lock (does NOT prune)",
        risky_prune_present=have_prune,
        be2_branches_in_driver=d.count('subcase="B_e2"'),
        mapping=dict(alpha="covers Model T and Model D-alpha",
                     beta="covers Model D-beta0 only"),
        minimal=False,
        findings=["alpha/beta is exhaustive and sound but NOT minimal: Model T sits inside "
                  "alpha with a strong positive orbit constraint that alpha does not use",
                  "the 'risky' case for opener_1 is EMPTY by Theorem 132.1, so the engine "
                  "should prune there instead of dropping the lock",
                  "no third structural case is hidden: T, D-alpha, D-beta0 exhaust B/e=2 "
                  "and D-beta1 is impossible"])


# ------------------------------------------------------------------ §16·§17 예산
def budget():
    """§16·§17 — 길이 여유가 **정확히 0** 이라는 사실의 정밀 회계.

        단어 720개, 패스 122개 ⇒ pass 내부 전이 598개(전부 ω = 1), joint 121개.
        L = 6 + 598 + Σ_joint ω = 604 + 242 + Σ(ω−2) = 846 + Σ(ω−2) = 871
        ⇒ Σ(ω−2) = 25,  H = 0 ⇒ **ω=3 joint 가 정확히 25개, ω=2 joint 가 정확히 96개.**

        run 은 `r = O + e = 28 + e` 개 ⇒ inter-run joint 는 `27 + e` 개.
        그 중 `f_out = e + 2` 개가 ω=2 이고 나머지 `25` 개가 ω=3 — **정확히 맞아떨어진다.**
        intra-run ω=2 joint 는 `121 − 25 − (e+2) = 94 − e` 개이고
        `Σ_run (|run| − 1) = P − r = 94 − e` 와 **일치**한다.

    즉 여유가 0 이지만 **모순도 없다** — 회계는 정확히 닫힌다.  따라서 §16 이 바라는
    “한 단위 초과” 는 이 층위의 세기만으로는 나오지 않는다.  정직한 음성 결과다.
    """
    rows = {}
    for e in (0, 1, 2):
        r = 28 + e
        rows[f"e{e}"] = dict(runs=r, inter_run_joints=r - 1, free_exits=e + 2,
                             omega3_joints=(r - 1) - (e + 2),
                             intra_run_omega2=121 - 25 - (e + 2),
                             passes_minus_runs=122 - r,
                             consistent=((r - 1) - (e + 2) == 25
                                         and 121 - 25 - (e + 2) == 122 - r))
    return dict(words=720, passes=122, joints=121, intra_pass_transitions=598,
                L=871, sum_omega_minus_2=25, omega3_joints=25, omega2_joints=96,
                by_e=rows, all_consistent=all(v["consistent"] for v in rows.values()),
                one_unit_contradiction_found=False,
                note="the accounting closes exactly for every e; no one-unit overflow is "
                     "derivable at this level of counting (honest negative result)")


# -------------------------------------------------------------- §3 h<->g 교환
def exchange_soundness(maxlen=39):
    """§3 — `h ↔ g` 교환이 두 `B/e=1` 패턴을 동치로 만드는가?  **아니다.**

    엔진의 slot 은 walk 순서로 붙으므로 이름 바꾸기는 walk 을 전혀 바꾸지 않는다:
    어느 opener 가 먼저 나오는지는 walk 이 정하지 이름이 정하지 않는다.  따라서
    “자유 closer 가 slot 0 인가 slot 1 인가” 는 walk 의 **불변량**이고 두 패턴은
    이름 바꾸기로 옮겨지지 않는다.

    남은 후보는 **walk 뒤집기**다.  `reverse ∘ σ = σ^{-1} ∘ reverse` 이므로 뒤집기는
    육각형을 육각형으로 보내고 pass 길이를 보존하지만, `ν` 를 `ν^{-1}` 로 바꾸고 walk
    순서를 뒤집어 opener 와 closer 를 맞바꾼다.  문제는 **궤도 구조 `τ` 가 뒤집기와
    교환되지 않는다**는 점이다.  아래 `n = 4` 전수가 이를 확인한다: 뒤집은 walk 이
    합법이 아니거나 `(G, e, f_out)` 을 보존하지 않는 예가 존재하면 뒤집기는 쓸 수 없다.
    """
    n = 4
    g = setup(n)
    perms, idx, sg, om = g["perms"], g["idx"], g["sig"], g["omega"]
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
    legal = {sq for _, sq in ws}
    rev_legal = rev_illegal = 0
    rev_changes_invariants = 0
    for L, seq in ws:
        rseq = tuple(idx[tuple(reversed(perms[i]))] for i in reversed(seq))
        ok = all(OK[rseq[i]][rseq[i + 1]] for i in range(len(rseq) - 1))
        if not ok:
            rev_illegal += 1
            continue
        rev_legal += 1
        rL = n + sum(W[rseq[i]][rseq[i + 1]] for i in range(len(rseq) - 1))
        a = walk_measure(g, W, seq, L)
        b = walk_measure(g, W, rseq, rL)
        if (a["G"], a["e"], a["f_out"], a["F"]) != (b["G"], b["e"], b["f_out"], b["F"]):
            rev_changes_invariants += 1
    return dict(
        n=4, walks=len(ws),
        hg_relabel_is_a_symmetry=False,
        hg_reason="slot index is defined by walk order, so relabelling h and g does not "
                  "move any walk; 'which slot owns the free closer' is a walk invariant",
        reversal_legal=rev_legal, reversal_illegal=rev_illegal,
        reversal_changes_invariants=rev_changes_invariants,
        reversal_usable=(rev_illegal == 0 and rev_changes_invariants == 0),
        verdict="RETAIN BOTH B/e=1 patterns - no proved quotient")


# ------------------------------------------------------------------ §8·§19 런 수
def run_counts():
    """§8·§19 — 75 를 재구성하고 이번 라운드의 새 수를 준다."""
    be1_131 = 25 * (1 + 2)
    be2_131 = 25 * 2
    # 라운드 132: B/e=2 는 T · D-alpha · D-beta0 로 갈리고 D-beta1 은 죽는다.
    be2_132 = 25 * 3
    be1_132 = 25 * (1 + 2)
    return dict(
        be1_round131=be1_131,
        be1_round131_reason="25 split shapes x (P0 needs 1 branch: both opener locks "
                            "unconditional; P1 needs 2: opener_0's lock is undecidable at "
                            "lock time, so alpha/beta)",
        be1_round132=be1_132,
        be1_round132_note="the count is unchanged, but P0's opener_1 lock is now PROVED "
                          "unconditional (Theorem 132.1) and beta gains the full order nest",
        be2_round131=be2_131, be2_round132=be2_132,
        be2_round132_note="the alpha branch splits into Model T (positive orbit constraint) "
                          "and Model D-alpha (negative one); D-beta0 is the old beta; "
                          "D-beta1 is analytically dead",
        split_shapes_grouped=False,
        split_shape_note="no proved grouping of the 25 ordered (b_0, b_1) shapes: the order "
                         "and orbit theorems are stated for arbitrary b and do not depend "
                         "on coarse features, so all 25 survive")


# ------------------------------------------------------------------ n = 4 검증
def n4_checks(maxlen=39):
    """정리 132.1 과 order type 을 `n = 4` (x = 0 등호 walk) 로 검사한다."""
    n = 4
    g = setup(n)
    perms, idx, sg, ta, om = g["perms"], g["idx"], g["sig"], g["tau"], g["omega"]
    orbid, hexid, orbph = g["orbid"], g["hexid"], g["orbph"]
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
    viol = Counter()
    stat = Counter()
    for L, seq in ws:
        m = walk_measure(g, W, seq, L)
        if m["G"] != 2 or m["x"] != 0 or m["f_out"] != m["F"] + m["e"]:
            continue
        passes, hexes, nu = m["passes"], m["hexes"], m["nu"]
        P = len(passes)
        cnt = Counter(hexes)
        multi = [h for h in dict.fromkeys(hexes) if cnt[h] >= 2]
        if not (len(multi) == 2 and all(cnt[h] == 2 for h in multi)):
            continue
        stat["typeB_x0_equality"] += 1
        ps = [[i for i in range(P) if hexes[i] == h] for h in multi]
        (o0, c0), (o1, c1) = ps[0], ps[1]
        orbs = [orbid[u] for (u, _) in passes]
        runs, cur = [], [0]
        for i in range(1, P):
            if orbs[i] == orbs[i - 1]:
                cur.append(i)
            else:
                runs.append(cur)
                cur = [i]
        runs.append(cur)
        runof = [0] * P
        for ri, r in enumerate(runs):
            for p in r:
                runof[p] = ri
        free = [False] * P
        for i in range(P - 1):
            free[i] = (idx[ta(perms[passes[nu[i]][0]])] == passes[i + 1][0])
        Q0, Q1 = orbid[passes[o0][0]], orbid[passes[o1][0]]
        T0, T1 = orbid[passes[c0][0]], orbid[passes[c1][0]]
        lock0 = (runof[c0] == runof[o0 + 1]) if o0 + 1 < P else False
        lock1 = (runof[c1] == runof[o1 + 1]) if o1 + 1 < P else False
        stat[f"e{m['e']}_lock{int(lock0)}{int(lock1)}"] += 1
        # --- 정리 132.1 --------------------------------------------------
        if not lock1:
            viol["Theorem 132.1: opener_1's lock always holds"] += 1
        # --- alpha 사슬 ----------------------------------------------------
        if lock0 and lock1:
            if not (o0 < c0 == o0 + (n - 1) < o1 < c1 == o1 + (n - 1)):
                viol["alpha chain"] += 1
        # --- beta nest ------------------------------------------------------
        if not lock0:
            if T0 != Q1:
                viol["beta: T_0 = Q_1"] += 1
            if not (o0 < o1 < c1 < c0):
                viol["beta nest order o0 < o1 < c1 < c0"] += 1
            if c1 != o1 + (n - 1):
                viol["beta: closer_1 = opener_1 + (n-1)"] += 1
            if c0 != o0 + 2 * (n - 1):
                viol["beta: closer_0 = opener_0 + 2(n-1)"] += 1
            if sum(1 for u in range(NW) if orbid[u] == Q1) != \
                    len({orbph[passes[i][0]] for i in range(P) if orbs[i] == Q1}):
                viol["beta: Q_1 is full"] += 1
            stat["beta_walks"] += 1
        # --- D-beta1 은 없어야 한다 ------------------------------------------
        if m["e"] == 2 and lock0 and not lock1:
            viol["D-beta1 must be empty"] += 1
        # --- 모형 T / D --------------------------------------------------------
        if m["e"] == 2:
            stat["e2_modelT" if Q0 == Q1 else "e2_modelD"] += 1
            if Q0 == Q1 and not (lock0 and lock1):
                viol["Model T: both locks unconditional"] += 1
    return dict(n=4, typeB_x0_equality=stat["typeB_x0_equality"],
                beta_walks=stat["beta_walks"],
                lock_census={k: v for k, v in sorted(stat.items()) if k.startswith("e")},
                violations=dict(viol), clean=(len(viol) == 0))


def summarise(n4=None, exch=None):
    d = dict(round=132, cell="(k,G) = (4,2)", outer_axis="G (never F)",
             notation=notation(), be1_patterns=be1_patterns(),
             repeat_orbit=repeat_orbit_formula(), theorem_132_1=theorem_132_1(),
             lock_table=lock_table(), coincidence=orbit_coincidence_census(),
             order_types=order_types(), models=split_multiplicity_models(),
             audit=audit_alpha_beta(), budget=budget(), run_counts=run_counts())
    if n4 is not None:
        d["n4_checks"] = n4
    if exch is not None:
        d["exchange"] = exch
    return d


if __name__ == "__main__":
    d = summarise(n4_checks(), exchange_soundness())
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_b_hardcore_132.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps({k: d[k] for k in ("n4_checks", "exchange", "budget", "run_counts")},
                     ensure_ascii=False, indent=1))
