#!/usr/bin/env python3
"""라운드 109 §5 — **일정 수립용** 난이도 예측치만 계산한다.

여기서 나오는 어떤 값도 가지치기 정리로 쓰지 않는다.  오직 166개 상태를 **쉬운 것부터**
정렬하기 위한 것이다.  라운드-108 의 사운드 모델(550 tail 전부)을 그대로 쓴다.

상태마다 기록:
    pairs · assignments · max_s · assignments_with_s_ge_1
    admissible_heavy_arcs  (예산 보조정리로 살아남는 cost <= s+1 호의 총합)
    root_components · obligations · branching_estimate

사용법:
    python3 src/schedule_rr_round109.py
"""

from __future__ import annotations

import importlib.util as iu
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def _load(name, path):
    spec = iu.spec_from_file_location(name, path)
    mod = iu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FJ = _load("certify_rr_full_joint", ROOT / "src" / "certify_rr_full_joint.py")
C = FJ.C


def main() -> None:
    t0 = time.time()
    sids = json.loads((OUT / "rr_h5_audit" / "round109_input_states.json").read_text())["sids"]
    word, orb, hexm, jt = C.geometry()
    ident = {w: i for i, w in word.items()}
    mc = FJ.min_cost_table(word, ident)
    rot = {(i, k): FJ.rot_id(word, ident, i, k) for i in range(720) for k in range(6)}
    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    _h, covers = C.read_jsonl(C.ARCHIVE / "covers.jsonl.gz")
    _h, hall = C.read_jsonl(C.ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        passing[h["sid"]].append(h["cover_id"])

    rows = []
    for n, sid in enumerate(sids, 1):
        st = S[sid]
        B = 3 + st["K"] - (st["S"] + st["F"] - st["O"]) - st["H"]
        pairs = sorted(passing[sid])
        n_assign = hard = heavy_total = 0
        max_s = -99
        comps = obl = 0
        for cid in pairs:
            dom, ell, root = C.domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
            for A in C.assignments(dom):
                n_assign += 1
                _n2, lout0, lout1, lr0, lr1 = C.weighted_graph(A, ell, root, jt)
                s = B - FJ.root_bound(lout0, lr0)
                max_s = max(max_s, s)
                if s <= 0:
                    continue
                hard += 1
                nodes, out, rt = FJ.full_graph(A, ell, root, word, ident, mc, rot)
                obl = len(nodes)
                comps = FJ.components(out[0], (1 << len(nodes)) - 1)
                keep = min(FJ.MAXC, s + 1)
                for cc in range(2, keep + 1):
                    heavy_total += sum(bin(v).count("1") for v in out[cc])
        rows.append({"sid": sid, "B": B, "pairs": len(pairs), "assignments": n_assign,
                     "max_s": max_s, "assignments_with_s_ge_1": hard,
                     "admissible_heavy_arcs": heavy_total,
                     "root_components": comps, "obligations": obl,
                     "branching_estimate": round(heavy_total / max(1, hard), 1)})
        if n % 25 == 0:
            print(f"  {n}/{len(sids)} {time.time()-t0:.0f}s", flush=True)

    rows.sort(key=lambda r: (r["admissible_heavy_arcs"], r["max_s"], r["assignments_with_s_ge_1"]))
    rep = {"round": 109, "states": len(rows),
           "note": "일정 수립 전용 — 어떤 값도 가지치기에 쓰지 않는다",
           "max_s_histogram": dict(sorted(Counter(r["max_s"] for r in rows).items())),
           "total_hard_assignments": sum(r["assignments_with_s_ge_1"] for r in rows),
           "total_admissible_heavy_arcs": sum(r["admissible_heavy_arcs"] for r in rows),
           "easiest_first": [r["sid"] for r in rows],
           "rows": rows, "seconds": round(time.time() - t0)}
    (OUT / "rr_round109_schedule.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items()
                      if k not in ("rows", "easiest_first")}, ensure_ascii=False, indent=1))
    q = [r["admissible_heavy_arcs"] for r in rows]
    print("admissible_heavy_arcs  min/median/max:", q[0], q[len(q) // 2], q[-1])
    hh = [r["assignments_with_s_ge_1"] for r in rows]
    print("hard assignments per state min/median/max:",
          min(hh), sorted(hh)[len(hh) // 2], max(hh))


if __name__ == "__main__":
    main()
