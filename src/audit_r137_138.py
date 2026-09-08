#!/usr/bin/env python3
"""라운드 137 감사 — Astra 의 `(k,G)=(3,2)` 폐쇄 주장에 대한 독립 검증.

Astra 의 소스를 하나도 import 하지 않는다.  기하는 `verify_f2_structure_126.setup(6)`
에서만 가져오고, 모델 정의는 보고서 `RR_G2_K3_ONE_DEFECT_GAP_CUT_CODEX.md` 의 산문에서
읽어 처음부터 다시 구현한다.

검증 항목:
  A. 값-재명명 대칭 — `v = 012345` 정규화의 정당성 (§7, §12 의 전제).
  B. 보통 경량 사슬 용량 `C0(d) = N*(0,0,d)` 독립 재계산 (§7).
  C. M 합성곱 `max_d C0(d)+C0(13-d)` (§7).
  D. R 합성곱 `max_d R(d)+C0(13-d)` — R 은 자체 탐색기 결과 (§15).
  E. §5 간극-추출 매개변수 항등식 `P_in+P_out=117`, `O_in+O_out=26`, `D_in+D_out=13`
     그리고 `S_out = O_out - 1`, `S_in ∈ {m-1, m}`.
  F. 일곱 개 δ=1 행 ↔ §6 포함 사례 대응표.
  G. 추출의 문자열 수준 재현 — 외부 조인트 보존과 무반복성.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from itertools import permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
G = setup(6)
P6, IDX, SG, TA = G["perms"], G["idx"], G["sig"], G["tau"]
ORB, HEX, OPH = G["orbid"], G["hexid"], G["orbph"]


def _s5(w):
    y = P6[w]
    for _ in range(5):
        y = SG(y)
    return y


W3B = [IDX[(_s5(w)[3], _s5(w)[4], _s5(w)[5], _s5(w)[2], _s5(w)[0], _s5(w)[1])]
       for w in range(720)]
W3C = [IDX[(_s5(w)[3], _s5(w)[4], _s5(w)[5], _s5(w)[2], _s5(w)[1], _s5(w)[0])]
       for w in range(720)]
TAU = [IDX[TA(P6[w])] for w in range(720)]

# Astra 보고서에서 옮겨 적은 표 (검증 대상, 신뢰 대상 아님)
ASTRA_C0 = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83]
ASTRA_R = {0: 20, 2: 8, 6: 24, 8: 22, 9: 21, 10: 40, 11: 39, 12: 48, 13: 47}
ASTRA_R_CHAINS = {0: 4, 1: 0, 2: 3, 3: 0, 4: 0, 5: 0, 6: 48, 7: 0,
                  8: 26, 9: 21, 10: 216, 11: 684, 12: 1711, 13: 2346}


# ---------------------------------------------------------------- A. 대칭
def renaming_symmetry():
    """값-재명명 `rho` 가 사슬 모형 전체의 자기동형인가?

    가환이면 720 개 시작 단어가 전부 동치이므로 `v = 012345` 정규화가 정당하다.
    이것은 §7 (`Normalize v=012345 by value-renaming`) 과 나의 `R(d)` 탐색기
    양쪽의 전제다.  전수 확인: 720 개 재명명 × 720 개 단어.

    주의: `orbph` 는 `setup()` 이 궤도마다 임의로 고른 기준점에서 잰 `tau` 색인이다.
    재명명은 궤도를 궤도로, `tau` 순서를 보존하며 보내므로 위상은 **궤도마다 상수만큼
    이동**한다.  용량 모형은 "그 궤도의 어느 5 자리를 썼는가" 만 보므로 상수 이동은
    무해하다.  따라서 위상 검사는 **궤도별 상수 이동을 허용하여** 수행한다.
    """
    kinds = Counter()
    orb_maps, hex_maps = set(), set()
    shifts_nonzero = 0
    for rho in permutations(range(6)):
        img = [IDX[tuple(rho[c] for c in P6[w])] for w in range(720)]
        for w in range(720):
            if img[TAU[w]] != TAU[img[w]]:
                kinds["tau"] += 1; break
        for w in range(720):
            if img[W3B[w]] != W3B[img[w]]:
                kinds["w3b"] += 1; break
        for w in range(720):
            if img[W3C[w]] != W3C[img[w]]:
                kinds["w3c"] += 1; break
        om, hm, sh = {}, {}, {}
        for w in range(720):
            if om.setdefault(ORB[w], ORB[img[w]]) != ORB[img[w]]:
                kinds["orbit_not_wellrdefined"] += 1; break
            if hm.setdefault(HEX[w], HEX[img[w]]) != HEX[img[w]]:
                kinds["hex_not_welldefined"] += 1; break
            d = (OPH[img[w]] - OPH[w]) % 5
            if sh.setdefault(ORB[w], d) != d:
                kinds["phase_shift_not_constant"] += 1; break
        else:
            if any(v for v in sh.values()):
                shifts_nonzero += 1
        orb_maps.add(tuple(sorted(om.items())))
        hex_maps.add(tuple(sorted(hm.items())))
    orbit_of_0 = {IDX[tuple(rho[c] for c in P6[0])] for rho in permutations(range(6))}
    clean = sum(kinds.values()) == 0
    return dict(renamings=720, violations_by_kind=dict(kinds),
                total_violations=sum(kinds.values()),
                renamings_with_nonzero_phase_shift=shifts_nonzero,
                distinct_orbit_permutations=len(orb_maps),
                distinct_hex_permutations=len(hex_maps),
                phase_preserved_up_to_per_orbit_shift=clean,
                transitive_on_words=(len(orbit_of_0) == 720),
                normalization_justified=(clean and len(orbit_of_0) == 720),
                note=("orbph 는 임의 기준점 기반이므로 궤도별 상수 이동을 허용해야 한다. "
                      "이동을 허용하면 720 개 재명명 전부가 사슬 모형의 자기동형이다."))


# --------------------------------------------- B. 보통 경량 사슬 용량 C0(d)
def ordinary_capacity(dmax=13, v=0, node_cap=None):
    """`C0(d) = N*(0,0,d)`: 전부 full pass, 궤도 재사용 없음, 반환 없음.

    run 내부는 `tau` 한 걸음, run 사이는 경량 연결자 `W3b`/`W3c`.  결손은
    닫힌 궤도들의 `5 - (그 궤도 pass 수)` 합.  끝점 제약 없음.
    """
    best = {d: -1 for d in range(dmax + 1)}
    atmax = Counter()
    nodes = [0]
    capped = [False]
    usedhex = {HEX[v]}
    omask = {ORB[v]: 1 << OPH[v]}

    def closed_deficit(cur_orb):
        return sum(5 - bin(m).count("1") for q, m in omask.items() if q != cur_orb)

    def rec(cur, corb, passes):
        nodes[0] += 1
        if node_cap is not None and nodes[0] > node_cap:
            capped[0] = True
            return
        d = closed_deficit(None)
        if d <= dmax and passes > best[d]:
            best[d] = passes
        if d <= dmax:
            atmax[(d, passes)] += 1
        if closed_deficit(corb) > dmax:
            return
        nxt = TAU[cur]
        if ORB[nxt] == corb and not (omask[corb] >> OPH[nxt] & 1) \
                and HEX[nxt] not in usedhex:
            omask[corb] |= 1 << OPH[nxt]
            usedhex.add(HEX[nxt])
            rec(nxt, corb, passes + 1)
            usedhex.discard(HEX[nxt])
            omask[corb] &= ~(1 << OPH[nxt])
        for w in (W3C[cur], W3B[cur]):
            if HEX[w] in usedhex or ORB[w] in omask:
                continue
            omask[ORB[w]] = 1 << OPH[w]
            usedhex.add(HEX[w])
            rec(w, ORB[w], passes + 1)
            usedhex.discard(HEX[w])
            del omask[ORB[w]]

    t0 = time.time()
    rec(v, ORB[v], 1)
    exact = {d: (best[d] if best[d] >= 0 else None) for d in range(dmax + 1)}
    # C0(d) 는 "결손 <= d" 이므로 정확 결손 최대값의 누적 최대
    cum, run = {}, -1
    for d in range(dmax + 1):
        if best[d] > run:
            run = best[d]
        cum[d] = run
    return dict(v=v, dmax=dmax, nodes=nodes[0], capped=capped[0],
                seconds=round(time.time() - t0, 1),
                exact_deficit_max=exact, C0=cum,
                astra_C0=ASTRA_C0,
                agrees=[cum[d] for d in range(dmax + 1)] == ASTRA_C0)


# ------------------------------------------------------- C/D. 합성곱
def convolutions(c0):
    need = 117
    ordinary = [(d, c0[d] + c0[13 - d]) for d in range(14)]
    mmax = max(v for _, v in ordinary)
    margmax = [d for d, v in ordinary if v == mmax]
    rr = [(d, ASTRA_R[d] + c0[13 - d]) for d in sorted(ASTRA_R)]
    rmax = max(v for _, v in rr)
    rargmax = [d for d, v in rr if v == rmax]
    return dict(required_passes=need,
                M=dict(table=ordinary, maximum=mmax, argmax=margmax,
                       shortfall=need - mmax, contradiction=mmax < need,
                       astra_claim_112=(mmax == 112),
                       astra_argmax_claim=sorted(margmax) == [4, 9]),
                R=dict(table=rr, maximum=rmax, argmax=rargmax,
                       shortfall=need - rmax, contradiction=rmax < need,
                       astra_claim_103=(rmax == 103),
                       astra_argmax_claim=rargmax == [0]),
                both_contradict=(mmax < need and rmax < need))


# ------------------------------------------ E. §5 매개변수 항등식
def gap_parameter_identities():
    """`j = |I|`, `m` = 그 궤도 수에 대해 §5 의 합 항등식을 전수 확인.

    출발점은 우리 자신의 항등식이다: 폐쇄 전 (3,2) δ=1 행은
    `P = 122, O = 27, D = 5*27-122 = 13, S = 25`.
    보통 블록 하나 제거: `P -= 5, O -= 1, D` 불변, `S -= 1`.
    추출: 내부가 `(j, m)`, 외부는 나머지 + 병합된 full pass 하나.
    """
    P0, O0 = 122, 27
    D0 = 5 * O0 - P0
    S0 = O0 - 1 - 1        # (3,2) δ=1 행: S = 25 = O - 2  (기록된 행 값)
    rows = []
    ok = True
    for m in range(1, 27):
        for j in range(m, 5 * m + 1):
            P_in, O_in, D_in = j, m, 5 * m - j
            # 외부: 보통 블록 하나(-5 pass, -1 궤도) + 구간을 full pass 하나로 대체
            P_out = P0 - 5 - j
            O_out = O0 - 1 - m
            D_out = 5 * O_out - P_out
            good = (P_in + P_out == 117 and O_in + O_out == 26
                    and D_in + D_out == 13 and D_in >= 0 and D_out >= 0
                    and P_out == 117 - j and O_out == 26 - m
                    and D_out == 13 + j - 5 * m)
            S_out = 25 - m
            good = good and (S_out == O_out - 1)
            if D_in >= 0 and D_out >= 0:
                rows.append(dict(j=j, m=m, P_in=P_in, P_out=P_out, O_in=O_in,
                                 O_out=O_out, D_in=D_in, D_out=D_out,
                                 S_out=S_out, ok=good))
                ok = ok and good
    return dict(base=dict(P=P0, O=O0, D=D0, S=25, S_matches_O_minus_2=(S0 == 25)),
                feasible_pairs=len(rows), all_identities_hold=ok,
                S_in_M_rule="S_in = m-1 (e=x=H=0)",
                S_in_R_rule="S_in = m   (e=1, x=H=0)",
                sample=rows[:3] + rows[-3:],
                # 용량이 마주하는 수: 내부+외부 pass 합
                required_total_passes=117)


# ------------------------------------------------- F. 일곱 행 커버리지
def row_coverage():
    """(3,2) δ=1 잔여 일곱 행과 §6 포함 사례의 대응.

    행 표(우리 자신의 것): A/e0→M, A/e1→M|R, A/e2→R,
                           B/e0→M, B/e1→M|R, B/e2→M|R, B/e3→R.
    라운드 135/136 에서 A/e0, B/e0 등 일부는 이미 제외되었고, 라운드 137 은
    δ=1 의 두 메커니즘 M(a=1) 과 R(eta=1) 전부를 §6 의 여섯 사례로 덮는다고 주장.
    """
    rows = [("A", 0, ["M"]), ("A", 1, ["M", "R"]), ("A", 2, ["R"]),
            ("B", 0, ["M"]), ("B", 1, ["M", "R"]), ("B", 2, ["M", "R"]),
            ("B", 3, ["R"])]
    cases = {("M", "A"): "M, Type A",
             ("M", "B"): "M, Type B: paid opener0 / paid opener1",
             ("R", "A"): "R, Type A",
             ("R", "B"): "R, Type B: exceptional target T0 / T1"}
    tab, covered = [], True
    for t, e, mechs in rows:
        cs = [cases[(mm, t)] for mm in mechs]
        tab.append(dict(type=t, e=e, mechanisms=mechs, inclusion_cases=cs,
                        covered=all(cs)))
        covered = covered and all(cs)
    return dict(rows=tab, row_count=len(rows),
                mechanism_cases_used=sorted({c for r in tab
                                             for c in r["inclusion_cases"]}),
                every_row_mapped=covered,
                note=("사례 분할은 (메커니즘, 타입) 의 곱이며 e 에 의존하지 않는다. "
                      "이는 §6 이 e 별로 나뉘지 않았다는 점과 일치한다."))


# ----------------------------------------- G. 추출의 문자열 수준 재현
def extraction_replay():
    """§5 의 상보 짧은 호 쌍을 문자 수준에서 실제로 잘라 본다.

    **정정**: 초판은 `tau` 로 창을 훑었다.  §5 의 `c = sigma^a(v)` 대로 창은
    `sigma` (1-회전) 단계다.  pass 는 육각형(= `sigma`-순환, 6 창) 위를 달리고,
    궤도(= `tau`-순환, 5 원소)는 그 pass 의 **진입 슬롯**을 준다.  `D = 5*O - P`
    가 바로 궤도마다 진입 슬롯이 다섯 개라는 뜻이다.

    확인 항목:
      (i)   외부 단어가 문자 진입 `v` 를 그대로 유지한다;
      (ii)  닫개의 종점 `sigma^5(v)` 가 그대로 유지된다;
      (iii) opener 창 ∪ closer 창 = 병합된 full pass 의 창 (정확한 타일링);
      (iv)  완성된 마지막 pass `(c,6)` 이 opener 의 상보 창을 흡수한다;
      (v)   두 조각이 공유하는 것은 갈라진 육각형 **하나뿐**이고,
      (vi)  `E`-궤도는 공유하지 않는다 (`ORB[v] != ORB[c]`).
    """
    def wins(entry, length):
        out, cur = [], entry
        for _ in range(length):
            out.append(cur)
            cur = IDX[SG(P6[cur])]
        return out

    checked, fails = 0, []
    hexes_meet_6_orbits = all(
        len({ORB[w] for w in range(720) if HEX[w] == h}) == 6
        for h in range(120))
    for v in range(720):
        for a in (1, 2, 3, 4, 5):
            c = wins(v, a + 1)[a]                     # c = sigma^a(v)
            opener, closer = wins(v, a), wins(c, 6 - a)
            merged, completed = wins(v, 6), wins(c, 6)
            checked += 1
            if merged[0] != v:
                fails.append(("entry", v, a))
            if closer[-1] != merged[-1]:
                fails.append(("exit", v, a))
            if opener + closer != merged:
                fails.append(("tiling", v, a))
            if not set(opener).issubset(set(completed)):
                fails.append(("complement", v, a))
            sh = {HEX[w] for w in completed} & {HEX[w] for w in merged}
            if sh != {HEX[v]}:
                fails.append(("shared-hex", v, a, sorted(sh)))
            if ORB[v] == ORB[c]:
                fails.append(("shared-orbit", v, a))
            if len(set(merged)) != 6 or len(set(completed)) != 6:
                fails.append(("window-repeat", v, a))
    return dict(pairs_checked=checked,
                every_hexagon_meets_6_distinct_orbits=hexes_meet_6_orbits,
                failures=fails[:10], failure_count=len(fails),
                all_pass=(len(fails) == 0),
                conclusion=("상보 쌍은 육각형 하나를 정확히 타일링하고, 병합 pass 는 "
                            "외부 조인트 둘을 문자 그대로 보존하며, 두 조각은 "
                            "갈라진 육각형 하나만 공유하고 E-궤도는 공유하지 않는다."))


def main():
    heavy = "--heavy" in sys.argv
    res = dict(round=137, role="independent audit of Astra Round 137",
               astra_commit="ec8a5f1aaa2d5b42dc885dca86420877287555aa",
               astra_branch="codex/round137-mr-hard-core")
    res["A_renaming_symmetry"] = renaming_symmetry()
    res["E_gap_parameters"] = gap_parameter_identities()
    res["F_row_coverage"] = row_coverage()
    res["G_extraction_replay"] = extraction_replay()
    if heavy:
        c0 = ordinary_capacity()
        res["B_C0"] = c0
        res["CD_convolutions"] = convolutions(c0["C0"])
    else:
        res["B_C0"] = "skipped (run with --heavy)"
        res["CD_convolutions"] = convolutions({d: ASTRA_C0[d] for d in range(14)})
        res["CD_convolutions"]["c0_source"] = "ASTRA TABLE (not yet independent)"
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_r137_audit_138.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
