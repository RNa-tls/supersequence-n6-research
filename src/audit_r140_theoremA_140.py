#!/usr/bin/env python3
"""라운드 140 감사 — 보편 자유-이탈 정리 `f_out <= F + e` 의 독립 검증.

Astra 의 코드는 하나도 import 하지 않는다.  n=4 정규화 NR4 영역을 내가 직접
생성하고, 각 단어를 문자열에서 다시 파싱해 `P, G, F, J, e, x, S, H, f_out, delta`
를 계산한 뒤 정리를 시험한다.

정리 (보고서 §2):
    `nu` 를 `v_nu(i) = sigma^(l_i)(v_i)` 로 정의한다.  `nu` 는 full pass 를 고정하고
    갈라진 육각형마다 길이 `m_h` 순환 하나를 갖는다.  시간순 오름 `i < nu(i)` 이
    곧 abandonment 이고 `F = #오름`.
    weight-2 조인트에서 문자 출처 `p' = sigma^(l_i-1)(v_i)` 의 표적은
        `target = E(sigma(p')) = E(v_nu(i))`                     (2.1)
    이므로 표적 궤도는 `orb(v_nu(i))` 다.
      * full pass (`nu(i)=i`) 면 표적은 같은 궤도 -> run 내부, `U` 에 없다;
      * 짧은 pass 의 내림 (`nu(i)<i`) 이면 표적 궤도는 pass `nu(i)` 에서 이미
        열렸으므로 진입 `i+1` 은 **반복 run 개시**다.
    `A` = 오름 집합, `U` = 자유 run 간 이탈, `Rpt` = 반복 run 개시 사건.
    `Ord = {i+1 : i in U, nu(i)<i} subset Rpt`,  `a = |A\\U|`,  `eta = |Rpt\\Ord|`.
    오름 자유이탈 = `F-a`, 내림 자유이탈 = `e-eta`, 따라서
        `delta := F + e - f_out = a + eta >= 0`.                 (2.2)
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(n):
    P = list(permutations(range(n)))
    IDX = {p: i for i, p in enumerate(P)}
    N = len(P)

    def sig(p):
        return p[1:] + p[:1]

    def tau(p):                       # E: 앞 n-1 자리 회전, 마지막 고정
        return p[1:n - 1] + p[:1] + p[n - 1:]

    SIG = [IDX[sig(p)] for p in P]
    TAU = [IDX[tau(p)] for p in P]
    # 육각형 = sigma-순환 (n 개), 궤도 = E-순환 (n-1 개)
    HEX = [-1] * N
    ORB = [-1] * N
    h = o = 0
    for i in range(N):
        if HEX[i] < 0:
            j = i
            for _ in range(n):
                HEX[j] = h
                j = SIG[j]
            h += 1
        if ORB[i] < 0:
            j = i
            for _ in range(n - 1):
                ORB[j] = o
                j = TAU[j]
            o += 1
    OM = [[0] * N for _ in range(N)]
    LEGAL = [[False] * N for _ in range(N)]
    for a in range(N):
        for b in range(N):
            w = n
            for k in range(1, n):
                if P[a][k:] == P[b][:n - k]:
                    w = k
                    break
            OM[a][b] = w
            cat = list(P[a]) + list(P[b])[n - w:]
            LEGAL[a][b] = all(len(set(cat[i:i + n])) != n for i in range(1, w))
    return dict(n=n, P=P, IDX=IDX, N=N, SIG=SIG, TAU=TAU, HEX=HEX, ORB=ORB,
                OM=OM, LEGAL=LEGAL)


def nr4_words(g, maxlen=39, start=None):
    """모든 순열을 정확히 한 번 쓰는 정규화 NR4 단어 (최대 겹침 조인트)."""
    n, N, OM, LEGAL = g["n"], g["N"], g["OM"], g["LEGAL"]
    s0 = g["IDX"][tuple(range(n))] if start is None else start
    words = []
    nodes = [0]
    seq = [s0]
    used = [False] * N
    used[s0] = True

    def rec(cur, length):
        nodes[0] += 1
        if len(seq) == N:
            words.append(tuple(seq))
            return
        # 건전한 가지치기: 남은 순열 하나마다 최소 무게 1 이 더 붙는다.
        if length + (N - len(seq)) > maxlen:
            return
        for b in range(N):
            if used[b]:
                continue
            w = OM[cur][b]
            if length + w > maxlen or not LEGAL[cur][b]:
                continue
            used[b] = True
            seq.append(b)
            rec(b, length + w)
            seq.pop()
            used[b] = False

    t0 = time.time()
    rec(s0, n)
    return dict(words=words, count=len(words), nodes=nodes[0],
                seconds=round(time.time() - t0, 1), maxlen=maxlen)


def analyse(g, seq):
    """순열 열 -> 문자 단어의 자원/구조 전량."""
    n, OM, SIG, TAU, HEX, ORB = g["n"], g["OM"], g["SIG"], g["TAU"], g["HEX"], g["ORB"]
    ws = [OM[seq[i]][seq[i + 1]] for i in range(len(seq) - 1)]
    # pass = weight-1 조인트로 이어진 극대 묶음
    passes, cur = [], [seq[0]]
    for i, w in enumerate(ws):
        if w == 1:
            cur.append(seq[i + 1])
        else:
            passes.append(cur)
            cur = [seq[i + 1]]
    passes.append(cur)
    entry = [pp[0] for pp in passes]
    length = [len(pp) for pp in passes]
    Pn = len(passes)
    # 조인트 무게: pass 사이의 무게
    jw = []
    k = 0
    for i in range(Pn - 1):
        k += length[i] - 1
        jw.append(ws[k])
        k += 1
    S = sum(1 for w in jw if w >= 3)
    H = sum(w - 3 for w in jw if w > 3)
    # G = 다중도 초과 = P - (진입이 닿은 서로 다른 육각형 수) = sum_h (m_h - 1).
    # 완전 덮기 단어에서는 P - N/n 과 같지만, 국소 단어에도 옳다.
    Gm = Pn - len({HEX[e] for e in entry})
    pos_of = {e: i for i, e in enumerate(entry)}
    # nu
    nu = []
    for i in range(Pn):
        t = entry[i]
        for _ in range(length[i]):
            t = SIG[t]
        nu.append(pos_of.get(t))
    if any(v is None for v in nu):
        return None
    F = sum(1 for i in range(Pn) if i < nu[i])
    J = Gm - F
    # run = **같은 E-궤도에 있는 pass 진입의 극대 연속열** (보고서 §1).
    # 유료 궤도-내부 조인트(x-호)는 run 을 끊지 않는다 ("paid intra-run joints").
    runs = []
    curr = [0]
    for i in range(Pn - 1):
        if ORB[entry[i + 1]] == ORB[entry[i]]:
            curr.append(i + 1)
        else:
            runs.append(curr)
            curr = [i + 1]
    runs.append(curr)
    r = len(runs)
    O = len({ORB[e] for e in entry})
    e = r - O
    x = sum(1 for i in range(Pn - 1)
            if jw[i] >= 3 and ORB[entry[i + 1]] == ORB[entry[i]])
    f_out = sum(1 for i in range(Pn - 1)
                if jw[i] == 2 and ORB[entry[i + 1]] != ORB[entry[i]])
    # Rpt: 반복 run 개시 사건 (그 run 의 첫 pass 인덱스)
    seen = set()
    Rpt = []
    for rr in runs:
        q = ORB[entry[rr[0]]]
        if q in seen:
            Rpt.append(rr[0])
        seen.add(q)
    A = {i for i in range(Pn) if i < nu[i]}
    U = {i for i in range(Pn - 1)
         if jw[i] == 2 and ORB[entry[i + 1]] != ORB[entry[i]]}
    Ord = {i + 1 for i in U if nu[i] < i}
    a = len(A - U)
    eta = len(set(Rpt) - Ord)
    delta = F + e - f_out
    return dict(P=Pn, G=Gm, F=F, J=J, O=O, e=e, x=x, S=S, H=H, f_out=f_out,
                S_identity=(S == O + e - 1 - f_out + x),
                delta=delta, a=a, eta=eta, r=r, nu=nu,
                Ord_subset_Rpt=Ord.issubset(set(Rpt)),
                identity_2_2=(delta == a + eta),
                theoremA=(f_out <= F + e),
                theoremA_old=(f_out <= Gm + e + x),
                O_bound=(O <= 1 + S + F))


def identity_2_1(ns=(4, 5, 6)):
    """`(2.1)`: weight-2 조인트의 표적 = `E(sigma(p'))`.  전수 확인."""
    out, bad = {}, []
    for n in ns:
        g = build(n)
        N, P, IDX, OM, LEGAL, SIG, TAU = (g["N"], g["P"], g["IDX"], g["OM"],
                                          g["LEGAL"], g["SIG"], g["TAU"])
        cnt = 0
        for p in range(N):
            tgt = [b for b in range(N) if OM[p][b] == 2 and LEGAL[p][b]]
            cnt += 1
            if len(tgt) != 1 or tgt[0] != TAU[SIG[p]]:
                bad.append((n, p, tgt))
        out[n] = cnt
    return dict(per_n=out, total=sum(out.values()), failures=bad[:6],
                failure_count=len(bad), all_pass=(len(bad) == 0),
                statement="the unique legal weight-2 target of p' is E(sigma(p'))")


if __name__ == "__main__":
    g4 = build(4)
    res = dict(identity_2_1=identity_2_1())
    w = nr4_words(g4)
    hist = Counter()
    viol_A = []
    viol_id = []
    viol_O = []
    rows = []
    for seq in w["words"]:
        r = analyse(g4, seq)
        if r is None:
            continue
        hist[r["G"]] += 1
        if not r["theoremA"]:
            viol_A.append(dict(seq=list(seq), **{k: r[k] for k in
                               ("P","G","F","e","x","S","H","f_out","delta")}))
        if not r["identity_2_2"]:
            viol_id.append(seq)
        if not r["O_bound"]:
            viol_O.append(seq)
        rows.append(r)
    res["nr4"] = dict(count=w["count"], nodes=w["nodes"], seconds=w["seconds"],
                      maxlen=w["maxlen"],
                      astra_claims_29255=(w["count"] == 29255),
                      astra_nodes=49682345, my_nodes=w["nodes"],
                      G_histogram=dict(sorted(hist.items())),
                      astra_G_histogram=[827, 5999, 10625, 7545, 3384, 629, 246],
                      G_histogram_matches=([hist[i] for i in range(7)]
                                           == [827, 5999, 10625, 7545, 3384, 629, 246]),
                      theoremA_violations=len(viol_A),
                      theoremA_violation_witnesses=viol_A[:5],
                      S_identity_violations=sum(1 for r in rows
                                                if not r["S_identity"]),
                      Ord_subset_Rpt_violations=sum(1 for r in rows
                                                    if not r["Ord_subset_Rpt"]),
                      old_theorem_violations=sum(1 for r in rows
                                                 if not r["theoremA_old"]),
                      identity_2_2_violations=len(viol_id),
                      O_bound_violations=len(viol_O),
                      delta_ge_J_counterexamples=sum(
                          1 for r in rows if r["delta"] < r["J"]),
                      all_pass=(not viol_A and not viol_id and not viol_O))
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_r140_theoremA_140.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
