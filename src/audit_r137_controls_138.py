#!/usr/bin/env python3
"""라운드 137 감사 — Astra 의 835 개 유한 컨트롤 **독립 재현**.

Astra 의 JSON 은 **데이터로만** 읽고 (그들의 코드는 하나도 import 하지 않는다),
문자열 단어에서 창·pass·조인트·궤도를 우리 자신의 기하 `setup(n)` 으로 다시 만든다.

핵심은 §6 의 **사밀성(privacy)** 전제다: 추출된 안쪽 조각과 바깥쪽 조각의 궤도
집합이 서로소여야 한다.  서로소가 아니면 `O_in + O_out = 26` 이 깨지고 결손 예산이
공유 궤도 하나당 5 씩 늘어나 §7 의 용량 모순이 무효가 된다.  835 개 컨트롤에서
그 전제를 직접 검사한다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GEO = {n: setup(n) for n in (4, 6)}


def analyse(word, n):
    """문자 단어 하나를 우리 기하로 완전히 분해한다."""
    g = GEO[n]
    idx = g["idx"]
    pos = [i for i in range(len(word) - n + 1)
           if len(set(word[i:i + n])) == n]
    wins = [idx[tuple(int(ch) for ch in word[i:i + n])] for i in pos]
    if len(set(wins)) != len(wins):
        return dict(literal_no_repeat=False)
    passes, start = [], 0
    for i in range(1, len(pos) + 1):
        if i == len(pos) or pos[i] != pos[i - 1] + 1:
            passes.append((wins[start], i - start))
            start = i
    weights = [pos[sum(l for _, l in passes[:k + 1])] -
               pos[sum(l for _, l in passes[:k + 1]) - 1]
               for k in range(len(passes) - 1)]
    orbs = [g["orbid"][e] for e, _ in passes]
    P = len(passes)
    O = len(set(orbs))
    D = (n - 1) * O - P
    # run = weight-2 조인트로 이어진 pass 들의 최대 묶음
    runs, cur = [], [0]
    for k, w in enumerate(weights):
        if w == 2:
            cur.append(k + 1)
        else:
            runs.append(cur); cur = [k + 1]
    runs.append(cur)
    S = sum(1 for w in weights if w == 3)
    H = sum(w - 3 for w in weights if w > 3)
    return dict(literal_no_repeat=True, positions=pos, passes=passes,
                weights=weights, P=P, O=O, D=D, r=len(runs),
                e=len(runs) - O, S=S, H=H, windows=len(pos),
                orbit_set=sorted(set(orbs)),
                run_orbits=[g["orbid"][passes[r[0]][0]] for r in runs],
                all_full=all(l == n for _, l in passes),
                entry=passes[0][0], exit_window=wins[-1])


def replay(path=None):
    p = Path(path) if path else ROOT / "outputs" / "rr_round137_gap_cut_codex.json"
    g = json.loads(p.read_text())
    rows = g["rows"]
    fail = Counter()
    kinds = Counter()
    shared = []
    checked = 0
    for row in rows:
        n = row["n"]
        cert = row["certificate"]
        kinds[f"{n}/{cert['kind']}"] += 1
        checked += 1
        inn = analyse(cert["inner"]["word"], n)
        out = analyse(cert["outer"]["word"], n)
        if not inn["literal_no_repeat"]:
            fail["inner_repeats_a_permutation"] += 1; continue
        if not out["literal_no_repeat"]:
            fail["outer_repeats_a_permutation"] += 1; continue
        # (1) 사밀성 — 두 조각의 궤도가 서로소인가
        ov = set(inn["orbit_set"]) & set(out["orbit_set"])
        if ov:
            fail["ORBITS_NOT_PRIVATE"] += 1
            shared.append(dict(word=row["word"], n=n, shared=sorted(ov)))
        # (2) 기록된 metric 과 우리 재계산이 같은가
        for tag, mine, rec in (("inner", inn, cert["inner_metrics"]),
                               ("outer", out, cert["outer_metrics"])):
            for k in ("P", "O", "D", "r", "e", "S", "H", "windows"):
                if mine[k] != rec[k]:
                    fail[f"{tag}_metric_{k}"] += 1
        # (3) 조인트 무게가 기록과 같은가
        if inn["weights"] != cert["inner"]["weights"]:
            fail["inner_weights"] += 1
        if out["weights"] != cert["outer"]["weights"]:
            fail["outer_weights"] += 1
        # (4) 모든 pass 가 full 인가 (용량 모형의 전제)
        if not inn["all_full"]:
            fail["inner_not_all_full"] += 1
        if not out["all_full"]:
            fail["outer_not_all_full"] += 1
        # (5) 안쪽 조각이 선언된 종류(M / R)의 모양인가
        ro = inn["run_orbits"]
        if cert["kind"] == "M_FRESH_GAP":
            if len(set(ro)) != len(ro):
                fail["M_gap_has_a_repeated_orbit"] += 1
            if inn["e"] != 0:
                fail["M_gap_e_not_0"] += 1
        else:
            c = Counter(ro)
            twice = [q for q, m in c.items() if m == 2]
            if len(twice) != 1 or any(m > 2 for m in c.values()):
                fail["R_gap_not_exactly_one_doubled_orbit"] += 1
            elif ro[0] != twice[0] or ro[-1] != twice[0]:
                fail["R_gap_root_not_first_and_last_run"] += 1
            if inn["e"] != 1:
                fail["R_gap_e_not_1"] += 1
        # (6) x = H = 0
        if inn["H"] or out["H"]:
            fail["heavy_joint_present"] += 1
        # (7) 결손 비음수
        if inn["D"] < 0 or out["D"] < 0:
            fail["negative_deficit"] += 1
    return dict(rows_checked=checked, kinds=dict(kinds),
                failures=dict(fail), total_failures=sum(fail.values()),
                shared_orbit_examples=shared[:5],
                privacy_holds_on_all_controls=(fail["ORBITS_NOT_PRIVATE"] == 0),
                all_pass=(sum(fail.values()) == 0))


def privacy_sensitivity(C0, R):
    """사밀성이 **얼마나** 하중을 받는지 정량화한다.

    궤도 `s` 개가 두 조각에 걸쳐 공유되면 pass 총합은 여전히 117 이지만
    `O_in + O_out = 26 + s` 이므로
        `D_in + D_out = 5(26+s) - 117 = 13 + 5s`.
    즉 공유 궤도 하나당 결손 예산이 **5 늘어난다**.  그 예산으로 용량 합성곱이
    117 에 닿는지 본다.  닿으면 §7 의 모순은 사밀성 없이는 성립하지 않는다.
    """
    out = []
    for s in (0, 1):
        B = 13 + 5 * s
        best_m, arg_m = -1, None
        for d1 in range(0, B + 1):
            d2 = B - d1
            if d1 <= 13 and d2 <= 13:
                v = C0[d1] + C0[d2]
                if v > best_m:
                    best_m, arg_m = v, (d1, d2)
        best_r, arg_r = -1, None
        for d1, rv in R.items():
            d2 = B - d1
            if 0 <= d2 <= 13:
                if rv + C0[d2] > best_r:
                    best_r, arg_r = rv + C0[d2], (d1, d2)
        out.append(dict(shared_orbits=s, deficit_budget=B,
                        M_best=best_m, M_argmax=arg_m,
                        R_best=best_r, R_argmax=arg_r,
                        M_still_contradicts=(best_m < 117),
                        R_still_contradicts=(best_r < 117),
                        note=("d1,d2 <= 13 인 조합만 썼으므로 s=1 의 값은 "
                              "**하한**이다; 실제 최대는 더 클 수 있다.")))
    return dict(cases=out,
                verdict=("사밀성은 완전히 하중을 받는다: 공유 궤도가 단 하나만 있어도 "
                         "M 용량 합성곱이 117 을 넘으므로 §7 의 모순이 사라진다."
                         if not out[1]["M_still_contradicts"] else
                         "공유 궤도 하나로는 모순이 살아남는다."))


if __name__ == "__main__":
    C0 = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83]
    R = {0: 20, 2: 8, 6: 24, 8: 22, 9: 21, 10: 40, 11: 39, 12: 48, 13: 47}
    res = dict(replay=replay(sys.argv[1] if len(sys.argv) > 1 else None),
               privacy_sensitivity=privacy_sensitivity(C0, R))
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_r137_controls_audit_138.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
