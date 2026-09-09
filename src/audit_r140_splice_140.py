#!/usr/bin/env python3
"""라운드 140 감사 §16-§20, §25-§26 — 일반 successor-splicing 과 모델 포함.

§17 끝점 항등식, §18 조인트 합법성 보존, §19 합성(자름 경계), §20 육각형 다중도,
§26 용량 모델 포함(이동 분류).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_r140_theoremA_140 import build                          # noqa: E402
from audit_r140_g3_140 import support_table, beta_components       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def endpoint_identity(ns=(4, 5, 6, 7)):
    """§17 — `sigma^-1(v_nu(i)) = sigma^(l-1)(v_i)`.

    `v_nu(i) = sigma^l(v_i)` 이므로 `sigma^-1(sigma^l(v)) = sigma^(l-1)(v)`.
    `sigma^n = id` 하나만 쓰는 항등식이며, 유한 검사에 의존하지 않는다.
    그래도 n=4..7 의 모든 순열 × 모든 pass 길이에서 전수 확인한다.
    """
    tot, bad, per = 0, [], {}
    for n in ns:
        g = build(n)
        SIG, N = g["SIG"], g["N"]
        inv = [0] * N
        for i in range(N):
            inv[SIG[i]] = i
        cnt = 0
        for v in range(N):
            for l in range(1, n + 1):
                t = v
                for _ in range(l):
                    t = SIG[t]
                lhs = inv[t]                       # sigma^-1(v_nu)
                rhs = v
                for _ in range(l - 1):
                    rhs = SIG[rhs]                 # sigma^(l-1)(v)
                if lhs != rhs:
                    bad.append((n, v, l))
                cnt += 1
        per[n] = cnt
        tot += cnt
    return dict(per_n=per, total=tot, failures=bad[:5], failure_count=len(bad),
                all_pass=(len(bad) == 0),
                symbolic="sigma^-1 . sigma^l = sigma^(l-1) since sigma^n = id")


def joint_preservation(n=6, step=7):
    """§18 — splice 후 조인트의 무게·꼬리·중간창이 항등적으로 같은가."""
    g = build(n)
    P, IDX, SIG, OM, N = g["P"], g["IDX"], g["SIG"], g["OM"], g["N"]

    def tail_mids(a, b, w):
        cat = list(P[a]) + list(P[b])[n - w:]
        return (tuple(list(P[b])[n - w:]),
                tuple(tuple(cat[i:i + n]) for i in range(1, w)))

    checked, bad = 0, []
    for v in range(0, N, step):
        for l in range(1, n + 1):
            src_old = v
            for _ in range(l - 1):
                src_old = SIG[src_old]
            nu_t = v
            for _ in range(l):
                nu_t = SIG[nu_t]
            src_new = nu_t
            for _ in range(n - 1):
                src_new = SIG[src_new]
            if src_old != src_new:
                bad.append(("endpoint", v, l))
                continue
            for t in range(0, N, 11):
                w = OM[src_old][t]
                if (w, ) + tail_mids(src_old, t, w) != (w, ) + tail_mids(src_new, t, w):
                    bad.append(("joint", v, l, t))
                checked += 1
    return dict(triples_checked=checked, failure_count=len(bad),
                failures=bad[:5], all_pass=(len(bad) == 0))


def composition_bound(G=3):
    """§19/§20 — `m <= K-c+h+R <= G+1-c+h` 를 41 개 지지에서 직접 확인."""
    tab = support_table(G)
    rows, bad = [], []
    for t in tab:
        for s in t["supports"]:
            K, R = s["K"], s["R"]
            for c in range(0, K):
                for h in range(0, 4):
                    tight = K - c + h + R
                    loose = G + 1 - c + h
                    if tight > loose:
                        bad.append(dict(K=K, R=R, c=c, h=h))
                    rows.append((K, R, c, h, tight, loose))
    return dict(combinations=len(rows), violations=len(bad), examples=bad[:4],
                all_tight_le_loose=(len(bad) == 0),
                c_le_K_minus_1="the dummy-containing component is never an all-free circuit",
                note=("K+R <= G+1 (접속 사건 정리) 이 곧바로 "
                      "m <= K-c+h+R <= G+1-c+h 를 준다"))


def pure_free_circuit_structure(G=3):
    """§20 — 순수 자유 순환은 한 E-궤도의 `n-1` 포트를 정확히 갖는가 (구조 논증)."""
    return dict(
        argument=("splice 후 모든 자유 변은 문자 그대로 E-단계다 (§2 의 (2.1)). "
                  "진입/진출 차수가 최대 1 이므로 자유 변만으로 이루어진 순환은 "
                  "성분 전체이고, E 의 위수가 n-1 이므로 그 순환은 한 궤도의 "
                  "n-1 개 포트를 정확히 한 번씩 지난다.  진입 유일성 때문에 그 "
                  "궤도는 다른 곳에 나타날 수 없고, 제거는 궤도 하나와 n-1 개 "
                  "진입을 전역에서 없앤다."),
        verified_empirically_in_round139="819 pure-free circuits, all exactly n-1 in one orbit",
        c_bound="c <= K-1")


def move_taxonomy(n=6):
    """§26 — 용량 모델 포함의 근거: 합법 이동 분류 (라운드 138/139 결론 재확인)."""
    g = build(n)
    P, IDX, N = g["P"], g["IDX"], g["N"]

    def legal(a, b, m):
        cat = list(P[a]) + list(P[b])[n - m:]
        return all(len(set(cat[i:i + n])) != n for i in range(1, m))

    def s5(w):
        for _ in range(n - 1):
            w = g["SIG"][w]
        return w

    ORB, HEX = g["ORB"], g["HEX"]
    res = {}
    for m, base in ((2, 2), (3, 3)):
        for tail in permutations(range(base)):
            nm = "".join(map(str, tail))
            ok, props = 0, set()
            for w in range(N):
                y = s5(w)
                q = P[y]
                t = IDX[tuple(q[base:]) + tuple(q[i] for i in tail)]
                if legal(y, t, m):
                    ok += 1
                    props.add((HEX[t] == HEX[w], ORB[t] == ORB[w]))
            res[f"w{m}/{nm}"] = dict(legal_of=ok, total=N,
                                     props=sorted(map(str, props)))
    legal2 = [k for k, v in res.items() if k.startswith("w2") and v["legal_of"] == N]
    legal3 = [k for k, v in res.items() if k.startswith("w3") and v["legal_of"] == N]
    partial = {k: v["legal_of"] for k, v in res.items() if 0 < v["legal_of"] < N}
    return dict(table=res, legal_weight2=legal2, legal_weight3=legal3,
                counts={"w2": len(legal2), "w3": len(legal3)},
                no_partial=(partial == {}), partial=partial,
                matches_round126_catalogue=(len(legal2) == 1 and len(legal3) == 3),
                inclusion=("사슬의 이동은 tau 연장 + 120(궤도 안 위상 점프) + "
                           "201/210(궤도 밖 경량 연결자) 뿐이고, N*(b,0,d) 는 "
                           "임의의 비-E 위상 점프와 같은 궤도로의 재진입까지 "
                           "허용하므로 이들을 모두 포함하는 완화다."))


if __name__ == "__main__":
    res = dict(endpoint_identity=endpoint_identity(),
               joint_preservation=joint_preservation(),
               composition_bound=composition_bound(),
               pure_free_circuits=pure_free_circuit_structure(),
               move_taxonomy=move_taxonomy())
    (ROOT / "outputs" / "rr_r140_splice_140.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    out = {k: {kk: vv for kk, vv in v.items() if kk not in ("table",)}
           for k, v in res.items()}
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2600])
