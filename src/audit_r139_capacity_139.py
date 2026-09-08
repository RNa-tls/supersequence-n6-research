#!/usr/bin/env python3
"""라운드 139 감사 — `N*(b, 0, d)` 사슬 용량의 독립 재구현.

라운드 115 모형(라운드 138 감사에서 `b=0` 으로 재현해 둔 것)에 **b 토큰**을 더한다.

모형 (R115, 완화):
  * pass 는 전부 full, 육각형 중복 없음, 궤도 재사용 없음 (`g = 0`);
  * run 안에서의 연장은 그 궤도의 **아직 쓰지 않은 아무 위상**으로 갈 수 있고,
    위상이 `+1` 이면 무료, 아니면 **토큰 1 개**를 쓴다 (`b` = 지역 `e + x`);
  * run 사이는 경량 연결자 `W3b`/`W3c` (= 201/210); 새 궤도는 무료, **이미 등록된
    궤도로 되돌아가는 것은 토큰 1 개** (사슬 안의 여분 run) — `b` 의 주된 쓰임;
  * 결손 `d` = 닫힌 궤도들의 `5 - (그 궤도 pass 수)` 합.

`b = 0` 이면 라운드 138 감사에서 확인한 `C0` 표를 그대로 준다 (양성 통제).
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
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

# 궤도별 위상 -> 단어
ORB_AT = {}
for w in range(720):
    ORB_AT[(ORB[w], OPH[w])] = w


def chain_capacity(b=0, g=0, dmax=13, v=0, node_cap=None):
    """`N*(b, g, d)` 를 `d = 0..dmax` 에 대해 한 번의 탐색으로 구한다.

    **가지치기 주의**: `b >= 1` 이면 이미 떠난 궤도로 토큰 하나를 써서 되돌아올 수
    있으므로, "닫힌 궤도의 결손 합이 예산을 넘으면 가지치기" 는 **불건전**하다.
    R115 의 낙관적 `feasible` 을 그대로 쓴다: 남은 토큰과 handoff 토큰 수만큼의
    궤도를 결손에서 **면제**해 주고(가장 큰 결손부터 탐욕적으로), 나머지 합이
    예산 이하일 때만 계속한다.  면제는 과대평가이므로 실제 걸을 수 있는 가지를
    자르지 않는다.
    """
    nodes = [0]
    capped = [False]
    usedhex = {HEX[v]}
    omask = {ORB[v]: 1 << OPH[v]}
    defcnt = [0] * 5
    defcnt[4] = 1
    best = {}

    def feasible(extra_tokens, skip_orb, scap):
        c = defcnt[:]
        if skip_orb is not None and skip_orb in omask:
            c[5 - bin(omask[skip_orb]).count("1")] -= 1
        tok, tot = extra_tokens, 0
        for d in range(4, 0, -1):
            take = min(c[d], tok)
            tok -= take
            tot += (c[d] - take) * d
        return tot <= scap

    def rec(cur, corb, passes, tok):
        nodes[0] += 1
        if node_cap is not None and nodes[0] > node_cap:
            capped[0] = True
            return
        if feasible(g, None, dmax):
            tot = sum(d * defcnt[d] for d in range(5))
            # 실제 결손이 정확히 tot 인 사슬 -> 그 이상의 예산 전부에 유효
            if tot <= dmax and passes > best.get(tot, -1):
                best[tot] = passes
        # 낙관적 가지치기: 남은 토큰 tok (= BCAP - bused) 과 handoff g 만큼의
        # 궤도를 결손에서 면제한다.  R115 의 feasible(GCAP + (BCAP-bused), corb).
        if not feasible(g + tok, corb, dmax):
            return
        # (1) 현재 run 을 연장: 그 궤도의 아직 안 쓴 아무 위상으로
        ph = OPH[cur]
        for dp in range(1, 5):
            p = (ph + dp) % 5
            if omask[corb] >> p & 1:
                continue
            cost = 0 if dp == 1 else 1
            if cost > tok:
                continue
            nxt = ORB_AT[(corb, p)]
            if HEX[nxt] in usedhex:
                continue
            d0 = 5 - bin(omask[corb]).count("1")
            defcnt[d0] -= 1
            defcnt[d0 - 1] += 1
            omask[corb] |= 1 << p
            usedhex.add(HEX[nxt])
            rec(nxt, corb, passes + 1, tok - cost)
            usedhex.discard(HEX[nxt])
            omask[corb] &= ~(1 << p)
            defcnt[d0 - 1] -= 1
            defcnt[d0] += 1
        # (2) run 을 끝내고 경량 연결자로.  **새 궤도는 무료, 이미 등록된 궤도는
        #     토큰 1 개** (= 사슬 안의 여분 run).  이것이 `b` 의 주된 쓰임이다.
        for w in (W3C[cur], W3B[cur]):
            if HEX[w] in usedhex:
                continue
            nq = ORB[w]
            fresh = nq not in omask
            if not fresh and tok < 1:
                continue
            prev = omask.get(nq, 0)
            if fresh:
                defcnt[4] += 1
            else:
                d0 = 5 - bin(prev).count("1")
                defcnt[d0] -= 1
                defcnt[d0 - 1] += 1
            omask[nq] = prev | (1 << OPH[w])
            usedhex.add(HEX[w])
            rec(w, nq, passes + 1, tok - (0 if fresh else 1))
            usedhex.discard(HEX[w])
            if fresh:
                del omask[nq]
                defcnt[4] -= 1
            else:
                omask[nq] = prev
                d0 = 5 - bin(prev).count("1")
                defcnt[d0 - 1] -= 1
                defcnt[d0] += 1

    t0 = time.time()
    rec(v, ORB[v], 1, b)
    cum, run = {}, -1
    for d in range(dmax + 1):
        if best.get(d, -1) > run:
            run = best[d]
        cum[d] = run
    return dict(b=b, g=g, dmax=dmax, v=v, nodes=nodes[0], capped=capped[0],
                seconds=round(time.time() - t0, 1),
                exact_deficit_max={d: best.get(d) for d in range(dmax + 1)},
                N={d: cum[d] for d in range(dmax + 1)})


ASTRA = {
    (0, 0): 20, (0, 1): 20, (0, 2): 33, (0, 3): 33, (0, 4): 46, (0, 5): 46,
    (0, 6): 49, (0, 7): 58, (0, 8): 62, (0, 13): 83,
    (1, 0): 35, (1, 1): 35, (1, 2): 48, (1, 3): 48, (1, 8): 77, (1, 13): 98,
    (2, 3): 63, (2, 8): 92, (3, 3): 78,
}

if __name__ == "__main__":
    b = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    dmax = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else None
    r = chain_capacity(b=b, g=0, dmax=dmax, node_cap=cap)
    r["astra_expected"] = {f"({b},{d})": ASTRA[(b, d)]
                           for d in range(dmax + 1) if (b, d) in ASTRA}
    r["agrees"] = all(r["N"][d] == ASTRA[(b, d)]
                      for d in range(dmax + 1) if (b, d) in ASTRA)
    out = ROOT / "outputs" / f"rr_r139_capacity_b{b}_d{dmax}_139.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps({k: r[k] for k in ("b", "dmax", "nodes", "capped", "seconds",
                                        "N", "astra_expected", "agrees")},
                     ensure_ascii=False, indent=1))
