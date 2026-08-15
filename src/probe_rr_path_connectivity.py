#!/usr/bin/env python3
"""라운드 94 — Hall 매칭보다 강한 **경로 연결성** 필요조건.

라운드 93(독립 확인)은 미래 pass 진입 의무를 전임 자원에 **단사로 배정**할 수 있는지만 본다.
실제 완성은 하나의 시간 순서 walk 이므로 그 배정들이 **하나의 뿌리 달린 구조**여야 한다.

유도 (엔진 의미론에서, 라운드 93 에서 확인된 것만 사용).

    * 회전은 port 를 등록하지 않고 joint 는 정확히 1개 등록한다 ⟹ pass 하나가 육각형 하나를
      소비하고 진입 칸 하나만 등록한다.
    * 남은 의무 = 빈 육각형 각각 1회 진입 (+ fragment 가 남아 있으면 수리 진입 1회).
    * 진입 칸은 최종 25궤도의 단어여야 한다.
    * 진입 칸에서의 출발은 `ℓ=5`(fragment 수리는 `5−c_f`) 이므로 다음 진입 칸은
      `joint(σ^ℓ(u))` 중 하나다.
    * 각 pass 는 정확히 한 번 발사한다.

따라서 미래는 **현재 pass 를 뿌리로 하는 하나의 유향 경로**이고, 의무 위의 유향 그래프

    x → y  ⟺  x 의 어떤 진입 후보에서 y 의 어떤 진입 후보로 `σ^ℓ`+joint 가 닿는다

에서 다음이 성립해야 한다.

    A. 모든 의무가 뿌리(현재 pass)에서 **도달 가능**해야 한다.
    B. 뿌리를 포함하지 않고 **외부 전임자가 전혀 없는 닫힌 부분집합 X** 는 불가능하다.
       (A 의 위반 집합이 정확히 그런 X 이므로 A ⟺ B 이며, 이 모듈은 둘을 따로 구현해
       실제로 일치하는지 확인한다.)
    C. Hall 단사 배정과 뿌리 연결성을 **동시에** 만족해야 한다.  각 의무의 유입 차수가 1,
       각 슬롯의 유출 차수가 ≤1 이므로 선택된 간선은 (뿌리에서 나온 경로) + (사이클들) 로
       분해된다.  사이클이 하나라도 있으면 그 사이클은 뿌리에서 닿을 수 없으므로 불가능하다.

과대근사(안전): 한 육각형의 진입 후보를 source 역할과 target 역할에서 독립적으로 고르도록
허용하고, `E¹`/`E²`/재진입이 만들 수 있는 연결도 배제하지 않는다.  따라서 **위반만** 폐쇄
근거가 된다.

사용법:
    python3 src/probe_rr_path_connectivity.py layers   # A/B/C 층별 payoff
    python3 src/probe_rr_path_connectivity.py control  # 실현된 이력에 대한 양성 대조
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parent.parent / "outputs" / "rr_port_path_hall_archive"


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


def load(archive=ARCHIVE):
    _, geo = read_jsonl(archive / "geometry.jsonl.gz")
    by_id = {g["id"]: g for g in geo}
    hex_words = defaultdict(list)
    for g in geo:
        hex_words[g["hexagon"]].append(g["id"])
    _, states = read_jsonl(archive / "states.jsonl.gz")
    _, covers = read_jsonl(archive / "covers.jsonl.gz")
    _, hall = read_jsonl(archive / "hall_results.jsonl.gz")
    return by_id, hex_words, states, covers, hall


def obligation_graph(state, cover, geo, hex_words):
    """의무 위의 유향 그래프와 뿌리의 초기 후속 집합."""
    final = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1} | set(cover)
    empty = [h for h, m in enumerate(state["hex_masks"]) if m == 0]
    cand = {("hex", h): [w for w in hex_words[h] if geo[w]["orbit"] in final] for h in empty}
    frag = state["fragment"]
    if frag:
        cand[("frag",)] = [frag["entry_id"]]
    nodes = list(cand)

    def succ_words(node):
        if node == ("root",):
            return set(geo[state["p_id"]]["joint_targets"]["5"])
        if node == ("frag",):
            return set(geo[frag["entry_id"]]["joint_targets"][str(frag["ell"])])
        out = set()
        for u in cand[node]:
            out.update(geo[u]["joint_targets"]["5"])
        return out

    word_owner = {}
    for node, words in cand.items():
        for w in words:
            word_owner[w] = node
    edges = {}
    for node in [("root",)] + nodes:
        targets = set()
        for w in succ_words(node):
            owner = word_owner.get(w)
            if owner is not None and owner != node:
                targets.add(owner)
        edges[node] = targets
    return nodes, edges, cand


def layer_a_reachable(nodes, edges):
    seen = {("root",)}
    queue = deque([("root",)])
    while queue:
        x = queue.popleft()
        for y in edges.get(x, ()):
            if y not in seen:
                seen.add(y)
                queue.append(y)
    return [n for n in nodes if n not in seen], seen


def layer_b_closed_subset(nodes, edges):
    """뿌리를 포함하지 않고 외부 전임자가 없는 극대 닫힌 집합 (독립 구현)."""
    incoming = defaultdict(set)
    for x, ys in edges.items():
        for y in ys:
            incoming[y].add(x)
    X = set(nodes)
    changed = True
    while changed:
        changed = False
        for n in list(X):
            if any(p not in X for p in incoming.get(n, ())):
                X.discard(n)
                changed = True
    return sorted(X)


def layer_b2_terminal_bounds(nodes, edges):
    """단일 경로는 **끝점이 정확히 하나**다 — 그로부터 나오는 값싼 필요조건들.

      * 뿌리의 유출 차수가 0 이면 첫 pass 를 발사할 수 없다.
      * 유출 차수 0 인 의무가 2개 이상이면 둘 다 경로의 끝이어야 하므로 불가능하다.
      * 응축 그래프의 **sink SCC 가 2개 이상**이면 마찬가지다 — sink 를 떠날 수 없으므로
        경로는 그 안에서 끝나야 하는데 끝은 하나뿐이다.
    """
    if not edges.get(("root",)):
        return "root_has_no_successor", None
    dead = [n for n in nodes if not edges.get(n)]
    if len(dead) >= 2:
        return "two_terminal_obligations", [list(x) for x in dead[:6]]
    index, low, on, stack, order, comp = {}, {}, set(), [], [], {}
    counter = [0]

    def strong(v):
        work = [(v, iter(edges.get(v, ())))]
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        while work:
            u, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(edges.get(w, ()))))
                    advanced = True
                    break
                if w in on:
                    low[u] = min(low[u], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[u])
            if low[u] == index[u]:
                group = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    group.append(w)
                    if w == u:
                        break
                cid = len(order)
                order.append(group)
                for w in group:
                    comp[w] = cid

    for n in nodes:
        if n not in index:
            strong(n)
    sinks = []
    for cid, group in enumerate(order):
        if not any(comp.get(y, cid) != cid for x in group for y in edges.get(x, ())):
            sinks.append(cid)
    if len(sinks) >= 2:
        return "two_sink_components", [[list(x) for x in order[c][:3]] for c in sinks[:3]]
    return None, None


def layer_c_rooted_matching(nodes, edges, node_cap=200_000):
    """Hall 단사 배정 + 뿌리 연결성(사이클 없음)을 동시에 만족하는 배정이 있는가.

    각 의무는 유입 1, 각 슬롯은 유출 ≤1 이므로 이는 뿌리에서 시작하는 Hamilton 경로와 같다.
    완전 탐색이 캡을 넘으면 **UNKNOWN** 을 돌려준다 (UNSAT 이라 부르지 않는다).
    """
    incoming = defaultdict(list)
    for x, ys in edges.items():
        for y in ys:
            incoming[y].append(x)
    remaining = set(nodes)
    st = {"n": 0, "complete": True}

    def rec(current, remaining):
        if not remaining:
            return True
        st["n"] += 1
        if st["n"] > node_cap:
            st["complete"] = False
            return False
        options = [y for y in edges.get(current, ()) if y in remaining]
        if not options:
            return False
        # MRV: 남은 유입 후보가 가장 적은 쪽부터
        options.sort(key=lambda y: sum(1 for p in incoming[y] if p in remaining or p == current))
        for y in options:
            remaining.discard(y)
            if rec(y, remaining):
                return True
            remaining.add(y)
        return False

    ok = rec(("root",), remaining)
    if ok:
        return "SAT", st["n"]
    return ("UNSAT" if st["complete"] else "UNKNOWN"), st["n"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("layers", "control"))
    ap.add_argument("--archive", default=str(ARCHIVE))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--layer-c", action="store_true", help="층 C 까지 실행 (느릴 수 있음)")
    ap.add_argument("--out")
    args = ap.parse_args()
    geo, hex_words, states, covers, hall = load(Path(args.archive))
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])
    cover_by = {(c["sid"], c["cover_id"]): c for c in covers}
    alive = [s for s in states if passing.get(s["sid"])]
    if args.limit:
        alive = alive[:args.limit]
    print(f"Hall-SAT states: {len(alive)} | passing pairs: "
          f"{sum(len(passing[s['sid']]) for s in alive)}", flush=True)

    agg = Counter()
    pair_stats = Counter()
    rows = []
    t0 = time.time()
    for i, s in enumerate(alive):
        verdicts = []
        for cid in passing[s["sid"]]:
            cover = cover_by[(s["sid"], cid)]["orbits"]
            nodes, edges, cand = obligation_graph(s, cover, geo, hex_words)
            unreachable, seen = layer_a_reachable(nodes, edges)
            closed = layer_b_closed_subset(nodes, edges)
            assert set(closed) == set(unreachable), (s["sid"], cid)
            if unreachable:
                verdicts.append(("A_UNREACHABLE", cid, len(unreachable),
                                 [list(x) for x in unreachable[:6]]))
                pair_stats["A_fail"] += 1
                continue
            reason, sample = layer_b2_terminal_bounds(nodes, edges)
            if reason:
                verdicts.append((f"B2_{reason}", cid, 0, sample))
                pair_stats[f"B2_{reason}"] += 1
                continue
            if args.layer_c:
                v, n = layer_c_rooted_matching(nodes, edges)
                pair_stats[f"C_{v}"] += 1
                verdicts.append((f"C_{v}", cid, 0, None))
            else:
                pair_stats["A_pass"] += 1
                verdicts.append(("A_PASS", cid, 0, None))
        kinds = {v[0] for v in verdicts}
        if "A_PASS" in kinds or "C_SAT" in kinds:
            state_verdict = "SAT"
        elif "C_UNKNOWN" in kinds:
            state_verdict = "UNKNOWN"
        else:
            state_verdict = "UNSAT"
        agg[state_verdict] += 1
        rows.append(dict(sid=s["sid"], root=s["root"], c=s["c"],
                         passing_covers=len(passing[s["sid"]]),
                         verdict=state_verdict,
                         certificates=[dict(kind=v[0], cover_id=v[1], size=v[2], sample=v[3])
                                       for v in verdicts if v[0] != "A_PASS"][:4]))
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(alive)} {dict(agg)} {time.time()-t0:.0f}s", flush=True)
    result = dict(states=len(alive), aggregate=dict(agg), pair_stats=dict(pair_stats),
                  layer_c_enabled=bool(args.layer_c), seconds=round(time.time() - t0),
                  rows=rows)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     ensure_ascii=False, indent=1)[:2000])
    if args.out:
        json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
