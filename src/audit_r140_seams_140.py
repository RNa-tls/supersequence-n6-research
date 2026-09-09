#!/usr/bin/env python3
"""라운드 140 감사 — 유일한 등호 경우(52 개 이음매)의 독립 검증.

세 등호 봉투는 전부 같은 시험으로 환원된다:
    `K=4, c=3, H=1, heavy=[4], m=2, b=0, Dsum=12, P_req=108`, `(k,s)=(1,2),(2,1),(3,0)`.
보통 사슬 두 개, 총 결손 12, 필요 pass 108, weight-4 이음매 하나.

확인할 것:
  (1) `max_d [C0(d)+C0(12-d)] = 108` 이고 `d = 4, 8` 에서만 달성 (**열거 완전성**);
  (2) 극값 사슬 집합: 결손 4 에서 46 pass 짜리, 결손 8 에서 62 pass 짜리를 전수 열거;
  (3) 두 방향 × 모든 극값 쌍 × 합법 weight-4 꼬리 13 개 = 이음매 총수;
  (4) 전부 **육각형 충돌**로 죽는가 (궤도 공유는 기각 사유가 아니다).
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
EXIT = [IDX[_s5(w)] for w in range(720)]


def legal(a, b, m):
    cat = list(P6[a]) + list(P6[b])[6 - m:]
    return all(len(set(cat[i:i + 6])) != 6 for i in range(1, m))


W4_TAILS = [t for t in permutations(range(4))
            if legal(0, IDX[(P6[0][4], P6[0][5]) + tuple(P6[0][i] for i in t)], 4)]


def w4_targets(y):
    q = P6[y]
    return [IDX[(q[4], q[5]) + tuple(q[i] for i in t)] for t in W4_TAILS]


def extremal(dmax, want, v=0):
    """`b=0` 보통 경량 사슬: 정확 결손 `d` 에서 pass 수가 `want[d]` 인 것 전부."""
    found = {d: [] for d in want}
    best = {}
    nodes = [0]
    usedhex = {HEX[v]}
    omask = {ORB[v]: 1 << OPH[v]}
    seq = [v]

    def cd(cur):
        return sum(5 - bin(m).count("1") for q, m in omask.items() if q != cur)

    def rec(cur, corb, passes):
        nodes[0] += 1
        d = cd(None)
        if d <= dmax:
            if passes > best.get(d, -1):
                best[d] = passes
            if d in want and passes == want[d]:
                found[d].append(tuple(seq))
        if cd(corb) > dmax:
            return
        nxt = TAU[cur]
        if ORB[nxt] == corb and not (omask[corb] >> OPH[nxt] & 1) \
                and HEX[nxt] not in usedhex:
            omask[corb] |= 1 << OPH[nxt]
            usedhex.add(HEX[nxt]); seq.append(nxt)
            rec(nxt, corb, passes + 1)
            seq.pop(); usedhex.discard(HEX[nxt])
            omask[corb] &= ~(1 << OPH[nxt])
        for w in (W3C[cur], W3B[cur]):
            if HEX[w] in usedhex or ORB[w] in omask:
                continue
            omask[ORB[w]] = 1 << OPH[w]
            usedhex.add(HEX[w]); seq.append(w)
            rec(w, ORB[w], passes + 1)
            seq.pop(); usedhex.discard(HEX[w])
            del omask[ORB[w]]

    t0 = time.time()
    rec(v, ORB[v], 1)
    return dict(nodes=nodes[0], seconds=round(time.time() - t0, 1),
                best={d: best.get(d) for d in range(dmax + 1)},
                chains={d: found[d] for d in want},
                counts={d: len(found[d]) for d in want})


def rename_to(chain, first):
    src, dst = P6[chain[0]], P6[first]
    rho = {src[i]: dst[i] for i in range(6)}
    return tuple(IDX[tuple(rho[c] for c in P6[w])] for w in chain)


def run():
    ex = extremal(12, {})
    mx = {d: ex["best"][d] for d in range(13)}
    conv = sorted(((mx[a] + mx[12 - a], a, 12 - a) for a in range(13)
                   if mx[a] and mx[12 - a]), reverse=True)
    top = conv[0][0]
    argmax = [(a, b) for v, a, b in conv if v == top]
    ex2 = extremal(8, {4: mx[4], 8: mx[8]})
    c4, c8 = ex2["chains"][4], ex2["chains"][8]
    seams, survivors, collide = 0, [], 0
    orb_shared_but_hex_ok = 0
    for order, (A, B) in (("d4->d8", (c4, c8)), ("d8->d4", (c8, c4))):
        for a in A:
            for b in B:
                y = EXIT[a[-1]]
                hexA = {HEX[w] for w in a}
                orbA = {ORB[w] for w in a}
                for t in w4_targets(y):
                    B2 = rename_to(b, t)
                    seams += 1
                    clash = hexA & {HEX[w] for w in B2}
                    if clash:
                        collide += 1
                        if orbA & {ORB[w] for w in B2}:
                            orb_shared_but_hex_ok += 1
                    else:
                        survivors.append(dict(order=order, target=t))
    return dict(
        exact_deficit_maxima={d: mx[d] for d in range(13)},
        search_nodes=ex["nodes"],
        convolution_max=top, convolution_argmax=argmax,
        astra_claims_108_at_4_and_8=(top == 108 and sorted(argmax) == [(4, 8), (8, 4)]),
        maxima_46_and_62=(mx[4] == 46 and mx[8] == 62),
        extremal_counts={4: len(c4), 8: len(c8)},
        astra_claims_1_and_2=(len(c4) == 1 and len(c8) == 2),
        total_seams=seams, astra_claims_52=(seams == 52),
        hexagon_collisions=collide,
        seams_with_shared_orbit_also_hex_colliding=orb_shared_but_hex_ok,
        survivors=survivors, survivor_count=len(survivors),
        all_52_collide_in_hexagons=(len(survivors) == 0),
        w4_legal_tails=len(W4_TAILS))


if __name__ == "__main__":
    r = run()
    (ROOT / "outputs" / "rr_r140_seams_140.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
