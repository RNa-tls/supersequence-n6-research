#!/usr/bin/env python3
"""라운드 140 감사 — Astra 가 스스로 **반증**했다고 밝힌 주장들의 독립 확인,
그리고 splice/공유-궤도 회계 항등식의 대수적 검증.

Astra §3 은 두 개의 그럴듯한 강화를 문자 단어로 반증한다.  감사자로서 그
반증이 실제로 성립하는지(=Astra 가 한계를 정직하게 기록했는지) 확인한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_r140_theoremA_140 import build, analyse                # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def from_string(word, n=4):
    """문자 단어 -> 순열 인덱스 열 (등록된 창들)."""
    g = build(n)
    pos = [i for i in range(len(word) - n + 1)
           if len(set(word[i:i + n])) == n]
    seq = [g["IDX"][tuple(int(c) for c in word[i:i + n])] for i in pos]
    return g, seq, pos


def check_word(word, n=4):
    g, seq, pos = from_string(word, n)
    if len(set(seq)) != len(seq):
        return dict(word=word, ok=False, why="repeats a permutation")
    r = analyse(g, seq)
    if r is None:
        return dict(word=word, ok=False, why="nu target not registered")
    r["word"] = word
    r["ok"] = True
    r["n_windows"] = len(pos)
    r["contiguous"] = (pos == list(range(pos[0], pos[0] + len(pos)))) if False else None
    return r


def astra_refutations():
    """§3 의 두 반증을 문자 그대로 재현."""
    out = {}
    w1 = "012301202130210312032102031023103201320"
    r1 = check_word(w1)
    out["delta_ge_J_refutation"] = dict(
        word=w1, computed={k: r1.get(k) for k in
                           ("G", "F", "J", "e", "x", "S", "H", "delta", "f_out")},
        astra_claim=dict(G=3, F=2, J=1, e=2, x=1, S=2, H=2, delta=0, f_out=4),
        matches=all(r1.get(k) == v for k, v in
                    dict(G=3, F=2, J=1, e=2, x=1, S=2, H=2,
                         delta=0, f_out=4).items()),
        delta_lt_J=(r1.get("delta", 9) < r1.get("J", -9)),
        theoremA_still_holds=r1.get("theoremA"),
        note="delta >= J 는 실제 문자 단어로 반증된다; 정리 A 자체는 성립")
    w2 = "012302313203120321032013231023012130213"
    r2 = check_word(w2)
    out["delta_ge_q_plus_s_word"] = dict(
        word=w2, computed={k: r2.get(k) for k in
                           ("G", "F", "J", "e", "x", "S", "H", "delta", "f_out")},
        astra_delta_claim=3, delta_matches=(r2.get("delta") == 3),
        theoremA_still_holds=r2.get("theoremA"))
    w3 = "0123012013201"
    r3 = check_word(w3)
    out["arbitrary_paid_cut_word"] = dict(
        word=w3, computed={k: r3.get(k) for k in
                           ("P", "G", "F", "O", "e", "x", "S", "delta", "f_out")},
        astra_claim="two passes in one orbit, e=0 and x=1",
        e_is_0=(r3.get("e") == 0), x_is_1=(r3.get("x") == 1),
        theoremA_still_holds=r3.get("theoremA"),
        note=("임의 유료 자름에서는 r-1 반복 run 사건이 존재하지 않을 수 있으므로 "
              "run-존중 사밀 보조정리 대신 자유-블록 항등식(§6)을 써야 한다"))
    return out


def master_algebra(G=3):
    """§6 의 항등식들을 기호적으로 검증."""
    bad = []
    checks = 0
    for k in range(0, 6):
        O = 24 + k
        for c in range(0, 5):
            Pp = 120 + G - 5 * c
            Op = O - c
            for s in range(0, 5):
                # sum D_j = 5*(O'+s) - P' = 5k - G + 5s
                lhs = 5 * (Op + s) - Pp
                if lhs != 5 * k - G + 5 * s:
                    bad.append(("D_sum", k, c, s))
                checks += 1
            for S in range(0, 40):
                for H in range(0, 4):
                    # sum b_j + s = S+1-O+c ;  L = 844+G+S+H <= 871
                    rhs = S + 1 - O + c
                    if 844 + G + S + H <= 871 and rhs > 4 - G - k + c - H:
                        bad.append(("budget", k, c, S, H))
                    checks += 1
    # sum b_j + s = delta - F + x + c  via  S = O+e-1-f_out+x  and delta = F+e-f_out
    bad2 = []
    for O in range(20, 30):
        for e in range(0, 6):
            for f_out in range(0, 8):
                for x in range(0, 4):
                    for F in range(0, 5):
                        for c in range(0, 4):
                            S = O + e - 1 - f_out + x
                            delta = F + e - f_out
                            if S + 1 - O + c != delta - F + x + c:
                                bad2.append((O, e, f_out, x, F, c))
    return dict(checks=checks, violations=len(bad), examples=bad[:4],
                identity_chain_violations=len(bad2),
                identities=["sum D_j = 5k - G + 5s",
                            "sum P_j = 120 + G - 5c",
                            "sum b_j + s = S+1-O+c = delta-F+x+c",
                            "L<=871  =>  sum b_j + s <= 4-G-k+c-H"],
                all_hold=(len(bad) == 0 and len(bad2) == 0))


def sharing_multiplicity(max_pieces=5):
    """§22 — 궤도가 3 개 이상의 조각에 나타나는 경우의 기여를 직접 확인.

    `s = sum_Q (그 궤도를 담은 조각 수 - 1)`.  궤도 Q 가 `t` 개 조각에 나타나면
    `s` 에 `t-1` 을 기여하고, `sum_j O_j` 에는 `t` 를, 따라서 `sum D_j` 에는
    `5(t-1)` 을 더한다.  세 조각 이상도 특별 취급이 필요 없다.
    """
    rows = []
    for t in range(1, max_pieces + 1):
        contrib_s = t - 1
        contrib_sumO = t
        contrib_sumD = 5 * (t - 1)
        rows.append(dict(pieces_containing_orbit=t, contributes_to_s=contrib_s,
                         contributes_to_sum_O=contrib_sumO,
                         contributes_to_sum_D=contrib_sumD,
                         linear_in_t=(contrib_sumD == 5 * contrib_s)))
    return dict(rows=rows, all_linear=all(r["linear_in_t"] for r in rows),
                note=("t 개 조각에 걸친 궤도는 s 에 t-1, sum D_j 에 5(t-1) 을 "
                      "기여한다. t>=3 도 같은 선형식이므로 3 개 이상 공유가 "
                      "따로 예외가 되지 않는다."))


if __name__ == "__main__":
    res = dict(astra_refutations=astra_refutations(),
               master_algebra=master_algebra(),
               sharing_multiplicity=sharing_multiplicity())
    (ROOT / "outputs" / "rr_r140_claims_140.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1)[:3000])
