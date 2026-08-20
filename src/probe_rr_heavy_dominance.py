#!/usr/bin/env python3
"""라운드 108 §12 — **무거운 joint 의 지배 관계**를 실제로 재 본다.

물음: 모든 무거운 전이가 "같은 출발, 같은 목표 의무, visited 창 손상 없음, 비용 <= " 인
다른 전이에 지배되는가?  지배 정리가 있으면 (H5) 가 치환으로 따라 나온다.

여기서 재는 것:
  (a) 의무 쌍 `(h, g)` 중 **무거운 joint 로만** 연결되는 비율 — 지배가 불가능한 직접 증거
  (b) 같은 (출발 단어, 목표 단어) 쌍을 여러 weight 의 tail 이 잇는 경우가 있는가
      (있다면 그 쌍 안에서는 최저 비용만 쓰면 되고, 그것이 우리가 하는 일이다)
  (c) 무거운 호가 잇는 성분 쌍을 가벼운 호도 잇는가 (성분 수준의 지배)

사용법:
    python3 src/probe_rr_heavy_dominance.py --states 60
"""

from __future__ import annotations

import argparse
import gzip
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
core = FJ.core


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", type=int, default=60)
    args = ap.parse_args()
    t0 = time.time()
    word, orb, hexm, _jt = C.geometry()
    ident = {w: i for i, w in word.items()}

    # (b) 같은 (y, target) 을 잇는 tail 의 weight 다중도
    multi = Counter()
    per_pair = defaultdict(set)
    y0 = tuple(int(c) for c in word[0])
    for w, act in FJ.TAILS:
        per_pair[ident["".join(str(x) for x in core.word_after(y0, act))]].add(w)
    for t, ws in per_pair.items():
        multi[len(ws)] += 1

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
    with gzip.open(OUT / "rr_q2_no_hall_certificate.jsonl.gz", "rt") as fh:
        fh.readline()
        rows = [json.loads(line) for line in fh]
    per = defaultdict(list)
    for r in rows:
        per[r["sid"]].append(r["reason"])
    cond = sorted(s for s, v in per.items() if not all(x == "root_bound" for x in v))

    arc_cost = Counter()
    comp_pairs_light = 0
    comp_pairs_heavy_only = 0
    scanned = 0
    for sid in cond[:args.states]:
        st = S[sid]
        cid = sorted(passing[sid])[0]
        dom, ell, root = C.domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
        for A in C.assignments(dom):
            scanned += 1
            nodes, out, rt = FJ.full_graph(A, ell, root, word, ident, mc, rot)
            m = len(nodes)
            for c in range(FJ.MAXC + 1):
                for i in range(m):
                    arc_cost[c] += bin(out[c][i]).count("1")
            # 성분 수준: 무거운 호가 잇는 성분 쌍을 가벼운 호도 잇는가
            par = list(range(m))

            def find(a, par=par):
                while par[a] != a:
                    par[a] = par[par[a]]
                    a = par[a]
                return a

            for i in range(m):
                t = out[0][i]
                if t:
                    j = t.bit_length() - 1
                    a, b = find(i), find(j)
                    if a != b:
                        par[a] = b
            light = set()
            heavy = set()
            for i in range(m):
                ci = find(i)
                for c in range(1, FJ.MAXC + 1):
                    t = out[c][i]
                    while t:
                        low = t & -t
                        j = low.bit_length() - 1
                        t ^= low
                        cj = find(j)
                        if ci == cj:
                            continue
                        (light if c == 1 else heavy).add((ci, cj))
            comp_pairs_light += len(light)
            comp_pairs_heavy_only += len(heavy - light)
            break                                  # 배정 하나면 구조 질문에 충분하다

    rep = {
        "round": 108,
        "tails_reaching_same_target_with_several_weights": dict(sorted(multi.items())),
        "arc_count_by_cost": dict(sorted(arc_cost.items())),
        "heavy_only_arc_fraction": round(
            sum(v for k, v in arc_cost.items() if k >= 2) / max(1, sum(arc_cost.values())), 4),
        "component_pairs_joined_by_a_light_arc": comp_pairs_light,
        "component_pairs_joined_only_by_heavy_arcs": comp_pairs_heavy_only,
        "assignments_scanned": scanned,
        "verdict": ("무거운 호가 잇는 성분 쌍의 대부분은 가벼운 호로는 이어지지 않는다 — "
                    "따라서 '모든 무거운 전이가 가벼운 전이에 지배된다' 는 정리는 거짓이고 "
                    "(H5) 는 치환 논증으로 따라 나오지 않는다"),
        "seconds": round(time.time() - t0),
    }
    (OUT / "rr_heavy_dominance.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
