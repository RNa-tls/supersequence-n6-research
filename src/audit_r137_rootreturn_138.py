#!/usr/bin/env python3
"""라운드 137 감사 — **root-return 사슬 용량 `R(d)` 의 독립 재구현** (정정판).

Astra 의 코드·기하·탐색을 하나도 import 하지 않는다.  모델 정의만 보고서에서 읽고
`verify_f2_structure_126.setup(6)` 의 기하 위에 처음부터 다시 짠다.

모델 (라운드 137 보고서 §7):
  * pass 는 전부 full, 육각형 중복 없음, `x = H = 0`;
  * 첫 진입 `v`, 마지막 진입 `τ^{-1}(v)` (둘 다 root 궤도);
  * root 궤도는 **정확히 두 run**, 다른 궤도는 **정확히 한 run**;
  * run 내부 이동은 `τ` 한 걸음뿐, run 사이는 경량 연결자 `W3b`/`W3c`;
  * 결손 `d` = Σ_궤도 (5 − 그 궤도의 pass 수), **정확히** `d`.

**정정**: 초판은 궤도 위상 비트를 확장 분기에서는 상대 위상, 연결자 분기에서는 절대
위상으로 매겨 마스크가 어긋났다.  이제 **절대 위상 `OPH` 하나로** 통일한다.  두 root run
의 위상 구간이 서로소여야 한다는 조건은 마스크가 자동으로 강제하므로 `p ≤ q` 를 따로
들고 다닐 필요가 없다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
G = setup(6)
P6, IDX, SG, TA = G["perms"], G["idx"], G["sig"], G["tau"]
ORB, HEX, OPH = G["orbid"], G["hexid"], G["orbph"]


def _sig5(w):
    y = P6[w]
    for _ in range(5):
        y = SG(y)
    return y


W3B = [IDX[(_sig5(w)[3], _sig5(w)[4], _sig5(w)[5], _sig5(w)[2], _sig5(w)[0],
            _sig5(w)[1])] for w in range(720)]
W3C = [IDX[(_sig5(w)[3], _sig5(w)[4], _sig5(w)[5], _sig5(w)[2], _sig5(w)[1],
            _sig5(w)[0])] for w in range(720)]
TAU = [IDX[TA(P6[w])] for w in range(720)]


def root_return_capacity(dmax=13, v=0):
    rootorb = ORB[v]
    last_word = TAU[TAU[TAU[TAU[v]]]]                 # tau^{-1}(v)
    assert ORB[last_word] == rootorb and last_word != v

    best = {d: -1 for d in range(dmax + 1)}
    allc = Counter()
    atmax = Counter()
    nodes = [0]
    usedhex = set()
    omask = {}

    def deficit(exclude):
        return sum(5 - bin(m).count("1") for q, m in omask.items() if q != exclude)

    def deficit_lb(exclude, returned):
        """Sound lower bound on the FINAL deficit.

        An orbit that has been left can never be re-entered -- except the root
        orbit, which is still owed its second run while ``returned`` is false.
        Charging root's current deficit before that return is unsound: it can
        still absorb up to five more passes.  So root contributes 0 until the
        return has happened.
        """
        tot = 0
        for q, m in omask.items():
            if q == exclude:
                continue
            if q == rootorb and not returned:
                continue
            tot += 5 - bin(m).count("1")
        return tot

    def rec(cur, corb, passes, returned):
        nodes[0] += 1
        if returned and cur == last_word:
            d = deficit(None)
            if d <= dmax:
                if passes > best[d]:
                    best[d] = passes
                allc[d] += 1
                atmax[(d, passes)] += 1
        if deficit_lb(corb, returned) > dmax:
            return
        # (1) tau-extend the current run
        nxt = TAU[cur]
        if ORB[nxt] == corb and not (omask[corb] >> OPH[nxt] & 1) \
                and HEX[nxt] not in usedhex:
            omask[corb] |= 1 << OPH[nxt]
            usedhex.add(HEX[nxt])
            rec(nxt, corb, passes + 1, returned)
            usedhex.discard(HEX[nxt])
            omask[corb] &= ~(1 << OPH[nxt])
        # (2) end the run, take a light connector
        for w in (W3C[cur], W3B[cur]):
            if HEX[w] in usedhex:
                continue
            nq = ORB[w]
            fresh = nq not in omask
            if not fresh:
                if returned or nq != rootorb:      # the ONE allowed return is to root
                    continue
            if omask.get(nq, 0) >> OPH[w] & 1:
                continue
            prev = omask.get(nq, 0)
            omask[nq] = prev | (1 << OPH[w])
            usedhex.add(HEX[w])
            rec(w, nq, passes + 1, returned or (not fresh))
            usedhex.discard(HEX[w])
            if prev:
                omask[nq] = prev
            else:
                del omask[nq]

    omask[rootorb] = 1 << OPH[v]
    usedhex.add(HEX[v])
    rec(v, rootorb, 1, False)
    return dict(v=v, dmax=dmax, nodes=nodes[0],
                R={d: (best[d] if best[d] >= 0 else None) for d in range(dmax + 1)},
                chains_all={d: allc[d] for d in range(dmax + 1)},
                chains_at_max={d: atmax[(d, best[d])] for d in range(dmax + 1)
                               if best[d] >= 0})


if __name__ == "__main__":
    import time
    t = time.time()
    r = root_return_capacity()
    r["seconds"] = round(time.time() - t, 1)
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_r137_rootreturn_audit_138.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps({k: r[k] for k in ("nodes", "seconds", "R", "chains_all",
                                        "chains_at_max")}, indent=1))
