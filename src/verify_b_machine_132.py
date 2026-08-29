#!/usr/bin/env python3
"""라운드 132 §23 — 새 유형-B 규칙의 **양성 대조**.

라운드 132 가 더한 것은 셋이다:
* **정리 132.1 가지치기** — 뒤 opener 의 lock 목표가 알려진 반복 궤도와 같으면 **공집합**;
* **구조 모형 분기** `LOCK0MODE ∈ {0, 1, 3}` — D-β₀ / D-α / 모형 T 가 **망라적**;
* **order pin** `ORDPIN ∈ {1, 2}` — α 사슬과 β 둥지의 위치 등식.

세 규칙을 파이썬으로 재구현해 합법 `n = 4` walk 중 유형 B·`G = 2`·등호 `f_out = F + e`
인 것 전부에 적용한다.  **거짓 기각 0** 이어야 한다 (모형 분기는 세 값 중 **적어도 하나**가
받아들이면 통과 — 망라성 검사이다).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup, legal_joint          # noqa: E402
from verify_fg_repair_128 import walk_measure                   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def _structure(g, m):
    """walk 에서 유형-B 구조를 읽는다.  유형 B 가 아니면 None."""
    n = g["n"]
    perms, idx, ta, orbid, orbph = g["perms"], g["idx"], g["tau"], g["orbid"], g["orbph"]
    passes, hexes, nu = m["passes"], m["hexes"], m["nu"]
    P = len(passes)
    cnt = Counter(hexes)
    multi = [h for h in dict.fromkeys(hexes) if cnt[h] >= 2]
    if not (len(multi) == 2 and all(cnt[h] == 2 for h in multi)):
        return None
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
    free = [idx[ta(perms[passes[nu[i]][0]])] == passes[i + 1][0] for i in range(P - 1)]
    free.append(False)
    return dict(o0=o0, c0=c0, o1=o1, c1=c1, P=P, orbs=orbs, runof=runof, free=free,
                Q0=orbid[passes[o0][0]], Q1=orbid[passes[o1][0]],
                T0=orbid[passes[c0][0]], T1=orbid[passes[c1][0]],
                lock0=(runof[c0] == runof[o0 + 1]) if o0 + 1 < P else False,
                lock1=(runof[c1] == runof[o1 + 1]) if o1 + 1 < P else False,
                n=n)


def accepts(st, lock0mode, ordpin):
    """엔진의 라운드-132 새 규칙만 재생한다 (라운드 131 규칙은 이미 대조를 통과했다)."""
    n = st["n"]
    d = n - 1
    # --- 정리 132.1 가지치기: 뒤 opener 의 lock 이 깨지면 엔진이 잘라낸다 ------------
    if not st["lock1"]:
        return False, "132.1 prune would cut a walk whose opener_1 lock breaks"
    # --- 구조 모형 -------------------------------------------------------------
    if lock0mode == 0:
        if st["lock0"]:
            return False, "beta branch but opener_0's lock holds"
        if st["T0"] != st["Q1"]:
            return False, "beta requires T_0 = Q_1"
    elif lock0mode == 1:
        if not st["lock0"]:
            return False, "D-alpha branch but opener_0's lock breaks"
        if st["Q1"] == st["Q0"]:
            return False, "D-alpha forbids Q_1 = Q_0"
    elif lock0mode == 3:
        if not st["lock0"]:
            return False, "Model T branch but opener_0's lock breaks"
        if st["Q1"] != st["Q0"]:
            return False, "Model T requires Q_1 = Q_0"
    elif lock0mode == 4:
        if not st["lock0"]:
            return False, "plain-alpha branch but opener_0's lock breaks"
    elif lock0mode == 2:
        pass                       # auto: no structural condition (Round-131 semantics)
    # --- order pin --------------------------------------------------------------
    if ordpin == 1:
        if st["c0"] != st["o0"] + d or st["c1"] != st["o1"] + d:
            return False, "alpha chain closer = opener + (n-1)"
        if st["o1"] <= st["o0"] + d:
            return False, "alpha chain opener_1 > closer_0"
    elif ordpin == 2:
        u = st["o1"] - st["o0"]
        if not (1 <= u <= d - 1):
            return False, "beta nest u out of range"
        if st["c1"] != st["o1"] + d or st["c0"] != st["o0"] + 2 * d:
            return False, "beta nest distances"
    return True, None


def n4_control(maxlen=39):
    n = 4
    g = setup(n)
    perms, sg, om = g["perms"], g["sig"], g["omega"]
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
    rejects = []
    for L, seq in ws:
        m = walk_measure(g, W, seq, L)
        if m["G"] != 2 or m["f_out"] != m["F"] + m["e"]:
            continue
        st = _structure(g, m)
        if st is None:
            continue
        stat["typeB_equality"] += 1
        strict = (m["x"] == 0)
        if strict:
            stat["typeB_equality_x0"] += 1
        # 모형 분기의 망라성: {0,1,3} 중 적어도 하나가 받아야 한다.
        ok_model = [lm for lm in (0, 1, 3) if accepts(st, lm, 0)[0]]
        if not ok_model:
            stat["REJECT_model"] += 1
            if len(rejects) < 5:
                rejects.append(dict(L=L, e=m["e"], x=m["x"], why=accepts(st, 1, 0)[1]))
        else:
            stat["accept_model"] += 1
            stat["model_" + "".join(str(v) for v in ok_model)] += 1
        # ---- 라운드 132 감사 정정: 모형 T 의 **정확한** census -------------------
        # `model_3` (= Q0 = Q1 이고 두 lock 이 성립) 은 `e` 를 섞어 센 표본이다.
        # `B/e=2` 의 **진짜 세-run 모형 T** 는 공유 궤도가 실제로 run 셋을 가질 때뿐이다.
        if st["Q0"] == st["Q1"] and st["lock0"] and st["lock1"]:
            stat["T_sample_total"] += 1
            stat[f"T_sample_e{m['e']}"] += 1
            if m["e"] == 2:
                orbs, P = st["orbs"], st["P"]
                runs, cur = [], [0]
                for i in range(1, P):
                    if orbs[i] == orbs[i - 1]:
                        cur.append(i)
                    else:
                        runs.append(cur)
                        cur = [i]
                runs.append(cur)
                k = sum(1 for r in runs if orbs[r[0]] == st["Q0"])
                if k == 3:
                    stat["T_e2_three_run"] += 1
                    if m["x"] == 0:
                        stat["T_e2_three_run_x0"] += 1
        # ---- 드라이버가 **실제로** 쓰는 갈래 집합의 망라성 -----------------------
        # B/e=1, 자유 closer = closer_0 : {mode 2}
        # B/e=1, 자유 closer = closer_1 : {mode 4, mode 0}
        # B/e=2                          : {mode 3, mode 1, mode 0}
        free_c0 = st["free"][st["c0"]]
        if m["e"] == 1:
            branches = [2] if free_c0 else [4, 0]
        elif m["e"] == 2:
            branches = [3, 1, 0]
        else:
            branches = [2]
        cov = [lm for lm in branches if accepts(st, lm, 0)[0]]
        stat["driver_covered" if cov else "REJECT_driver"] += 1
        if not cov and len(rejects) < 8:
            rejects.append(dict(L=L, e=m["e"], x=m["x"], branches=branches,
                                why=accepts(st, branches[0], 0)[1]))
        # order pin 은 `x = 0` 에서만 주장된다 (run 이 τ-사슬이어야 5 pass 가 강제된다).
        if strict:
            lm = ok_model[0] if ok_model else 1
            pin = 2 if lm == 0 else 1
            ok, why = accepts(st, lm, pin)
            if ok:
                stat["accept_ordpin"] += 1
            else:
                stat["REJECT_ordpin"] += 1
                if len(rejects) < 8:
                    rejects.append(dict(L=L, e=m["e"], x=m["x"], ordpin=pin, why=why))
    return dict(
        n=4, typeB_equality=stat["typeB_equality"],
        typeB_equality_x0=stat["typeB_equality_x0"],
        accepted_model=stat["accept_model"], rejected_model=stat["REJECT_model"],
        accepted_ordpin=stat["accept_ordpin"], rejected_ordpin=stat["REJECT_ordpin"],
        driver_covered=stat["driver_covered"], driver_rejected=stat["REJECT_driver"],
        false_rejection=(stat["REJECT_model"] + stat["REJECT_ordpin"]
                         + stat["REJECT_driver"]),
        model_breakdown={k: v for k, v in sorted(stat.items()) if k.startswith("model_")},
        model_T_census=dict(
            Q0_eq_Q1_samples_total=stat["T_sample_total"],
            by_e={f"e{i}": stat[f"T_sample_e{i}"] for i in (0, 1, 2)},
            be2_genuine_three_run_witnesses=stat["T_e2_three_run"],
            be2_three_run_with_x0=stat["T_e2_three_run_x0"],
            caveat=("the 72 figure is the Q0 = Q1 SAMPLE across all e, not the B/e=2 "
                    "Model-T witness count, which is 11.  The absence of x = 0 among "
                    "those 11 is an n = 4 size artefact and is NOT an impossibility "
                    "theorem for n = 6 - it must never be used as one.")),
        reject_examples=rejects,
        clean=(stat["REJECT_model"] == 0 and stat["REJECT_ordpin"] == 0
               and stat["REJECT_driver"] == 0),
        note=("the model branch {D-beta0, D-alpha, Model T} must be EXHAUSTIVE over every "
              "type-B equality walk; ORDPIN is asserted only for x = 0, which is exact in "
              "the (4,2) cell"))


if __name__ == "__main__":
    d = n4_control()
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_b_machine_132.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(d, ensure_ascii=False, indent=1))
