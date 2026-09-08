#!/usr/bin/env python3
"""라운드 139 감사 — 등호 이음매 E2 / E3 의 독립 검증.

두 등호 봉투가 라운드 139 폐쇄의 유일한 비-엄격 지점이다:

* **E2**: 보통 사슬 두 개, 총 결손 13, 필요 pass 112, weight-4 이음매 하나.
  유일한 최대 분할은 결손 4/9 에서 46/66 (양쪽 순서).
* **E3**: 보통 사슬 세 개, 총 결손 8, 필요 pass 112, weight-4 이음매 둘.
  최대 분할은 (20,46,46)@(0,4,4) 와 (33,33,46)@(2,2,4) 의 순열.

Astra 는 두 경우 모두 **실제 육각형 충돌**로 죽는다고 주장한다.  여기서는
극값 사슬 집합을 우리가 직접 열거하고, 이음매를 우리가 직접 만들어 확인한다.

값-재명명 정규화(사슬의 첫 진입을 `012345` 로) 는 라운드 138 감사에서 720 개
재명명이 전부 사슬 모형의 자기동형이고 단어 위에 추이적임을 전수 확인해 두었다.
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
EXIT = [IDX[_s5(w)] for w in range(720)]          # full pass 의 마지막 창


def legal(a, b, m):
    cat = list(P6[a]) + list(P6[b])[6 - m:]
    return all(len(set(cat[i:i + 6])) != 6 for i in range(1, m))


W4_TAILS = [t for t in permutations(range(4))
            if legal(0, IDX[(P6[0][4], P6[0][5]) + tuple(P6[0][i] for i in t)], 4)]


def w4_targets(y):
    """끝 창 `y` 에서 나가는 **합법** weight-4 표적 13 개."""
    q = P6[y]
    return [IDX[(q[4], q[5]) + tuple(q[i] for i in t)] for t in W4_TAILS]


def extremal_chains(dmax, want, v=0, node_cap=None):
    """`b = 0` 보통 경량 사슬 중 **정확 결손 d** 에서 pass 수가 `want[d]` 인 것 전부."""
    found = {d: [] for d in want}
    best = {}
    nodes = [0]
    capped = [False]
    usedhex = {HEX[v]}
    omask = {ORB[v]: 1 << OPH[v]}
    seq = [v]

    def closed_deficit(cur):
        return sum(5 - bin(m).count("1") for q, m in omask.items() if q != cur)

    def rec(cur, corb, passes):
        nodes[0] += 1
        if node_cap and nodes[0] > node_cap:
            capped[0] = True
            return
        d = closed_deficit(None)
        if d <= dmax:
            if passes > best.get(d, -1):
                best[d] = passes
            if d in want and passes == want[d]:
                found[d].append(tuple(seq))
        if closed_deficit(corb) > dmax:
            return
        nxt = TAU[cur]
        if ORB[nxt] == corb and not (omask[corb] >> OPH[nxt] & 1) \
                and HEX[nxt] not in usedhex:
            omask[corb] |= 1 << OPH[nxt]
            usedhex.add(HEX[nxt])
            seq.append(nxt)
            rec(nxt, corb, passes + 1)
            seq.pop()
            usedhex.discard(HEX[nxt])
            omask[corb] &= ~(1 << OPH[nxt])
        for w in (W3C[cur], W3B[cur]):
            if HEX[w] in usedhex or ORB[w] in omask:
                continue
            omask[ORB[w]] = 1 << OPH[w]
            usedhex.add(HEX[w])
            seq.append(w)
            rec(w, ORB[w], passes + 1)
            seq.pop()
            usedhex.discard(HEX[w])
            del omask[ORB[w]]

    t0 = time.time()
    rec(v, ORB[v], 1)
    return dict(nodes=nodes[0], capped=capped[0], seconds=round(time.time() - t0, 1),
                best={d: best.get(d) for d in range(dmax + 1)},
                chains={d: found[d] for d in want},
                counts={d: len(found[d]) for d in want})


def rename_to(chain, first):
    """사슬을 값-재명명해서 첫 진입이 `first` 가 되게 한다 (유일한 재명명)."""
    src, dst = P6[chain[0]], P6[first]
    rho = {src[i]: dst[i] for i in range(6)}
    return tuple(IDX[tuple(rho[c] for c in P6[w])] for w in chain)


def seam_test(chainA, chainB):
    """A 의 끝에서 weight-4 로 B 로 넘어가는 13 개 이음매를 전부 시험."""
    y = EXIT[chainA[-1]]
    hexA = {HEX[w] for w in chainA}
    res = []
    for t in w4_targets(y):
        B2 = rename_to(chainB, t)
        hexB = {HEX[w] for w in B2}
        clash = hexA & hexB
        orbA = {ORB[w] for w in chainA}
        orbB = {ORB[w] for w in B2}
        res.append(dict(target=t, hex_collision=bool(clash),
                        n_hex_shared=len(clash),
                        orbit_shared=len(orbA & orbB),
                        survives=not clash))
    return res


def E2():
    """두 사슬, 결손 4 + 9, pass 46 + 66 = 112, w4 이음매 하나."""
    ex = extremal_chains(9, {4: 46, 9: 66})
    c4, c9 = ex["chains"][4], ex["chains"][9]
    seams, survivors = 0, []
    for order, (A, B) in (("d4->d9", (c4, c9)), ("d9->d4", (c9, c4))):
        for a in A:
            for b in B:
                for r in seam_test(a, b):
                    seams += 1
                    if r["survives"]:
                        survivors.append(dict(order=order, target=r["target"]))
    return dict(search_nodes=ex["nodes"], capped=ex["capped"],
                max_at_deficit4=ex["best"][4], max_at_deficit9=ex["best"][9],
                extremal_count_d4=len(c4), extremal_count_d9=len(c9),
                astra_claims_1_and_12=(len(c4) == 1 and len(c9) == 12),
                passes_46_plus_66=(46 + 66 == 112),
                total_seams=seams, astra_claims_312=(seams == 312),
                survivors=survivors[:5], survivor_count=len(survivors),
                all_collide_in_hexagons=(len(survivors) == 0))


def E3():
    """세 사슬, 총 결손 8, pass 112, w4 이음매 둘."""
    ex = extremal_chains(4, {0: 20, 2: 33, 4: 46})
    ch = {d: ex["chains"][d] for d in (0, 2, 4)}
    splits = []
    for trip in set(permutations((0, 4, 4))) | set(permutations((2, 2, 4))):
        if sum(trip) != 8:
            continue
        tot = sum({0: 20, 2: 33, 4: 46}[d] for d in trip)
        if tot == 112:
            splits.append(trip)
    first_total, first_surv = 0, []
    for trip in splits:
        for a in ch[trip[0]]:
            for b in ch[trip[1]]:
                for r in seam_test(a, b):
                    first_total += 1
                    if r["survives"]:
                        first_surv.append((trip, a, rename_to(b, r["target"])))
    second_total, second_surv = 0, []
    for trip, a, b2 in first_surv:
        merged = tuple(a) + tuple(b2)
        for c in ch[trip[2]]:
            y = EXIT[merged[-1]]
            hexM = {HEX[w] for w in merged}
            for t in w4_targets(y):
                C2 = rename_to(c, t)
                second_total += 1
                if not (hexM & {HEX[w] for w in C2}):
                    second_surv.append((trip, t))
    return dict(search_nodes=ex["nodes"], capped=ex["capped"],
                extremal_counts={d: len(ch[d]) for d in (0, 2, 4)},
                maxima={d: ex["best"][d] for d in (0, 2, 4)},
                splits=[list(s) for s in sorted(splits)],
                split_totals={str(list(s)): sum({0: 20, 2: 33, 4: 46}[d] for d in s)
                              for s in sorted(splits)},
                first_seams=first_total, first_survivors=len(first_surv),
                astra_claims_78_and_8=(first_total == 78 and len(first_surv) == 8),
                second_seams=second_total, second_survivors=len(second_surv),
                astra_claims_104=(second_total == 104),
                all_second_collide=(len(second_surv) == 0),
                E3_eliminated=(len(second_surv) == 0))


if __name__ == "__main__":
    r = dict(w4_legal_tails_per_window=len(W4_TAILS), E2=E2(), E3=E3())
    (ROOT / "outputs" / "rr_r139_seams_audit_139.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str)[:3500])
