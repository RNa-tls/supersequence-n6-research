#!/usr/bin/env python3
"""라운드 90c / 91-A — 네 경계 witness 의 완전 구조와 short edge 의 리터럴 검사.

라운드 90 은 유일-cover 19개를 전부 닫았다고 보고했으나 Codex 의 독립 감사는 **15 UNSAT /
4 SAT** 이었다.  차이는 하나다: 라운드 90 의 M2 는 `ℓ<5` edge 의 **개수**뿐 아니라 **출발
자리**까지 고정했고, 그 고정은 독립 재현되지 않았다.  네 상태는 적대적 경계 witness 로
보존한다 — 가용 short 예산 1 = 최소 필요 예산 1 로, 검증된 모든 조건을 등호에서 만족한다.

이 모듈이 하는 일.

witness (§6).  고정된 유일 cover `S` 에 대해 **정확히 1개의 short opening** 을 쓰는 모든
    A-rooted · port-단사 생성 구조를 열거하고, 대표 witness 를 여는 순서대로 펼친다
    (target 궤도 / G5·SHORT / source 궤도·위상·단어·육각형 / `ℓ` / joint / 착지 위상).

literal (§7, §8).  각 witness 의 short edge 를 엔진 의미론에 비추어 분류한다.  라운드 88/90
    의 결합 조건이 표현하지 않는 조건만 본다 — 출발 육각형의 현재 상태, no-repeat 상 시작 칸
    존재 여부, abandonment 여부.  분류는 다음 셋이다.

      EMPTY_SOURCE_HEX  신선한 육각형에서 `ℓ<5` 로 떠나면 `σ(마지막)` 이 이 pass 밖이라
                        abandonment 이고 `F = 2 > TARGET_F` 다.
      FULL_SOURCE_HEX   가득 찬 육각형에는 미방문 시작 칸이 없어 edge 가 발사되지 않는다.
      CURRENT_HEX       그 육각형의 pass 는 현재 pass 뿐이고, 엔진 확인상 abandonment 없는
                        출발은 `ℓ = 5` 뿐이다.
      FRAGMENT_HEX      short pass 가 합법일 수 있는 유일한 자리.

    네 상태의 40만 개 witness 중 `FRAGMENT_HEX` 는 **0개**였다.  거기서 나오는 후보 제약이

      SHORT-PASS LOCALITY — `ℓ<5` 매크로 edge 는 그 시점에 방문 칸이 있고 아직 가득 차지
      않은 육각형에서 출발해야 하며, `F=1` 아래에서 그것은 fragment 뿐이다.

    **이 제약은 Codex 감사 대기 상태이며, 이 모듈은 그것을 폐쇄 근거로 쓰지 않는다.**

사용법: `python3 src/probe_rr_boundary_witness.py {witness,literal} [--sids <json|csv>]`
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.setrecursionlimit(20000)
ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ssp = _load("probe_rr_single_short_pass", "src/probe_rr_single_short_pass.py")
core, exact, macro = ssp.core, ssp.exact, ssp.macro
OP, HP, SRC, NORB = ssp.OP, ssp.HP, ssp.SRC, ssp.NORB
WORD = {OP[w]: w for w in core.ALL_WORDS}
DEFAULT_SIDS = ROOT / "outputs" / "rr_boundary_witnesses_claude.json"
WITNESS_CAP = 400_000
NODE_CAP = 30_000_000


def short_port_table():
    """SHORTP[(q, f)][r] = 그 port 에서 `ℓ<5` 로 r 을 여는 (ℓ, joint) 목록."""
    w3 = [m for m in macro.NONROT_H0 if m.weight == 3]
    table = {}
    for (q, f), word in WORD.items():
        cursor, targets = word, defaultdict(list)
        for ell in range(5):
            for move in w3:
                r = OP[core.word_after(cursor, move.action)][0]
                if r != q:
                    targets[r].append((ell, move.label))
            cursor = core.word_after(cursor, core.SIGMA)
        table[(q, f)] = dict(targets)
    return table


SHORTP = short_port_table()


def one_short_witnesses(S, A, cap=WITNESS_CAP):
    """정확히 1개의 short opening 을 쓰는 모든 A-rooted · port-단사 부모 구조."""
    Aset, Sset = set(A), set(S)
    pool = sorted(Aset | Sset)
    g5 = {r: [(q, f) for q in pool if q != r for f in range(5) if r in SRC[(q, f)]] for r in S}
    sh = {r: [(q, f) for q in pool if q != r for f in range(5) if r in SHORTP[(q, f)]] for r in S}
    parent, kind, used, out = {}, {}, set(), []
    st = {"nodes": 0, "complete": True}

    def reaches(a, b):
        seen = set()
        while a in parent and a not in seen:
            seen.add(a)
            if a == b:
                return True
            a = parent[a]
        return a == b

    def rec(remaining, nshort):
        if st["nodes"] > NODE_CAP or len(out) > cap:
            st["complete"] = False
            return
        if not remaining:
            if nshort == 1:
                out.append({r: kind[r] for r in kind})
            return
        st["nodes"] += 1
        best, fewest = None, 1 << 30
        for r in remaining:
            n = sum(1 for p in g5[r] if p not in used)
            if nshort < 1:
                n += sum(1 for p in sh[r] if p not in used)
            if n < fewest:
                best, fewest = r, n
            if n == 0:
                return
        rest = remaining - {best}
        for (q, f) in g5[best]:
            if (q, f) in used or (q in Sset and reaches(q, best)):
                continue
            used.add((q, f))
            parent[best], kind[best] = q, ("G5", q, f, 5)
            rec(rest, nshort)
            used.discard((q, f))
            del parent[best], kind[best]
            if not st["complete"]:
                return
        if nshort < 1:
            for (q, f) in sh[best]:
                if (q, f) in used or (q in Sset and reaches(q, best)):
                    continue
                ell = SHORTP[(q, f)][best][0][0]
                used.add((q, f))
                parent[best], kind[best] = q, ("SHORT", q, f, ell)
                rec(rest, nshort + 1)
                used.discard((q, f))
                del parent[best], kind[best]
                if not st["complete"]:
                    return

    rec(frozenset(S), 0)
    return out, st["complete"], st["nodes"]


def expand(witness, A):
    """witness 를 여는 순서대로 펼친다 (부모 구조는 A-rooted 이므로 위상 정렬이 존재)."""
    opened, left, order = set(A), dict(witness), []
    while left:
        for r, (k, q, f, ell) in list(left.items()):
            if q not in opened:
                continue
            source = WORD[(q, f)]
            cursor = source
            for _ in range(ell):
                cursor = core.word_after(cursor, core.SIGMA)
            landing = None
            for move in macro.NONROT_H0:
                t = core.word_after(cursor, move.action)
                if OP[t][0] == r:
                    landing = (move.label, OP[t][1])
                    break
            order.append(dict(target_orbit=r, kind=k, source_orbit=q, source_phase=f,
                              source_word=list(source), source_hex=HP[source][0], ell=ell,
                              joint=landing and landing[0], landing_phase=landing and landing[1]))
            opened.add(r)
            del left[r]
    return order


def classify_short_source(state, hexagon, fragment_hex):
    """short edge 의 출발 육각형을 엔진 상태에 비추어 분류 (§7)."""
    filled = bin(state.hex_masks[hexagon]).count("1")
    if hexagon == fragment_hex:
        return "FRAGMENT_HEX"
    if hexagon == HP[state.p][0]:
        return "CURRENT_HEX"
    if filled == 0:
        return "EMPTY_SOURCE_HEX"
    if filled == 6:
        return "FULL_SOURCE_HEX"
    return "OTHER_PARTIAL_HEX"


def rotation_fact_holds():
    """전수 확인: `ℓ<5` 면 `σ(마지막)` 이 pass 밖, `ℓ=5` 면 안 (720 단어 x 6)."""
    for word in core.ALL_WORDS:
        cursor, run = word, [word]
        for ell in range(6):
            if ell:
                cursor = core.word_after(cursor, core.SIGMA)
                run.append(cursor)
            inside = core.word_after(cursor, core.SIGMA) in run
            if (ell < 5) == inside:
                return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("witness", "literal"))
    ap.add_argument("--sids", default=str(DEFAULT_SIDS))
    ap.add_argument("--out")
    args = ap.parse_args()
    path = Path(args.sids)
    if path.exists():
        data = json.load(open(path))
        want = {s["sid"] for s in (data["states"] if isinstance(data, dict) else data)}
    else:
        want = set(args.sids.split(","))
    rows = [r for r in ssp.po.load_states() if r["sid"] in want]
    print(f"boundary states: {len(rows)}", flush=True)
    report = []
    for r in rows:
        pin, _ = ssp.pinned_short_edge(r["state"])
        A = [q for q in range(NORB) if r["open_orbits"] >> q & 1]
        data = json.load(open(path)) if path.exists() else None
        S = next(s["unique_cover_S"] for s in data["states"] if s["sid"] == r["sid"])
        t0 = time.time()
        wits, complete, nodes = one_short_witnesses(S, A)
        entry = dict(sid=r["sid"], root=r["root"], witnesses=len(wits),
                     complete=complete, nodes=nodes, seconds=round(time.time() - t0, 1))
        if args.command == "witness":
            entry["representative"] = expand(wits[0], A) if wits else None
        else:
            classes, edges = Counter(), set()
            for w in wits:
                for target, (k, q, f, ell) in w.items():
                    if k != "SHORT":
                        continue
                    edges.add((q, f, target, ell))
                    classes[classify_short_source(
                        r["state"], HP[WORD[(q, f)]][0], pin["hex"] if pin else -1)] += 1
            entry["short_edge_classes"] = dict(classes)
            entry["distinct_short_edges"] = len(edges)
            entry["uses_fragment_hex"] = classes.get("FRAGMENT_HEX", 0)
        report.append(entry)
        print(f"  {r['sid'][:8]} {json.dumps({k: v for k, v in entry.items() if k != 'representative'}, ensure_ascii=False)}",
              flush=True)
    result = dict(states=report, rotation_fact_exhaustively_verified=rotation_fact_holds(),
                  note="SHORT-PASS LOCALITY 는 Codex 감사 대기 중이며 폐쇄 근거로 쓰지 않는다")
    print(json.dumps({k: v for k, v in result.items() if k != "states"}, ensure_ascii=False))
    if args.out:
        json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
