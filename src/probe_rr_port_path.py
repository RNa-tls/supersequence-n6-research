#!/usr/bin/env python3
"""라운드 93 — 경로 순서 port 등록(PATH-ORDERED REGISTRATION).

엔진 의미론에서 직접 유도한 등록 규칙 (`extend` 를 그대로 읽은 것).

| 사건 | 등록 |
|---|---|
| 회전 σ (weight 1) | 없음.  target window 를 **방문 처리만** 한다 |
| 매크로 joint (weight ≥ 2) | **정확히 1개** — target 단어의 port (`om[q] |= 1<<phase`) |
| `E¹` (ℓ=5, w2:10) | 1개 (같은 궤도, 위상 +1) |
| `E²` (ℓ=5, w3:120) | 1개 (같은 궤도, 위상 +2) |
| `G5` opening | 1개 (fresh target 궤도) |
| 재진입 | 1개 (이미 열린 궤도의 미등록 port) |
| 어떤 사건도 | port 를 **2개 이상** 등록하지 못한다 |
| 등록된 port | 그 단어가 방문 상태이므로 다시 endpoint 가 될 수 없다 (엔진이 AssertionError 로 막는다) |

따라서 **pass 하나가 육각형 하나를 소비하고 진입 칸 1개만 등록**한다.  나머지 5칸은 회전
내부로 소비되어 영원히 등록 불가다.  아카이브에서 이 주장을 직접 확인했다 — 육각형별 등록
port 수는 빈 육각형 0, 지나간 육각형 1(수리된 fragment 만 2), 현재 육각형 1 이다.

**경로 조건.**  남은 빈 육각형은 각각 정확히 한 번 진입돼야 하고, 진입 칸은 등록되는 port
이므로 최종 25궤도의 단어여야 한다.  진입 칸에서의 출발은 `ℓ = 5` 이므로 다음 진입 칸은
`joint(σ⁵(u))` 중 하나다(fragment 수리만 `ℓ = 5 − c_f`).  각 pass 는 정확히 한 번 발사한다.

이것은 남은 육각형 위의 Hamilton 경로 조건이고, 그 **완화**로 이분 매칭을 쓴다.

    왼쪽  = 진입해야 하는 육각형(빈 육각형 + fragment)
    오른쪽 = 발사 슬롯(현재 pass + 각 빈 육각형 + fragment) — 각 1회 발사
    간선  = 슬롯의 어떤 진입 후보에서 σ^ℓ + joint 로 왼쪽 육각형의 어떤 진입 후보에 닿음

후보를 궤도별로 합집합해 쓰므로 관대한 과대근사이며, **Hall 위반만 폐쇄 근거**가 된다.
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


SL = _load("probe_rr_short_local", "src/probe_rr_short_local.py")
ssp = SL.ssp
core, macro, OP, HP, NORB = SL.core, SL.macro, SL.OP, SL.HP, SL.NORB
WORDS = list(core.ALL_WORDS)
ORBIT_WORDS = defaultdict(list)
HEX_WORDS = defaultdict(list)
for _w in WORDS:
    ORBIT_WORDS[OP[_w][0]].append(_w)
    HEX_WORDS[HP[_w][0]].append(_w)


def joint_targets(word, ell):
    cursor = word
    for _ in range(ell):
        cursor = core.word_after(cursor, core.SIGMA)
    return [core.word_after(cursor, move.action) for move in macro.NONROT_H0]


NEXT5 = {w: joint_targets(w, 5) for w in WORDS}


def _match(left, adjacency):
    matched = {}

    def augment(x, seen):
        for y in adjacency[x]:
            if y in seen:
                continue
            seen.add(y)
            if y not in matched or augment(matched[y], seen):
                matched[y] = x
                return True
        return False

    return sum(1 for x in left if augment(x, set()))


def path_registration(state, open_bits, S):
    """(verdict, info).  UNSAT 은 Hall 위반이 실제로 있을 때만 — 캡도 타임아웃도 없다."""
    final = {q for q in range(NORB) if open_bits >> q & 1} | set(S)
    W = {w for q in final for w in ORBIT_WORDS[q]}
    counts, current, fragments, _ = ssp.hexagon_profile(state)
    empty = [h for h, c in enumerate(counts) if c == 0]
    cand = {h: [w for w in HEX_WORDS[h] if w in W] for h in empty}
    orphan = [h for h in empty if not cand[h]]
    info = dict(empty=len(empty), final_words=len(W))
    if orphan:
        return "UNSAT", dict(info, reason="hexagon_has_no_final_orbit_word",
                             witness_hexagons=orphan[:8])
    sl = SL.short_local(state, open_bits)
    frag_entry = None
    if sl["budget"]:
        port = tuple(sl["source_ports"][0])
        frag_entry = next(w for w in WORDS if OP[w] == port)
    left = [("hex", h) for h in empty] + ([("frag",)] if frag_entry else [])
    slots = [("cur",)] + left

    def successors(slot):
        if slot == ("cur",):
            return set(NEXT5[state.p])
        if slot == ("frag",):
            return set(joint_targets(frag_entry, sl["ell"]))
        out = set()
        for u in cand[slot[1]]:
            out.update(NEXT5[u])
        return out

    succ = {s: successors(s) for s in slots}
    adjacency = {}
    for node in left:
        targets = set(cand[node[1]]) if node[0] == "hex" else {frag_entry}
        adjacency[node] = [s for s in slots if s != node and (succ[s] & targets)]
    unreachable = [n for n in left if not adjacency[n]]
    size = _match(left, adjacency)
    info.update(left=len(left), slots=len(slots), matched=size,
                unreachable=len(unreachable))
    if size < len(left):
        return "UNSAT", dict(info, reason="registration_hall_violation",
                             deficit=len(left) - size,
                             witness_hexagons=[n[1] for n in unreachable if n[0] == "hex"][:8])
    return "SAT", info


def decide_state(row, model="joint+path"):
    """모든 valid cover 를 흘려보내며 결합 조건 + 경로 조건을 함께 판정."""
    sl = SL.short_local(row["state"], row["open_orbits"])
    acc = {"verdict": "UNSAT", "cover": None, "path": None, "covers": 0,
           "joint_pass": 0}

    def on_cover(S, _row=row, _sl=sl, _acc=acc):
        ok, _T = SL.feasible(S, _row["open_orbits"], _sl, "local")
        if not ok:
            return False
        _acc["joint_pass"] += 1
        if model == "joint":
            _acc["verdict"], _acc["cover"] = "SAT", list(S)
            return True
        verdict, info = path_registration(_row["state"], _row["open_orbits"], set(S))
        if verdict == "SAT":
            _acc["verdict"], _acc["cover"], _acc["path"] = "SAT", list(S), info
            return True
        _acc["path"] = info
        return False

    scan = ssp.scan_covers(row, on_cover)
    acc["covers"] = scan["covers"]
    if acc["verdict"] == "UNSAT" and not scan["complete"]:
        acc["verdict"] = "UNKNOWN"
    return acc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("semantics", "sweep"))
    ap.add_argument("--sids", help="sid 목록 JSON (없으면 전체)")
    ap.add_argument("--exclude", help="이미 닫힌 sid 목록 JSON")
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = ssp.po.load_states()

    if args.command == "semantics":
        dist = Counter()
        for r in rows:
            st = r["state"]
            registered = Counter()
            for q in range(NORB):
                for f in range(5):
                    if st.orbit_masks[q] >> f & 1:
                        registered[HP[next(w for w in ORBIT_WORDS[q] if OP[w][1] == f)][0]] += 1
            counts, current, fragments, _ = ssp.hexagon_profile(st)
            for h in range(120):
                kind = ("empty" if counts[h] == 0 else "fragment" if h in fragments
                        else "current" if h == current else "passed")
                dist[(kind, registered[h])] += 1
        result = dict(states=len(rows),
                      registered_ports_per_hexagon={f"{k[0]}:{k[1]}": v for k, v in sorted(dist.items())},
                      claim="pass 하나당 등록 port 는 정확히 1개 — 빈 육각형 0, 지나간 육각형 1(수리된 fragment 2), 현재 1")
    else:
        want = None
        if args.sids:
            data = json.load(open(args.sids))
            want = {s["sid"] if isinstance(s, dict) else s
                    for s in (data["states"] if isinstance(data, dict) else data)}
        closed = set()
        if args.exclude:
            closed = set(json.load(open(args.exclude)))
        base = [r for r in rows if (want is None or r["sid"] in want) and r["sid"] not in closed]
        print(f"input states: {len(base)}", flush=True)
        agg, out = Counter(), []
        t0 = time.time()
        for i, r in enumerate(base):
            res = decide_state(r)
            agg[res["verdict"]] += 1
            out.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=r["K"],
                            verdict=res["verdict"], covers=res["covers"],
                            joint_passing=res["joint_pass"], witness_cover=res["cover"],
                            path=res["path"]))
            if (i + 1) % 500 == 0:
                print(f"  {i+1}/{len(base)} {dict(agg)} {time.time()-t0:.0f}s", flush=True)
        newly = [o for o in out if o["verdict"] == "UNSAT"]
        result = dict(input_states=len(base), aggregate=dict(agg), new_closures=len(newly),
                      by_c=dict(Counter(o["c"] for o in newly)),
                      by_root=dict(Counter(o["root"] for o in newly)),
                      seconds=round(time.time() - t0), ledger=out)
    print(json.dumps({k: v for k, v in result.items() if k != "ledger"},
                     ensure_ascii=False, indent=1)[:2500])
    if args.out:
        json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
