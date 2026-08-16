#!/usr/bin/env python3
"""라운드 97 — **D4 강제-간선 전파** (그리고 라운드-96 D1 의 저장소 내 재현).

배경.  라운드 93–96 에서 확립된 것만 쓴다.  genuine 완성은 `{root} ∪ 의무` 위의 **뿌리 달린
유향 Hamilton 경로**다 (pass 하나 ↔ 의무 하나, 진입 port 1개 등록, 발사 1회).  그 경로에서

    * ROOT: 유입 0, 유출 1
    * terminal 아닌 의무: 유입 1, 유출 1
    * terminal(정확히 1개): 유입 1, 유출 0

전파 규칙 — **전부 위 차수 사실에서 직접 나오며 휴리스틱 삭제는 하나도 쓰지 않는다** (§8).

    R1  |in(v)| = 1 이면 그 간선은 **강제**다.  v 는 유입이 정확히 1 이어야 하므로 terminal
        선택과 무관하게 성립한다.
    R2  강제 간선 `u→v` 가 정해지면 `u` 의 다른 유출과 `v` 의 다른 유입을 삭제한다.
        근거: `u` 는 유출 ≤ 1, `v` 는 유입 = 1.  삭제마다 인증서(어느 강제 간선 때문인지)가
        있다.
    R3  |in(v)| = 0 → 모순.
    R4  유출 0 인 정점이 2개 이상 → 모순 (terminal 은 전역에서 **정확히 하나**; 이것이 §3 이
        요구한 '전역 terminal 허용량' 방식이다).  ROOT 의 유출이 0 이어도 모순.
    R5  강제 간선들이 ROOT 를 포함하지 않는 유향 사이클을 이루면 모순 — 경로는 정점을
        재방문하지 않는다.  (`len(cycle) < |의무|` 인 **진부분** 사이클만 쓴다.)

층 (§11).

    D4a = R1–R5 전파.
    D4b = D4a 통과 후 **강제 사슬을 축약**하고 라운드-96 의 D1 분리자 조건을 다시 건다.
          축약이 건전한 이유: 어떤 rooted Hamilton 경로도 강제 간선을 연속으로 쓰므로 축약
          그래프 `G'` 에도 rooted Hamilton 경로가 존재해야 하고, 따라서
          `c(U(G') − S) ≤ |S| + 1` 이 그대로 필요조건이다.
    D1  = 라운드 96 의 `c(U(G) − v) ≤ 2` (여기서는 잠정 폐쇄 4개의 **재현용**으로만 둔다).

상태 판정은 언제나 **모든 잔여 cover 가 FAIL** 일 때만 UNSAT 이다 (`any` 금지).

사용법:
    python3 src/probe_rr_forced_edge.py control            # §9 양성 대조
    python3 src/probe_rr_forced_edge.py d1                 # 라운드-96 D1 재현
    python3 src/probe_rr_forced_edge.py d4a                # D4a 전수
    python3 src/probe_rr_forced_edge.py d4b                # D4b 전수
    python3 src/probe_rr_forced_edge.py export             # 원장 산출
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_rr_path_connectivity as PC  # noqa: E402

ROOTV = ("root",)
OUT = Path(__file__).resolve().parent.parent / "outputs"


# --------------------------------------------------------------------------- 전파

def propagate(nodes, edges):
    """R1–R5.  성공하면 `(out, forced)`, 모순이면 `(None, (이유, 인증서))`."""
    verts = [ROOTV] + list(nodes)
    node_set = set(nodes)
    out = {v: {y for y in edges.get(v, ()) if y in node_set} for v in verts}
    inn = {v: set() for v in verts}
    for v in verts:
        for y in out[v]:
            inn[y].add(v)
    inn[ROOTV] = set()
    forced: dict = {}
    changed = True
    while changed:
        changed = False
        for v in nodes:
            if not inn[v]:
                return None, ("no_incoming", [list(v)])
            if len(inn[v]) == 1:
                u = next(iter(inn[v]))
                if forced.get(u) == v:
                    continue
                if u in forced and forced[u] != v:
                    return None, ("source_two_successors", [list(u)])
                forced[u] = v
                changed = True
                for w in list(out[u]):          # R2
                    if w != v:
                        out[u].discard(w)
                        inn[w].discard(u)
                for z in list(inn[v]):          # R2
                    if z != u:
                        inn[v].discard(z)
                        out[z].discard(v)
        dead = [v for v in verts if not out[v]]
        if ROOTV in dead:
            return None, ("root_no_successor", None)
        if len(dead) >= 2:
            return None, ("two_terminals", [list(x) for x in dead[:4]])
    seen = set()
    for start in list(forced):                  # R5
        if start in seen:
            continue
        path, x = [], start
        while x in forced and x not in path:
            path.append(x)
            x = forced[x]
        if x in path:
            cycle = path[path.index(x):]
            if ROOTV not in cycle and len(cycle) < len(nodes):
                return None, ("forced_proper_subtour", [list(y) for y in cycle[:8]])
        seen.update(path)
    return (out, forced), None


def d4a_verdict(nodes, edges):
    res, bad = propagate(nodes, edges)
    if bad is not None:
        return "FAIL", bad[0], bad[1]
    return "PASS", None, None


# --------------------------------------------------------------------------- 분리자

def undirected(nodes, edges):
    verts = [ROOTV] + list(nodes)
    ok = set(verts)
    adj = {v: set() for v in verts}
    for x in verts:
        for y in edges.get(x, ()):
            if y in ok:
                adj[x].add(y)
                adj[y].add(x)
    return verts, adj


def components(verts, adj, removed):
    idx = {}
    for v in verts:
        if v not in removed:
            idx[v] = len(idx)
    par = list(range(len(idx)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for v, i in idx.items():
        for w in adj[v]:
            if w in idx:
                ra, rb = find(i), find(idx[w])
                if ra != rb:
                    par[ra] = rb
    return len({find(i) for i in idx.values()})


def d1_verdict(nodes, edges):
    """라운드 96: 어떤 정점 하나를 빼도 성분이 2 이하여야 한다."""
    verts, adj = undirected(nodes, edges)
    for v in verts:
        c = components(verts, adj, {v})
        if c > 2:
            return "FAIL", v, c
    return "PASS", None, None


def d4b_verdict(nodes, edges):
    """D4a 통과 후 강제 사슬 축약 → D1."""
    res, bad = propagate(nodes, edges)
    if bad is not None:
        return "FAIL", bad[0], bad[1]
    out, forced = res
    rep = {v: v for v in [ROOTV] + list(nodes)}

    def find(a):
        while rep[a] != a:
            rep[a] = rep[rep[a]]
            a = rep[a]
        return a

    for u, v in forced.items():
        ra, rb = find(u), find(v)
        if ra == rb:
            continue
        if rb == ROOTV:
            rep[ra] = rb
        else:
            rep[rb] = ra
    groups = defaultdict(list)
    for v in [ROOTV] + list(nodes):
        groups[find(v)].append(v)
    if len(groups) <= 2:
        return "PASS", None, None
    rootg = find(ROOTV)
    nodes2 = [g for g in groups if g != rootg]
    edges2 = defaultdict(set)
    for x in [ROOTV] + list(nodes):
        for y in out.get(x, ()):
            a, b = find(x), find(y)
            if a != b:
                edges2[a].add(b)
    ren = {rootg: ROOTV}
    edges2b = {ren.get(k, k): {ren.get(y, y) for y in vs} for k, vs in edges2.items()}
    state, sep, c = d1_verdict(nodes2, edges2b)
    if state == "FAIL":
        return "FAIL", "contracted_separator", {
            "separator": ["root"] if sep == ROOTV else list(sep),
            "components": c,
            "contracted_nodes": len(nodes2),
        }
    return "PASS", None, None


LAYERS = {"d1": d1_verdict, "d4a": d4a_verdict, "d4b": d4b_verdict}


# --------------------------------------------------------------------------- 잔여 쌍

def surviving_pairs(geo, hexw, states, covers, hall):
    """라운드 94/95 의 A+B2 생존 (상태, cover) 쌍 — 아카이브에서 직접 재계산."""
    by_id = {s["sid"]: s for s in states}
    cov = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])
    for sid, cids in passing.items():
        keep = []
        for cid in cids:
            nodes, edges, _ = PC.obligation_graph(by_id[sid], cov[(sid, cid)]["orbits"], geo, hexw)
            unreachable, _ = PC.layer_a_reachable(nodes, edges)
            if unreachable:
                continue
            why, _cert = PC.layer_b2_terminal_bounds(nodes, edges)
            if why:
                continue
            keep.append((cid, nodes, edges))
        if keep:
            yield sid, by_id[sid], keep


# --------------------------------------------------------------------------- 대조

def random_rooted_hamilton(rng, n, extra_ratio=3):
    """명시적 rooted Hamilton 경로를 **포함**하는 그래프 — 거부되면 오탐이다."""
    order = [ROOTV] + [("v", i) for i in range(n)]
    rng.shuffle(order[1:])
    nodes = [v for v in order if v != ROOTV]
    edges = defaultdict(set)
    for a, b in zip(order, order[1:]):
        edges[a].add(b)
    pool = [v for v in order]
    for _ in range(extra_ratio * n):
        a, b = rng.choice(pool), rng.choice(pool)
        if a != b and b != ROOTV:
            edges[a].add(b)
    return nodes, {k: set(v) for k, v in edges.items()}


def run_control(trials=1200, seed=97):
    rng = random.Random(seed)
    false_rej = Counter()
    for t in range(trials):
        n = 5 + t % 36
        nodes, edges = random_rooted_hamilton(rng, n, extra_ratio=t % 4)
        for name, fn in LAYERS.items():
            if fn(nodes, edges)[0] == "FAIL":
                false_rej[name] += 1
    return {"trials": trials, "false_rejections": {k: false_rej.get(k, 0) for k in LAYERS}}


# --------------------------------------------------------------------------- 스윕

def sweep(layer, geo, hexw, states, covers, hall, progress=1500):
    fn = LAYERS[layer]
    pair = Counter()
    statev = Counter()
    rsplit = defaultdict(Counter)
    fails = []
    t0 = time.time()
    for i, (sid, st, keep) in enumerate(surviving_pairs(geo, hexw, states, covers, hall)):
        per = []
        for cid, nodes, edges in keep:
            verdict, why, cert = fn(nodes, edges)
            pair[verdict] += 1
            if verdict == "FAIL":
                pair[why if isinstance(why, str) else "separator"] += 1
            per.append((cid, verdict, why, cert))
        all_fail = all(p[1] == "FAIL" for p in per)
        sv = "UNSAT" if all_fail else "SAT"
        statev[sv] += 1
        rsplit[st["r"]][sv] += 1
        if all_fail:
            fails.append({
                "sid": sid, "root": st.get("root"), "c": st.get("c"), "r": st["r"],
                "layer": layer,
                "per_cover": [{
                    "cover_id": p[0], "pair_verdict": "FAIL",
                    "contradiction": p[2] if isinstance(p[2], str) else "separator",
                    "certificate": p[3],
                } for p in per],
                "state_verdict": "UNSAT",
                "all_surviving_covers_fail": True,
            })
        if progress and (i + 1) % progress == 0:
            print(f"  {i+1} pair={dict(pair)} {time.time()-t0:.0f}s", flush=True)
    return {"layer": layer, "pair": dict(pair), "state": dict(statev),
            "r": {str(k): dict(v) for k, v in sorted(rsplit.items())},
            "fails": fails, "seconds": round(time.time() - t0)}


# --------------------------------------------------------------------------- 파일럿

def hamilton_pilot(nodes, edges, node_cap=200_000):
    """정확 rooted Hamilton 경로 DFS — **캡은 UNSAT 이 아니다**.

    가지치기는 전부 건전한 필요조건이다: (i) 남은 의무가 현재 정점에서 도달 가능해야 한다,
    (ii) 남은 부분그래프에서 유출 0 인 정점은 최대 1개다.
    반환: `("SAT", 노드수)` / `("UNSAT", 노드수)` / `("UNKNOWN", 캡)`.
    """
    node_set = set(nodes)
    adj = {v: [y for y in edges.get(v, ()) if y in node_set] for v in [ROOTV] + list(nodes)}
    remaining = set(nodes)
    visited = 0
    counter = [0]

    def prune(cur):
        seen = {cur}
        stack = [cur]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y in remaining and y not in seen:
                    seen.add(y)
                    stack.append(y)
        if len(seen - {cur}) < len(remaining):
            return True
        dead = 0
        for v in remaining:
            if not any(y in remaining and y != v for y in adj[v]):
                dead += 1
                if dead >= 2:
                    return True
        return False

    def dfs(cur):
        counter[0] += 1
        if counter[0] > node_cap:
            raise TimeoutError
        if not remaining:
            return True
        if prune(cur):
            return False
        for y in adj[cur]:
            if y in remaining:
                remaining.discard(y)
                if dfs(y):
                    return True
                remaining.add(y)
        return False

    sys.setrecursionlimit(10_000)
    try:
        ok = dfs(ROOTV)
    except TimeoutError:
        return "UNKNOWN", node_cap
    except RecursionError:
        return "UNKNOWN", counter[0]
    return ("SAT" if ok else "UNSAT"), counter[0]


def run_pilot_control(trials=300, seed=971, node_cap=3_000_000):
    """명시적 Hamilton 경로를 가진 그래프에서 DFS 가 **UNSAT 을 내면 안 된다**."""
    rng = random.Random(seed)
    out = Counter()
    for t in range(trials):
        nodes, edges = random_rooted_hamilton(rng, 5 + t % 36, extra_ratio=t % 4)
        out[hamilton_pilot(nodes, edges, node_cap)[0]] += 1
    return {"trials": trials, "verdicts": dict(out), "false_unsat": out["UNSAT"]}


def run_pilot(geo, hexw, states, covers, hall, limit=60, node_cap=200_000):
    verdicts = Counter()
    rows = []
    t0 = time.time()
    seen = 0
    for sid, st, keep in surviving_pairs(geo, hexw, states, covers, hall):
        if len(keep) != 1:          # UNIQUE_AB 만
            continue
        seen += 1
        if seen > limit:
            break
        cid, nodes, edges = keep[0]
        t1 = time.time()
        verdict, cost = hamilton_pilot(nodes, edges, node_cap)
        verdicts[verdict] += 1
        rows.append({"sid": sid, "cover_id": cid, "obligations": len(nodes),
                     "verdict": verdict, "nodes_explored": cost,
                     "seconds": round(time.time() - t1, 2)})
        print(f"  {seen} {sid[:8]} {verdict} {cost} {time.time()-t1:.1f}s", flush=True)
    return {"limit": limit, "node_cap": node_cap, "verdicts": dict(verdicts),
            "rows": rows, "seconds": round(time.time() - t0)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["control", "pilot-control", "d1", "d4a", "d4b",
                                     "export", "pilot"])
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--node-cap", type=int, default=200_000)
    ap.add_argument("--out", default=str(OUT / "rr_forced_edge_claude.json"))
    args = ap.parse_args()

    if args.mode == "control":
        print(json.dumps(run_control(), ensure_ascii=False, indent=1))
        return
    if args.mode == "pilot-control":
        print(json.dumps(run_pilot_control(), ensure_ascii=False, indent=1))
        return

    geo, hexw, states, covers, hall = PC.load()
    if args.mode == "pilot":
        res = run_pilot(geo, hexw, states, covers, hall, args.limit, args.node_cap)
        Path(OUT / "rr_forced_edge_pilot_claude.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({k: v for k, v in res.items() if k != "rows"},
                         ensure_ascii=False, indent=1))
        return
    if args.mode in ("d1", "d4a", "d4b"):
        res = sweep(args.mode, geo, hexw, states, covers, hall)
        print(json.dumps({k: v for k, v in res.items() if k != "fails"},
                         ensure_ascii=False, indent=1))
        print("state_closed:", len(res["fails"]))
        return

    report = {"round": 97, "control": run_control()}
    for layer in ("d1", "d4a", "d4b"):
        print(f"[{layer}]", flush=True)
        report[layer] = sweep(layer, geo, hexw, states, covers, hall)
    sets = {k: {f["sid"] for f in report[k]["fails"]} for k in ("d1", "d4a", "d4b")}
    report["sets"] = {
        "d1_only": sorted(sets["d1"] - sets["d4b"]),
        "d4b_only": sorted(sets["d4b"] - sets["d1"]),
        "intersection": sorted(sets["d1"] & sets["d4b"]),
        "union": sorted(sets["d1"] | sets["d4b"]),
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    ledger = OUT / "rr_forced_edge_ledger.jsonl.gz"
    with gzip.open(ledger, "wt") as fh:
        fh.write(json.dumps({
            "schema": "rr_forced_edge/1", "round": 97,
            "layers": {
                "D4a": "R1–R5 강제-간선 전파 (유일 유입 강제, 경쟁 간선 삭제, 유입 0, terminal 2개, ROOT 없는 진부분 강제 사이클)",
                "D4b": "D4a + 강제 사슬 축약 후 c(U(G')-v) <= 2",
                "D1": "라운드 96 c(U(G)-v) <= 2 (재현)",
            },
            "state_rule": "state_closed = 모든 잔여 cover 가 FAIL (any 금지)",
            "reconstruction": "그래프는 outputs/rr_port_path_hall_archive 에서 결정적으로 재구성",
            "control": report["control"],
            "ledger": "감사 잔여 4,802 변경 없음; 이 폐쇄는 전부 잠정",
        }, ensure_ascii=False) + "\n")
        for layer in ("d1", "d4a", "d4b"):
            for row in report[layer]["fails"]:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("wrote", args.out, "and", ledger)
    print(json.dumps({k: {kk: vv for kk, vv in report[k].items() if kk != "fails"}
                      for k in ("d1", "d4a", "d4b")}, ensure_ascii=False, indent=1))
    print({k: len(v) for k, v in report["sets"].items()})


if __name__ == "__main__":
    main()
