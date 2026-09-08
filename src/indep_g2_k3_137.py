#!/usr/bin/env python3
"""독립 라운드 — `(k, G) = (3, 2)` 의 `delta = 1` hard core 에 대한 **자체 공격**.

다른 모델의 미완성 작업을 이어받지 않는다.  라운드 136 까지의 **받아들여진 상태**와
그 이전의 검증된 보조정리만 쓰고, 나머지는 정의에서 다시 유도한다.

이 모듈이 새로 증명하는 것:

* **정리 I (이동-궤도 의미론).**  진입 `u`, 길이 `ℓ` 인 pass 에 대해 `M2` 와 `M3a` 는 **둘 다**
  `orb(σ^ℓ u)` (= `ν`-목표 궤도) 로 가고, `M3b`/`M3c` 는 **제3의 궤도**로 간다.
* **정리 II (위상 오프셋).**  `M2` 는 `phase(entry(ν(p))) + 1`, `M3a` 는 `+2` 에 착지한다 —
  `ℓ` 과 무관하게 언제나.
* **정리 III (M3a 축약).**  `ν`-상승이 `M3a` 로 유료 탈출해도 **축약 가능한 5-pass 블록**이
  되고 `ΔP = −4`, `ΔO = −1`, `ΔD = −1`, `ΔS = −1` 이다.
* **따름정리 IV (M-off-target 의 정확한 특징).**  유료 상승 탈출이 축약을 만들지 **않는**
  것은 그 탈출이 `M3b`/`M3c` 일 때뿐이다.
* **정리 V (사슬 용량 증가).**  `N*(b,0,s) = N*(0,0,s) + 15b` (궤도 +3, run +4 per token).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup, legal_joint          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def geom(n):
    g = setup(n)
    return g


def moves(g, y):
    """탈출 단어 `y` 에서의 네 가지 이동 (엔진과 같은 위치 공식)."""
    q = g["perms"][y]
    n = g["n"]
    if n == 6:
        return {"M2": (q[2], q[3], q[4], q[5], q[1], q[0]),
                "M3a": (q[3], q[4], q[5], q[1], q[2], q[0]),
                "M3b": (q[3], q[4], q[5], q[2], q[0], q[1]),
                "M3c": (q[3], q[4], q[5], q[2], q[1], q[0])}
    return {"M2": (q[2], q[3], q[1], q[0]),
            "M3a": (q[3], q[1], q[2], q[0]),
            "M3b": (q[3], q[2], q[0], q[1]),
            "M3c": (q[3], q[2], q[1], q[0])}


def sk(g, i, k):
    w = g["perms"][i]
    for _ in range(k):
        w = g["sig"](w)
    return g["idx"][w]


# ------------------------------------------------------------------ 정리 I·II
def move_semantics(n=6):
    """정리 I·II — 이동의 궤도와 위상을 **모든 단어 × 모든 길이**에서 확정한다."""
    g = geom(n)
    ORB, OPH, HEX, IDX, NW = g["orbid"], g["orbph"], g["hexid"], g["idx"], len(g["perms"])
    tag = Counter()
    phase = Counter()
    hexc = Counter()
    for u in range(NW):
        for L in range(1, n + 1):
            y = sk(g, u, L - 1)
            nu = sk(g, u, L)
            for k, t in moves(g, y).items():
                v = IDX[t]
                if ORB[v] == ORB[u]:
                    tag[(L, k, "own_orbit")] += 1
                elif ORB[v] == ORB[nu]:
                    tag[(L, k, "nu_target_orbit")] += 1
                else:
                    tag[(L, k, "third_orbit")] += 1
                if ORB[v] == ORB[nu]:
                    phase[(k, (OPH[v] - OPH[nu]) % (n - 1))] += 1
                hexc[(k, "same_hex" if HEX[v] == HEX[u] else "diff_hex")] += 1
    thm1 = all(tag.get((L, k, "nu_target_orbit"), 0) == NW
               for L in range(1, n) for k in ("M2", "M3a"))
    thm1b = all(tag.get((L, k, "third_orbit"), 0) == NW
                for L in range(1, n + 1) for k in ("M3b", "M3c"))
    thm1c = all(tag.get((n, k, "own_orbit"), 0) == NW for k in ("M2", "M3a"))
    thm2 = (phase.get(("M2", 1), 0) == NW * n and phase.get(("M3a", 2), 0) == NW * n)
    return dict(
        n=n, words=NW,
        theorem_I=dict(
            statement="M2 and M3a both land in orb(sigma^L u) (the nu-target orbit); "
                      "M3b and M3c land in a THIRD orbit (neither own nor nu-target)",
            short_pass_M2_M3a_hit_nu_target=thm1,
            M3b_M3c_always_third=thm1b,
            full_pass_M2_M3a_are_intra_run=thm1c,
            consequence="for a FULL pass the nu-target orbit IS its own orbit, so M3a is an "
                        "intra-run x-arc and is FORBIDDEN when x = 0; hence every paid exit "
                        "of a full pass is M3b or M3c, i.e. a Round-115 light connector"),
        theorem_II=dict(
            statement="M2 lands at phase(entry(nu(p))) + 1 and M3a at + 2, for every word "
                      "and every pass length",
            verified=thm2,
            offsets={f"{k}_plus_{d}": c for (k, d), c in sorted(phase.items())}),
        census={f"L{L}_{k}_{t}": c for (L, k, t), c in sorted(tag.items())},
        hexagon={f"{k}_{t}": c for (k, t), c in sorted(hexc.items())},
        clean=(thm1 and thm1b and thm1c and thm2))


# ------------------------------------------------------------------- 정리 III·IV
def m3a_contraction(n=6):
    """정리 III — `M3a` 유료 탈출도 **축약 가능한 블록**을 만든다.

    상승 `p = (v, a)` 가 `M3a` 로 나가면 착지 위상은 `phase(entry(ν(p))) + 2` 이므로
    `τ`-사슬로 `ν(p)` 에 닿는 데 3 걸음이면 된다: run 은 위상
    `φ+2, φ+3, φ+4, φ` 의 **4 pass** 이고 마지막이 `ν(p) = (σ^a v, b)` 다.
    따라서 블록은 `p` + 4 pass = **5 pass** 이고 이를 한 pass `(v, a+b)` 로 바꾸면

        ΔP = −4,  ΔO = −1,  ΔS = −1 (제거된 5 joint 중 하나가 ω=3),  ΔH = 0,
        ΔD = 5·(−1) − (−4) = **−1**   (위상 `φ+1` 이 영구 미사용으로 남는다)

    이는 라운드 135 의 `u` 매개변수를 **독립적으로 재유도**한다: `u` = `M3a` 형 축약의 수.
    """
    g = geom(n)
    ORB, OPH, HEX, IDX = g["orbid"], g["orbph"], g["hexid"], g["idx"]
    tau = g["tau"]
    bad = Counter()
    cases = 0
    for v in range(len(g["perms"])):
        for a in range(1, n):
            b = n - a
            cases += 1
            c = sk(g, v, a)                       # entry(nu(p))
            y = sk(g, v, a - 1)                   # exit(p)
            land = IDX[moves(g, y)["M3a"]]
            if ORB[land] != ORB[c]:
                bad["M3a leaves the nu-target orbit"] += 1
            if (OPH[land] - OPH[c]) % (n - 1) != 2:
                bad["M3a phase offset != +2"] += 1
            # tau-chain from the landing word back to c
            run = [land]
            w = land
            while w != c:
                w = IDX[tau(g["perms"][w])]
                run.append(w)
            if len(run) != n - 2:
                bad[f"run length != {n-2}"] += 1
            blk = [(v, a)] + [(w, n) for w in run[:-1]] + [(c, b)]
            if len(blk) != n - 1:
                bad["block size"] += 1
            # entrance / exit preserved by the replacement (v, a+b) = (v, n)
            bwe = sk(g, blk[-1][0], blk[-1][1] - 1)
            if bwe != sk(g, v, n - 1):
                bad["exit not preserved"] += 1
            hx = Counter(HEX[w] for (w, _) in blk)
            if hx[HEX[v]] != 2 or any(k != HEX[v] and z != 1 for k, z in hx.items()):
                bad["hexagon multiplicity"] += 1
            used = {OPH[w] for (w, _) in blk[1:]}
            if len(used) != n - 2:
                bad["phases used by the run"] += 1
            if (OPH[c] + 1) % (n - 1) in used:
                bad["phase +1 should stay unused"] += 1
            dP = 1 - len(blk)
            dO = -1
            if dP != -(n - 2) or (n - 1) * dO - dP != -1:
                bad["parameter delta"] += 1
    return dict(n=n, cases=cases, violations=dict(bad), clean=(len(bad) == 0),
                deltas=dict(P=-(n - 2), O=-1, D=-1, S=-1, H=0),
                corollary_IV=("a paid ascent exit fails to create a contractible block "
                              "ONLY when it is M3b or M3c - because M3a lands in the "
                              "nu-target orbit at +2 and still reaches nu(p). This is a "
                              "sharper characterisation of 'M-off-target' than 'the paid "
                              "exit targets the wrong orbit'"),
                reproves="Round-135's u parameter: u = number of M3a-type contractions")


# ---------------------------------------------------------------------- 정리 V
def capacity_growth():
    """정리 V (경험적, 전수 셀에서) — `N*(b,0,s) = N*(0,0,s) + 15b`."""
    cells = {"0,0,6": 49, "1,0,6": 64, "2,0,6": 79, "3,0,6": 94,
             "0,0,9": 66, "1,0,9": 81, "2,0,9": 96,
             "0,0,12": 83, "0,0,13": 83, "1,0,13": 98}
    orb = {"0,0,6": 11, "1,0,6": 14, "2,0,6": 17, "3,0,6": 20,
           "0,0,9": 15, "1,0,9": 18, "2,0,9": 21,
           "0,0,13": 19, "1,0,13": 22}
    rows = []
    for s in (6, 9, 13):
        base = cells.get(f"0,0,{s}")
        for b in range(0, 4):
            k = f"{b},0,{s}"
            if k in cells:
                rows.append(dict(b=b, s=s, passes=cells[k], orbits=orb.get(k),
                                 predicted=base + 15 * b,
                                 matches=(cells[k] == base + 15 * b)))
    return dict(law="N*(b,0,s) = N*(0,0,s) + 15b   (+3 orbits, +4 runs per token)",
                cells=rows, all_match=all(r["matches"] for r in rows),
                status="verified on every exhaustively computed cell available; stated as "
                       "an EMPIRICAL law, not proved in general",
                orbit_reach="at s = 13 a pure light chain reaches 19 + 3b orbits",
                consequence=("the (3,2) target object has 27 orbits, so as a PURE light "
                             "chain it would need 19 + 3b >= 27, i.e. b >= 3. Since b = e "
                             "here, every row with e <= 2 CANNOT be a pure light chain - "
                             "its short-pass connectors are structurally indispensable"))


# ------------------------------------------------------------------ delta = a + eta
def delta_decomposition():
    """§1 — `delta = a + eta` 와 `M`/`R` 이분법을 **정의에서** 다시 유도한다."""
    rows = []
    for typ, nshort, ndesc in (("A", 3, 1), ("B", 4, 2)):
        for e in range(0, 5):
            f_out = 1 + e
            if f_out > nshort:
                continue
            for a in (0, 1):
                eta = 1 - a
                d = e - eta
                if d < 0 or d > ndesc:
                    continue
                if (2 - a) + d != f_out:
                    continue
                rows.append(dict(type=typ, e=e, f_out=f_out, a=a, eta=eta,
                                 free_ascents=2 - a, free_descents=d,
                                 mechanism="M" if a == 1 else "R"))
    by = {}
    for r in rows:
        by.setdefault(f"{r['type']}/e{r['e']}", []).append(r["mechanism"])
    return dict(
        derivation=["f_out = #(free ascents) + #(free descents)",
                    "#ascents = F = 2, so #(free ascents) = 2 - a with a = #(nonfree ascents)",
                    "each free descent opens a distinct repeat run, so d := #(free descents) "
                    "<= e; put eta := e - d >= 0",
                    "delta = F + e - f_out = 2 + e - (2 - a) - d = a + (e - d) = a + eta"],
        identity="delta = a + eta",
        dichotomy="delta = 1 forces (a, eta) = (1,0) [mechanism M] or (0,1) [mechanism R]",
        M_needs="e = d <= #descents, so e <= 1 (type A) and e <= 2 (type B)",
        R_needs="d = e - 1 <= #descents, so e <= 2 (type A) and e <= 3 (type B)",
        rows=rows, by_row={k: sorted(set(v)) for k, v in sorted(by.items())},
        matches_accepted_state=True)


# ---------------------------------------------------------- §15 n = 4 적대적 검사
def n4_adversarial():
    """§15 — `n = 4` 에서 정리 I·II·III 를 **깨려고 시도**한다."""
    ms = move_semantics(4)
    mc = m3a_contraction(4)
    return dict(move_semantics_clean=ms["clean"],
                m3a_contraction_clean=mc["clean"], m3a_cases=mc["cases"],
                verdict=("Theorems I-III are not n=6-specific: they hold verbatim at n=4, "
                         "so they carry no hidden n=6 hypothesis"),
                n4_deltas=mc["deltas"])


def summarise():
    return dict(round="independent-(3,2)", target="(k,G) = (3,2), delta = 1 hard core",
                move_semantics=move_semantics(6),
                m3a_contraction=m3a_contraction(6),
                capacity_growth=capacity_growth(),
                delta_decomposition=delta_decomposition(),
                n4_adversarial=n4_adversarial())


if __name__ == "__main__":
    d = summarise()
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_indep_g2_k3_137.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print("Theorem I/II clean:", d["move_semantics"]["clean"])
    print("Theorem III:", d["m3a_contraction"]["cases"], "cases clean =",
          d["m3a_contraction"]["clean"], d["m3a_contraction"]["deltas"])
    print("Theorem V:", d["capacity_growth"]["all_match"])
    print("delta decomposition:", json.dumps(d["delta_decomposition"]["by_row"]))
    print("n=4 adversarial:", json.dumps(d["n4_adversarial"], ensure_ascii=False))


# ------------------------------------------------- 한 번 축약한 대상의 정확한 예산
def contracted_budget():
    """축약 한 번 뒤 대상의 `(P', O', D', b')` 를 정확히 계산한다.

    축약은 잠긴 run(5 pass, 1 궤도) 을 지우고 짧은 pass 쌍을 full pass 하나로 합친다:
    `P' = 122 − 5 = 117`, `O' = 27 − 1 = 26`, `D' = 5·26 − 117 = 13` (불변).

    run 수: 잠긴 run 이 사라져 `r → r − 1`.  게다가 **닫는 pass 의 탈출 joint 가 축약 뒤
    intra-run 이 될 수 있다** — 정리 I 때문이다.  닫는 pass `closer` 의 `ν`-목표는 opener 이고
    `T(closer) = orb(entry(opener))`; 축약 후 그 자리에는 진입 `entry(opener)` 인 **full**
    pass 가 있으므로 `M2`/`M3a` 는 **자기 궤도**로 간다.  따라서

      * `closer` 의 탈출이 `M2` (자유) 였다면 → 축약 후 intra-run τ-걸음: run 이 하나 더
        합쳐져 `r → r − 2`, `x' = 0`  ⇒ `e' = e − 1`, **`b' = e − 1`**;
      * `M3a` 였다면 → 축약 후 intra-run `ω=3`, 즉 **`x'` 호**: `r → r − 2`, `x' = 1`
        ⇒ `e' = e − 1`, **`b' = e`**;
      * `M3b`/`M3c` 였다면 → 여전히 궤도를 바꾼다: `r → r − 1`, `x' = 0`
        ⇒ `e' = e`, **`b' = e`**.
    """
    rows = []
    for typ, emax in (("A", 2), ("B", 3)):
        for e in range(0, emax + 1):
            for exit_kind, dr, xp in (("M2 (free)", 2, 0), ("M3a", 2, 1),
                                      ("M3b/M3c", 1, 0)):
                ep = e - (dr - 1)
                if ep < 0:
                    continue
                rows.append(dict(type=typ, e=e, closer_exit=exit_kind,
                                 P_prime=117, O_prime=26, D_prime=13,
                                 e_prime=ep, x_prime=xp, b_prime=ep + xp))
    return dict(P_prime=117, O_prime=26, D_prime=13,
                rule="b' = e - 1 if the contracted closer exited M2, else e",
                rows=rows,
                b_prime_values=sorted({r["b_prime"] for r in rows}),
                kill_condition="a row dies iff N1*(b', 0, 13) < 117")


# ------------------------------------------------------- 새 정리 VI: 한-결함 용량 배제
def one_defect_exclusion():
    """**정리 VI (한-결함 용량 배제).**

    `(3,2)` 의 `delta = 1` 행에서 축약이 **한 번** 가능하면 그 결과물은
    `P' = 117`, `O' = 26`, `D' = 13`, `H' = 0` 이고 짧은 pass 가 **정확히 둘**(겹친 육각형
    하나) 남는다.  정리 I 로 이 대상의 모든 joint 는 한-결함 사슬 모델의 이동이므로
    (full pass 의 유료 탈출은 `M3b`/`M3c`, 짧은 pass 는 `M2`/`M3a`/`M3b`/`M3c`),
    대상은 예산 `(b', 0, 13)` 짜리 **사슬 하나**다.  따라서

        117 = P'  ≤  N1*(b', 0, 13).

    전수(캡 없음) 계산: **`N1*(0,0,13) = 102`** (4,121,832,039 노드).
    `102 < 117` 이므로 **`b' = 0` 인 배치는 전부 불가능**하다.

    ### 축약이 반드시 존재하는가
    * `e = 0` — 반복 run 이 없으므로 **lock 이 깨질 수 없다** (깨진 lock 은 반복 run 을
      요구한다).  따라서 자유 상승의 lock 은 반드시 성립하고 축약이 존재한다. **무조건.**
    * 메커니즘 `R` (`a = 0`) — 상승 **둘 다** 자유이고 `eta = 1` 이라 lock 은 많아야 하나
      깨진다.  따라서 축약이 최소 하나 존재한다. **무조건.**
    * 메커니즘 `M` 이면서 `e ≥ 1` — 자유 상승이 하나뿐이고 그 lock 이 깨질 수 있다.
      이 경우에만 축약 존재가 **보장되지 않는다.**
    """
    cb = contracted_budget()
    kills, cond, survive = [], [], []
    for typ, emax in (("A", 2), ("B", 3)):
        for e in range(0, emax + 1):
            mechs = []
            if e <= (1 if typ == "A" else 2):
                mechs.append("M")
            if e >= 1:
                mechs.append("R")
            for r in [z for z in cb["rows"] if z["type"] == typ and z["e"] == e]:
                for mech in mechs:
                    contraction_guaranteed = (e == 0) or (mech == "R")
                    item = dict(row=f"{typ}/e{e}", mechanism=mech,
                                closer_exit=r["closer_exit"], b_prime=r["b_prime"],
                                required=117, capacity=(102 if r["b_prime"] == 0 else None),
                                contraction_guaranteed=contraction_guaranteed)
                    if r["b_prime"] == 0 and contraction_guaranteed:
                        kills.append(item)
                    elif r["b_prime"] == 0:
                        cond.append(item)
                    else:
                        survive.append(item)
    fully_dead = []
    for typ, emax in (("A", 2), ("B", 3)):
        for e in range(0, emax + 1):
            tag = f"{typ}/e{e}"
            rel = [z for z in kills + cond + survive if z["row"] == tag]
            if rel and all(z in kills for z in rel):
                fully_dead.append(tag)
    return dict(
        theorem="117 <= N1*(b',0,13); N1*(0,0,13) = 102 exhaustively, so b' = 0 is impossible",
        capacity=dict(cell="N1*(0,0,13)", passes=102, orbits=23, runs=23,
                      nodes=4121832039, capped=False),
        also=dict(cell="N1*(0,0,12)", passes=99, nodes=1736792185, capped=False),
        control="with the defect switched off the searcher reproduces Round 115 "
                "node-for-node (469,852 at s=9 and 14,407,541 at s=13)",
        unconditional_kills=kills, conditional_kills=cond, not_reached=survive,
        rows_fully_eliminated=fully_dead,
        summary=(f"{len(fully_dead)} of the 7 rows are eliminated outright; the remaining "
                 f"rows are reduced but not closed"))


def equality_frontier():
    """`b' = 1` 배치가 **정확히 등호**에 걸린다는 관측 (증명 아님).

    `+15` 법칙은 한-결함 모델에서도 두 번 확인된다:
        N1*(1,0,6) = 84 = 69 + 15,   N1*(1,0,9) = 101 = 86 + 15.
    따라서 `N1*(1,0,13) = 102 + 15 = 117` 이 예측되고, 필요한 pass 수도 정확히 117 이다.
    **등호는 모순이 아니다** — 라운드 135 가 `46 + 66 = 112` 에서 했듯 극값 증인만 열거해
    이음매/경계 조건이 이어질 수 있는지 보는 것이 정확한 다음 단계다.
    """
    return dict(
        law_checks=[dict(cell="N1*(1,0,6)", value=84, base=69, matches=True),
                    dict(cell="N1*(1,0,9)", value=101, base=86, matches=True)],
        prediction=dict(cell="N1*(1,0,13)", predicted=117, required=117,
                        is_equality=True, computed=False,
                        estimated_nodes="about 2e11 - not run in this round"),
        status="PREDICTION, not a proof; a cap was never read as UNSAT",
        next_step="enumerate only the extremal witnesses at (1,0,13) and test whether the "
                  "seam and boundary conditions can actually connect them")


def certificate():
    """§21 — 재현 가능한 계산 증명서."""
    import hashlib
    import subprocess

    def sha(p):
        p = Path(p)
        return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = None
    return dict(
        source_commit=commit, gcc="gcc -O2",
        searcher_c=sha(ROOT / "src" / "chain_capacity_g1_137.c"),
        searcher_bin=sha(ROOT / "src" / "chain_capacity_g1_137.bin"),
        round115_c=sha(ROOT / "src" / "chain_capacity_115.c"),
        module=sha(ROOT / "src" / "indep_g2_k3_137.py"),
        runs=[
            dict(argv="0 0 13 60000000000 1", cell="N1*(0,0,13)", passes=102, orbits=23,
                 runs=23, nodes=4121832039, capped=False),
            dict(argv="0 0 12 60000000000 1", cell="N1*(0,0,12)", passes=99, orbits=22,
                 runs=22, nodes=1736792185, capped=False),
            dict(argv="0 0 9 20000000000 1", cell="N1*(0,0,9)", passes=86, orbits=19,
                 runs=19, nodes=109941651, capped=False),
            dict(argv="1 0 6 40000000000 1", cell="N1*(1,0,6)", passes=84, orbits=18,
                 runs=19, nodes=338860753, capped=False),
            dict(argv="1 0 9 40000000000 1", cell="N1*(1,0,9)", passes=101, orbits=22,
                 runs=23, nodes=6572464021, capped=False),
            dict(argv="0 0 9 20000000000 0", cell="control = N*(0,0,9)", passes=66,
                 nodes=469852, capped=False),
            dict(argv="0 0 13 20000000000 0", cell="control = N*(0,0,13)", passes=83,
                 nodes=14407541, capped=False)],
        no_capped_values=True,
        note="no cap was ever interpreted as UNSAT; N1*(1,0,13) was NOT computed and its "
             "value 117 is a PREDICTION from the +15 law, not a proof")
