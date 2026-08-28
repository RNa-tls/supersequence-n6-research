#!/usr/bin/env python3
"""라운드 130 §14 — `G = 2` 짧은 pass 상태 기계의 **양성 대조**.

엔진의 기계가 실제 `G = 2` walk 을 하나도 거부하지 않는지(거짓 기각 0) `n = 4` 전수로
검사한다.  엔진 자체는 `n = 6` 전용이므로, 기계의 **의미론**을 파이썬으로 다시 구현해
합법 `n = 4` walk 10,625개(모두 `G = 2`)에 적용한다.

기계의 의미론:

* **유형 A** — 세 호는 `(w, m0)`, `(σ^{m0}(w), m1)`, `(σ^{m0+m1}(w), m2)` 이고
  `m0+m1+m2 = n`.  `w` 는 **walk 에서 처음 나오는** 호의 진입 단어다.
  `AORDER = 1` 이면 세 호가 walk 에서 정확히 그 순서(= `ν` 순서)로 나타나야 하며,
  라운드 129 에 의해 그것은 **내부 `F = 2`** 와 동치다.
* **유형 B** — 슬롯 두 개.  각 슬롯은 신선한 육각형에서 `(v, b)` 로 열리고 짝
  `(σ^b(v), n−b)` 로 닫힌다.  끼워넣기는 허용된다.
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


def replay_machine(n, g, passes, hexes, F):
    """walk 의 pass 열을 엔진의 기계로 재생한다.  받아들이면 True."""
    perms, idx, sg = g["perms"], g["idx"], g["sig"]
    cnt = Counter(hexes)
    multi = sorted(h for h, c in cnt.items() if c >= 2)
    shorts = [i for i, (u, ln) in enumerate(passes) if ln < n]
    if sorted(shorts) != sorted(i for i in range(len(passes)) if hexes[i] in multi):
        return False, "short passes are not exactly the multiply-entered hexagons' passes"
    if len(multi) == 1 and cnt[multi[0]] == 3:
        # ---- type A machine ------------------------------------------------
        arcs = [i for i in range(len(passes)) if hexes[i] == multi[0]]
        if len(arcs) != 3:
            return False, "type A needs exactly three arcs"
        w0 = passes[arcs[0]][0]
        m0 = passes[arcs[0]][1]
        z = perms[w0]
        for _ in range(m0):
            z = sg(z)
        w1 = idx[z]
        m1 = None
        for i in arcs[1:]:
            if passes[i][0] == w1:
                m1 = passes[i][1]
        if m1 is None:
            return False, "arc1 word not found"
        for _ in range(m1):
            z = sg(z)
        w2 = idx[z]
        if m0 + m1 >= n:
            return False, "arc lengths overflow"
        m2 = n - m0 - m1
        found = {passes[i][0]: passes[i][1] for i in arcs}
        if found != {w0: m0, w1: m1, w2: m2}:
            return False, "arc words/lengths do not match the sigma-cut"
        order_is_nu = [passes[i][0] for i in arcs] == [w0, w1, w2]
        if order_is_nu != (F == 2):
            return False, "nu-order does not coincide with F = 2"
        return True, ("A_nu_order" if order_is_nu else "A_reverse_order")
    if len(multi) == 2 and all(cnt[h] == 2 for h in multi):
        # ---- type B machine ------------------------------------------------
        for h in multi:
            ps = [i for i in range(len(passes)) if hexes[i] == h]
            if len(ps) != 2:
                return False, "type B needs two passes per hexagon"
            o, c = ps[0], ps[1]                    # walk order
            v, b = passes[o]
            z = perms[v]
            for _ in range(b):
                z = sg(z)
            if passes[c][0] != idx[z] or passes[c][1] != n - b:
                return False, "closer is not the forced partner"
        return True, "B"
    return False, "not a G = 2 multiplicity type"


def n4_positive_control(maxlen=39):
    n = 4
    g = setup(n)
    perms, sg, om = g["perms"], g["sig"], g["omega"]
    NW = len(perms)
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or legal_joint(n, perms[a], perms[b], W[a][b])
           for b in range(NW)] for a in range(NW)]
    ws = []

    def dfs(cur, used, seq, total):
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
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    dfs(0, 1, [0], 0)
    stat = Counter()
    rejects = []
    for L, seq in ws:
        m = walk_measure(g, W, seq, L)
        if m["G"] != 2:
            continue
        stat["G2"] += 1
        ok, why = replay_machine(n, g, m["passes"], m["hexes"], m["F"])
        stat[("accept:" + why) if ok else ("REJECT:" + why)] += 1
        if not ok and len(rejects) < 5:
            rejects.append(dict(L=L, why=why, F=m["F"], partition=list(m["partition"])))
    accepted = sum(v for k, v in stat.items() if str(k).startswith("accept"))
    return dict(
        n=4, maxlen=maxlen, walks=len(ws), G2_walks=stat["G2"],
        accepted=accepted, rejected=stat["G2"] - accepted,
        false_rejection=stat["G2"] - accepted,
        breakdown={str(k): v for k, v in sorted(stat.items()) if k != "G2"},
        reject_examples=rejects,
        clean=(accepted == stat["G2"]),
        note=("the type-A machine with AORDER = 1 accepts exactly the F = 2 walks, which is "
              "what the (4,2) cell needs since F = 2 is forced there; the F = 1 walks are "
              "accepted by the same machine with AORDER = 0"))


if __name__ == "__main__":
    print(json.dumps(n4_positive_control(), indent=1))
