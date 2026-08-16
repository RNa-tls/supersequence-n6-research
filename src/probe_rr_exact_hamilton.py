#!/usr/bin/env python3
"""라운드 98 — 정확 rooted Hamilton: **난이도 층화 → 값싼 층만 소진**.

라운드 97 파일럿에서 정확 탐색이 처음으로 UNSAT 을 완전 소진으로 냈다(Codex 가 역방향
suffix DFS 와 정방향 prefix DFS 두 가지로 독립 확인). 이 모듈은 그것을 무차별 스윕으로
확대하지 않고, 먼저 **탐색 비용을 예측하는 값싼 구조 특징**을 재고 예측이 싼 층만 소진한다.

용어.

    UNIQUE_PATH  현재 감사된 pre-Hamilton 조건 (Hall · 층 A · B2 · D1 · D4b) 을 통과하는
                 cover 가 **정확히 1개**인 상태.  D1/D4b 는 (상태, cover) 쌍 판정이므로
                 cover 를 개별적으로 제거하며, 그 결과 이전에 다중 cover 였던 상태가 새로
                 UNIQUE_PATH 가 될 수 있다.

건전성 규칙.

    * 캡 도달은 **UNKNOWN** 이다.  절대 UNSAT 으로 세지 않는다.
    * UNSAT 은 **완전 소진**일 때만이다.
    * 상태 폐쇄는 **모든** 잔여 cover 가 UNSAT 일 때만이다 — UNIQUE_PATH 는 그 특수한 경우.
    * 가지치기는 전부 필요조건이다: (i) 남은 의무가 현재 정점에서 도달 가능, (ii) 남은
      부분그래프에서 유출 0 인 정점 ≤ 1, (iii) 실패한 `(현재 정점, 남은 집합)` 재방문
      금지(정확한 상태 키이므로 memo 는 건전하다).

사용법:
    python3 src/probe_rr_exact_hamilton.py census      # §1 UNIQUE_PATH 재계수 + §3 특징
    python3 src/probe_rr_exact_hamilton.py pilot12     # §2 12개 파일럿 상태 특징 보존
    python3 src/probe_rr_exact_hamilton.py calibrate   # §4 층화 표본, 캡 상승
    python3 src/probe_rr_exact_hamilton.py subtour     # §8 subtour-cut 대안 비교
    python3 src/probe_rr_exact_hamilton.py sweep       # §9 easy 층 소진
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import statistics
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_rr_path_connectivity as PC  # noqa: E402
import probe_rr_forced_edge as F  # noqa: E402

ROOTV = F.ROOTV
OUT = Path(__file__).resolve().parent.parent / "outputs"
SOLVER_VERSION = "claude-r98-bitset-dfs/1"

# 라운드 97 파일럿에서 완전 소진 UNSAT 으로 확인되고 Codex 가 독립 확인한 상태 (§13).
PILOT_UNSAT = [
    "6273274c", "cca008e3", "7921d0cb", "714d11e1",
]
# 3M 캡에 걸린 여덟 개 — **UNKNOWN**, 폐쇄 아님 (§11 의 hard control).
PILOT_UNKNOWN = [
    "3189b5eb", "bed179a1", "72f19d2f", "77fbaf89",
    "c1dd5467", "7bb6b67c", "02eafeaa", "a34d6499",
]


# --------------------------------------------------------------------- 잔여 재계산

def prehamilton_pairs(geo, hexw, states, covers, hall, skip_closed=True):
    """Hall · A · B2 · D1 · D4b 를 **cover 단위**로 통과한 쌍만 내보낸다."""
    by_id = {s["sid"]: s for s in states}
    cov = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])
    for sid in sorted(passing):
        if skip_closed and any(sid.startswith(p) for p in PILOT_UNSAT):
            continue
        keep = []
        for cid in sorted(passing[sid]):
            nodes, edges, _ = PC.obligation_graph(by_id[sid], cov[(sid, cid)]["orbits"], geo, hexw)
            unreachable, _ = PC.layer_a_reachable(nodes, edges)
            if unreachable:
                continue
            why, _c = PC.layer_b2_terminal_bounds(nodes, edges)
            if why:
                continue
            if F.d1_verdict(nodes, edges)[0] == "FAIL":
                continue
            if F.d4b_verdict(nodes, edges)[0] == "FAIL":
                continue
            keep.append((cid, nodes, edges))
        if keep:
            yield sid, by_id[sid], keep


# --------------------------------------------------------------------- 비트셋 그래프

def to_bitset(nodes, edges):
    """`(m, out, inn, root_out, index, order)` — 의무는 0..m-1, ROOT 는 별도."""
    order = list(nodes)
    index = {v: i for i, v in enumerate(order)}
    m = len(order)
    out = [0] * m
    inn = [0] * m
    for v in order:
        for y in edges.get(v, ()):
            if y in index:
                out[index[v]] |= 1 << index[y]
                inn[index[y]] |= 1 << index[v]
    root_out = 0
    for y in edges.get(ROOTV, ()):
        if y in index:
            root_out |= 1 << index[y]
    return m, out, inn, root_out, index, order


def graph_hash(m, out, root_out):
    h = hashlib.sha256()
    h.update(f"{m}|{root_out}".encode())
    for x in out:
        h.update(f"|{x}".encode())
    return h.hexdigest()


def _bits(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


# --------------------------------------------------------------------- 특징 (§3, §7)

def features(nodes, edges):
    m, out, inn, root_out, index, order = to_bitset(nodes, edges)
    e = sum(bin(x).count("1") for x in out) + bin(root_out).count("1")
    ind = [bin(x).count("1") for x in inn]
    outd = [bin(x).count("1") for x in out]

    # D4 강제 사슬
    res, bad = F.propagate(nodes, edges)
    chains = {"forced_edges": 0, "chains": 0, "max_chain": 0}
    if bad is None:
        forced = res[1]
        chains["forced_edges"] = len(forced)
        targets = set(forced.values())
        starts = [u for u in forced if u not in targets]
        lengths = []
        for st in starts:
            n, x = 0, st
            seen = set()
            while x in forced and x not in seen:
                seen.add(x)
                x = forced[x]
                n += 1
            lengths.append(n)
        chains["chains"] = len(lengths)
        chains["max_chain"] = max(lengths) if lengths else 0

    # 절단점 (무향)
    verts, adj = F.undirected(nodes, edges)
    base = F.components(verts, adj, set())
    artic = sum(1 for v in verts if F.components(verts, adj, {v}) > base)

    # SCC (유향, ROOT 포함)
    sccs = _scc([ROOTV] + list(nodes), edges)

    # ROOT 로부터의 BFS 레벨 = 값싼 frontier 폭 (§7)
    level, cur, seen = [], {ROOTV}, {ROOTV}
    while cur:
        nxt = set()
        for x in cur:
            for y in edges.get(x, ()):
                if y not in seen and y in index:
                    seen.add(y)
                    nxt.add(y)
        if nxt:
            level.append(len(nxt))
        cur = nxt

    return {
        "m": m, "edges": e, "density": round(e / max(m * (m - 1), 1), 5),
        "indeg_min": min(ind) if ind else 0, "indeg_mean": round(sum(ind) / max(m, 1), 3),
        "indeg_median": statistics.median(ind) if ind else 0,
        "outdeg_min": min(outd) if outd else 0, "outdeg_mean": round(sum(outd) / max(m, 1), 3),
        "outdeg_median": statistics.median(outd) if outd else 0,
        "n_indeg1": sum(1 for x in ind if x == 1), "n_outdeg1": sum(1 for x in outd if x == 1),
        "n_outdeg0": sum(1 for x in outd if x == 0),
        "root_outdeg": bin(root_out).count("1"),
        "forced": chains,
        "articulation": artic,
        "scc_count": len(sccs), "scc_max": max(len(s) for s in sccs) if sccs else 0,
        "scc_nontrivial": sum(1 for s in sccs if len(s) > 1),
        "bfs_levels": len(level), "bfs_min_level": min(level) if level else 0,
        "bfs_max_level": max(level) if level else 0,
        "reach_all": len(seen) == m + 1,
    }


def _scc(verts, edges):
    index, low, on, stack, comps = {}, {}, set(), [], []
    counter = [0]
    for root in verts:
        if root in index:
            continue
        work = [(root, iter(edges.get(root, ())))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
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
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == u:
                        break
                comps.append(comp)
    return comps


# --------------------------------------------------------------------- 정확 탐색 (§6)

def solve(nodes, edges, node_cap=200_000, memo_cap=1_500_000, want_path=True):
    """비트셋 rooted Hamilton DFS.  반환 `(verdict, stats, path)`.

    verdict ∈ {SAT, UNSAT, UNKNOWN}.  UNSAT 은 **완전 소진**, UNKNOWN 은 캡이다.
    """
    m, out, inn, root_out, index, order = to_bitset(nodes, edges)
    full = (1 << m) - 1
    stats = Counter()
    memo = set()
    path = []

    def reachable(cur_mask, rem):
        seen = cur_mask
        frontier = cur_mask
        while frontier:
            nxt = 0
            for i in _bits(frontier):
                nxt |= out[i]
            nxt &= rem & ~seen
            seen |= nxt
            frontier = nxt
        return seen & rem

    def dfs(cur, rem):
        stats["nodes"] += 1
        if stats["nodes"] > node_cap:
            raise TimeoutError
        if not rem:
            return True
        key = (cur, rem)
        if key in memo:
            stats["prune_memo"] += 1
            return False
        cand = out[cur] & rem
        if not cand:
            stats["prune_dead_end"] += 1
            memo.add(key) if len(memo) < memo_cap else None
            return False
        if reachable(1 << cur, rem) != rem:
            stats["prune_reach"] += 1
            if len(memo) < memo_cap:
                memo.add(key)
            return False
        dead = 0
        for i in _bits(rem):
            if not out[i] & (rem & ~(1 << i)):
                dead += 1
                if dead >= 2:
                    stats["prune_two_terminals"] += 1
                    if len(memo) < memo_cap:
                        memo.add(key)
                    return False
        nxts = sorted(_bits(cand), key=lambda y: bin(out[y] & rem).count("1"))
        for y in nxts:
            path.append(y)
            if dfs(y, rem & ~(1 << y)):
                return True
            path.pop()
        if len(memo) < memo_cap:
            memo.add(key)
        return False

    sys.setrecursionlimit(20_000)
    t0 = time.time()
    try:
        stats["nodes"] += 1
        cand = sorted(_bits(root_out), key=lambda y: bin(out[y] & full).count("1"))
        ok = False
        for y in cand:
            path.append(y)
            if dfs(y, full & ~(1 << y)):
                ok = True
                break
            path.pop()
        verdict = "SAT" if ok else "UNSAT"
    except TimeoutError:
        verdict = "UNKNOWN"
    except RecursionError:
        verdict = "UNKNOWN"
        stats["recursion"] = 1
    stats["seconds"] = round(time.time() - t0, 2)
    stats["memo"] = len(memo)
    witness = None
    if verdict == "SAT" and want_path:
        witness = [list(order[i]) for i in path]
    return verdict, dict(stats), witness


def solve_reverse(nodes, edges, node_cap=200_000, want_path=False):
    """역방향(suffix) 정식화 — 독립 노드 계수를 얻기 위한 **다른 탐색**.

    `G` 를 뒤집고 가상 시작점 `S`(모든 의무로 가는 간선)를 붙인다.  `G` 에서 ROOT 의 유입이
    0 이므로 `G^R` 에서 ROOT 의 유출이 0 이고, 따라서 ROOT 는 자동으로 마지막이 된다.
    즉 `S` 에서 출발해 의무 전체와 ROOT 를 지나는 Hamilton 경로 ⟺ 원래 문제의 해.
    """
    ORIG = ("orig_root",)                      # ROOT 를 평범한 정점으로 강등
    ren = lambda v: ORIG if v == ROOTV else v  # noqa: E731
    rev = defaultdict(set)
    for x, ys in edges.items():
        for y in ys:
            rev[ren(y)].add(ren(x))
    rnodes = [ren(v) for v in nodes] + [ORIG]
    redges = {v: set(rev.get(v, ())) for v in rnodes}
    redges[ROOTV] = set(ren(v) for v in nodes)   # 가상 시작점 = 모든 terminal 후보
    verdict, stats, rpath = solve(rnodes, redges, node_cap=node_cap, want_path=want_path)
    path = None
    if verdict == "SAT" and rpath is not None:
        # 역방향 경로 S -> t -> ... -> ORIG 를 뒤집어 원래 방향으로 되돌린다.
        seq = [tuple(v) for v in rpath]
        assert seq[-1] == ("orig_root",), seq[-1]
        path = [list(v) for v in reversed(seq[:-1])]
    return verdict, stats, path


# ------------------------------------------------------- subtour-cut 대안 (§8)

def subtour_solve(nodes, edges, iter_cap=20_000):
    """배정 + subtour 분기 (Little 식, 외부 solver 없음).

    successor 배정 = `{ROOT} ∪ 의무` → `의무 ∪ {terminal 더미}` 의 완전 매칭.  선택 간선은
    (ROOT 에서 나온 경로) + (사이클들) 로 분해되므로, 사이클이 없으면 rooted Hamilton 경로다.
    사이클이 있으면 **그 사이클의 어떤 간선은 반드시 빠져야 하므로** 간선별로 분기한다 —
    완전(complete)하고 건전하다.
    """
    m, out, inn, root_out, index, order = to_bitset(nodes, edges)
    DUMMY = m
    src = list(range(m)) + [m]          # 의무들 + ROOT(=m)
    stats = Counter()

    def match(banned):
        """Hopcroft–Karp 없이 단순 증가경로 매칭 (m ~ 108)."""
        adj = []
        for s in src:
            if s == m:
                adj.append([y for y in _bits(root_out) if (s, y) not in banned])
            else:
                adj.append([y for y in _bits(out[s]) if (s, y) not in banned]
                           + ([DUMMY] if (s, DUMMY) not in banned else []))
        to_src = {}
        def aug(s, seen):
            for t in adj[src.index(s)]:
                if t in seen:
                    continue
                seen.add(t)
                if t not in to_src or aug(to_src[t], seen):
                    to_src[t] = s
                    return True
            return False
        for s in src:
            if not aug(s, set()):
                return None
        return {v: k for k, v in to_src.items()}

    def search(banned, depth):
        stats["iterations"] += 1
        if stats["iterations"] > iter_cap:
            raise TimeoutError
        succ = match(banned)
        if succ is None:
            stats["infeasible"] += 1
            return None
        # 사이클 검출 (ROOT 경로 밖)
        onpath = set()
        x = succ[m]
        while x != DUMMY:
            onpath.add(x)
            x = succ[x]
        cyc_nodes = [v for v in range(m) if v not in onpath]
        if not cyc_nodes:
            return succ
        start = cyc_nodes[0]
        cycle, x = [], start
        while x not in cycle:
            cycle.append(x)
            x = succ[x]
        cycle = cycle[cycle.index(x):]
        stats["cuts"] += 1
        for v in cycle:
            got = search(banned | {(v, succ[v])}, depth + 1)
            if got is not None:
                return got
        return None

    sys.setrecursionlimit(20_000)
    t0 = time.time()
    try:
        succ = search(frozenset(), 0)
        verdict = "SAT" if succ else "UNSAT"
    except TimeoutError:
        verdict, succ = "UNKNOWN", None
    except RecursionError:
        verdict, succ = "UNKNOWN", None
    stats["seconds"] = round(time.time() - t0, 2)
    witness = None
    if succ:
        witness, x = [], succ[m]
        while x != DUMMY:
            witness.append(list(order[x]))
            x = succ[x]
    return verdict, dict(stats), witness


# --------------------------------------------------------------------- 모드

def _load():
    return PC.load()


def cmd_census(args):
    geo, hexw, states, covers, hall = _load()
    hist = Counter()
    pairs = 0
    rows = []
    t0 = time.time()
    for i, (sid, st, keep) in enumerate(prehamilton_pairs(geo, hexw, states, covers, hall)):
        hist[len(keep)] += 1
        pairs += len(keep)
        row = {"sid": sid, "root": st.get("root"), "c": st.get("c"), "r": st["r"],
               "surviving_covers": [cid for cid, _n, _e in keep],
               "unique_path": len(keep) == 1}
        if len(keep) == 1:
            cid, nodes, edges = keep[0]
            row["features"] = features(nodes, edges)
            m, out, inn, root_out, _idx, _o = to_bitset(nodes, edges)
            row["graph_hash"] = graph_hash(m, out, root_out)
        rows.append(row)
        if (i + 1) % 500 == 0:
            print(f"  {i+1} states pairs={pairs} {time.time()-t0:.0f}s", flush=True)
    summary = {"round": 98, "states": len(rows), "pairs": pairs,
               "cover_histogram": dict(sorted(hist.items())),
               "unique_path": hist[1],
               "seconds": round(time.time() - t0)}
    with gzip.open(OUT / "rr_exact_hamilton_census.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"schema": "rr_exact_hamilton_census/1", **summary},
                            ensure_ascii=False) + "\n")
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def load_census():
    path = OUT / "rr_exact_hamilton_census.jsonl.gz"
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


def graphs_for(sids, geo, hexw, states, covers, hall):
    want = set(sids)
    got = {}
    for sid, st, keep in prehamilton_pairs(geo, hexw, states, covers, hall, skip_closed=False):
        short = sid[:8]
        if short in want or sid in want:
            got[short] = (sid, st, keep)
        if len(got) == len(want):
            break
    return got


GRAPHS = OUT / "rr_exact_hamilton_graphs.jsonl.gz"


def cmd_graphs(args):
    """§12 — UNIQUE_PATH 그래프를 **프론티어 재구축 없이** 풀 수 있게 통째로 내보낸다."""
    geo, hexw, states, covers, hall = _load()
    n = 0
    t0 = time.time()
    with gzip.open(GRAPHS, "wt") as fh:
        fh.write(json.dumps({
            "schema": "rr_exact_hamilton_graphs/1", "round": 98,
            "content": "Hall·층A·B2·D1·D4b 를 통과한 cover 가 정확히 1개인 상태의 의무 그래프",
            "vertex_convention": "의무는 0..m-1 (`nodes` 의 순서), ROOT 는 별도 `root_out`",
            "task": "ROOT 에서 출발해 0..m-1 을 각각 정확히 한 번 지나는 유향 경로의 존재",
        }, ensure_ascii=False) + "\n")
        for sid, st, keep in prehamilton_pairs(geo, hexw, states, covers, hall):
            if len(keep) != 1:
                continue
            cid, nodes, edges = keep[0]
            m, out, inn, root_out, index, order = to_bitset(nodes, edges)
            fh.write(json.dumps({
                "sid": sid, "cover_id": cid, "r": st["r"], "root": st.get("root"),
                "m": m, "nodes": [list(v) for v in order],
                "out": [sorted(_bits(x)) for x in out],
                "root_out": sorted(_bits(root_out)),
                "graph_hash": graph_hash(m, out, root_out),
            }, ensure_ascii=False) + "\n")
            n += 1
            if n % 200 == 0:
                print(f"  {n} graphs {time.time()-t0:.0f}s", flush=True)
    print("wrote", GRAPHS, n, "graphs", round(time.time() - t0), "s")


def load_graphs():
    with gzip.open(GRAPHS, "rt") as fh:
        json.loads(fh.readline())
        for line in fh:
            g = json.loads(line)
            nodes = [tuple(v) for v in g["nodes"]]
            edges = {nodes[i]: {nodes[j] for j in row} for i, row in enumerate(g["out"])}
            edges[ROOTV] = {nodes[j] for j in g["root_out"]}
            yield g, nodes, edges


def cmd_pilot12(args):
    """§2 — 라운드-97 파일럿 12개 상태의 난이도 데이터셋 (정방향·역방향 둘 다)."""
    geo, hexw, states, covers, hall = _load()
    got = graphs_for(PILOT_UNSAT + PILOT_UNKNOWN, geo, hexw, states, covers, hall)
    rows = []
    for short in PILOT_UNSAT + PILOT_UNKNOWN:
        if short not in got:
            rows.append({"sid_prefix": short, "error": "graph not found among survivors"})
            continue
        sid, st, keep = got[short]
        cid, nodes, edges = keep[0]
        feat = features(nodes, edges)
        fv, fs, path = solve(nodes, edges, node_cap=args.cap)
        rv, rs, _ = solve_reverse(nodes, edges, node_cap=args.cap)
        m, out, inn, root_out, _i, _o = to_bitset(nodes, edges)
        rows.append({
            "sid": sid, "cover_id": cid, "r": st["r"], "root": st.get("root"),
            "graph_hash": graph_hash(m, out, root_out),
            "surviving_covers": len(keep),
            "features": feat,
            "forward": {"verdict": fv, **fs},
            "reverse": {"verdict": rv, **rs},
            "round97_label": "UNSAT_COMPLETE" if short in PILOT_UNSAT else "UNKNOWN_CAP",
            "hamilton_path": path,
            "solver": SOLVER_VERSION, "node_cap": args.cap,
        })
        print(f"  {short} fwd={fv}/{fs['nodes']} rev={rv}/{rs['nodes']} "
              f"({fs['seconds']}s/{rs['seconds']}s)", flush=True)
    path = OUT / "rr_exact_hamilton_pilot12.json"
    path.write_text(json.dumps({"round": 98, "solver": SOLVER_VERSION,
                                "node_cap": args.cap, "rows": rows},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", path)


def solve_both(nodes, edges, cap, want_path=True):
    """역방향을 먼저(대체로 훨씬 싸다), 미결이면 정방향.  둘 다 완전 탐색이라 건전하다."""
    rv, rs, rpath = solve_reverse(nodes, edges, node_cap=cap, want_path=want_path)
    if rv != "UNKNOWN":
        return rv, {"direction": "reverse", **rs}, rpath
    fv, fs, fpath = solve(nodes, edges, node_cap=cap, want_path=want_path)
    return fv, {"direction": "forward", "reverse_nodes": rs["nodes"], **fs}, fpath


def verify_path(nodes, edges, path):
    """§5 — 보존한 순서의 **모든 간선을 원 그래프에 독립 대조**한다."""
    if path is None:
        return False
    seq = [ROOTV] + [tuple(v) for v in path]
    if len(set(seq[1:])) != len(nodes) or set(seq[1:]) != set(nodes):
        return False
    return all(b in edges.get(a, ()) for a, b in zip(seq, seq[1:]))


def cmd_sweep(args):
    """§9 — 내보낸 UNIQUE_PATH 그래프 전체에 값싼 캡으로 정확 탐색."""
    prev_undecided = None
    if args.undecided_from:
        prev = json.loads(Path(args.undecided_from).read_text())
        prev_undecided = {r["sid"] for r in prev["rows"] if r["verdict"] == "UNKNOWN"}
    rows = []
    counts = Counter()
    t0 = time.time()
    for i, (g, nodes, edges) in enumerate(load_graphs()):
        if prev_undecided is not None and g["sid"] not in prev_undecided:
            continue
        n_edges = sum(len(r) for r in g["out"]) + len(g["root_out"])
        if args.max_edges and n_edges > args.max_edges:
            continue
        verdict, stats, path = solve_both(nodes, edges, args.cap)
        counts[verdict] += 1
        row = {"sid": g["sid"], "cover_id": g["cover_id"], "r": g["r"], "root": g["root"],
               "graph_hash": g["graph_hash"], "m": g["m"], "edges": n_edges,
               "verdict": verdict, "node_cap": args.cap, "solver": SOLVER_VERSION,
               "direction": stats["direction"], "nodes": stats["nodes"],
               "seconds": stats["seconds"],
               "prune": {k: v for k, v in stats.items() if k.startswith("prune")}}
        if verdict == "SAT":
            row["hamilton_path"] = path
            row["path_verified"] = verify_path(nodes, edges, path)
        rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"  {i+1} {dict(counts)} {time.time()-t0:.0f}s", flush=True)
    res = {"round": 98, "solver": SOLVER_VERSION, "node_cap": args.cap,
           "verdicts": dict(counts), "rows": rows, "seconds": round(time.time() - t0)}
    out = OUT / (args.out or f"rr_exact_hamilton_sweep_{args.cap}.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1))
    print("wrote", out)


def _difficulty_key(f):
    """§3 이후 정해진 값싼 난이도 프록시 — verdict 를 보기 전에 고정한다."""
    return (f["edges"], -f["forced"]["forced_edges"], f["indeg_mean"])


def cmd_calibrate(args):
    """§4 — 층화 표본에 캡을 올려가며 정확 탐색."""
    header, rows = load_census()
    uniq = [r for r in rows if r["unique_path"]]
    uniq.sort(key=lambda r: _difficulty_key(r["features"]))
    n = len(uniq)
    take = args.limit
    third = take // 3
    picked = uniq[:third] + uniq[n // 2 - third // 2: n // 2 + (third - third // 2)] + uniq[-third:]
    seen, sel = set(), []
    for r in picked:
        if r["sid"] not in seen:
            seen.add(r["sid"])
            sel.append(r)
    for r in uniq:                       # §4: 여덟 개 hard control 을 반드시 포함
        if r["sid"][:8] in PILOT_UNKNOWN and r["sid"] not in seen:
            seen.add(r["sid"])
            sel.append(r)
    geo, hexw, states, covers, hall = _load()
    want = {r["sid"] for r in sel}
    graphs = {}
    for sid, st, keep in prehamilton_pairs(geo, hexw, states, covers, hall):
        if sid in want and len(keep) == 1:
            graphs[sid] = (st, keep[0])
        if len(graphs) == len(want):
            break
    caps = [100_000, 500_000, 3_000_000]
    out_rows = []
    counts = {c: Counter() for c in caps}
    t0 = time.time()
    for i, r in enumerate(sel):
        if r["sid"] not in graphs:
            continue
        st, (cid, nodes, edges) = graphs[r["sid"]]
        stratum = ("easy" if i < third else "medium" if i < 2 * third else "hard")
        if r["sid"][:8] in PILOT_UNKNOWN:
            stratum = "control_unknown"
        row = {"sid": r["sid"], "cover_id": cid, "stratum": stratum,
               "features": r["features"], "attempts": []}
        verdict = "UNKNOWN"
        for cap in caps:
            verdict, stats, path = solve(nodes, edges, node_cap=cap)
            row["attempts"].append({"cap": cap, "verdict": verdict, **stats})
            counts[cap][verdict] += 1
            if verdict != "UNKNOWN":
                if path:
                    row["hamilton_path"] = path
                for c2 in caps[caps.index(cap) + 1:]:
                    counts[c2][verdict] += 1
                break
        row["final"] = verdict
        out_rows.append(row)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(sel)} {dict(counts[caps[-1]])} {time.time()-t0:.0f}s", flush=True)
    res = {"round": 98, "solver": SOLVER_VERSION, "selected": len(out_rows),
           "caps": {str(c): dict(v) for c, v in counts.items()},
           "rows": out_rows, "seconds": round(time.time() - t0)}
    (OUT / "rr_exact_hamilton_calibration.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1))


def cmd_subtour(args):
    """§8 — 같은 그래프에서 DFS 대 subtour-cut 분기 비교."""
    geo, hexw, states, covers, hall = _load()
    got = graphs_for(PILOT_UNSAT + PILOT_UNKNOWN, geo, hexw, states, covers, hall)
    rows = []
    for short in PILOT_UNSAT + PILOT_UNKNOWN:
        if short not in got:
            continue
        sid, st, keep = got[short]
        cid, nodes, edges = keep[0]
        dv, ds, _ = solve(nodes, edges, node_cap=args.cap)
        sv, ss, spath = subtour_solve(nodes, edges, iter_cap=args.limit * 1000)
        rows.append({"sid": sid, "dfs": {"verdict": dv, **ds},
                     "subtour": {"verdict": sv, **ss},
                     "agree": dv == sv or "UNKNOWN" in (dv, sv),
                     "hamilton_path": spath})
        print(f"  {short} dfs={dv}/{ds['nodes']}n/{ds['seconds']}s "
              f"subtour={sv}/{ss.get('iterations')}it/{ss['seconds']}s", flush=True)
    (OUT / "rr_exact_hamilton_subtour.json").write_text(
        json.dumps({"round": 98, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote subtour comparison")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["census", "graphs", "pilot12", "calibrate", "subtour", "sweep"])
    ap.add_argument("--cap", type=int, default=3_000_000)
    ap.add_argument("--limit", type=int, default=150)
    ap.add_argument("--seed", type=int, default=98)
    ap.add_argument("--out", default=None)
    ap.add_argument("--undecided-from", default=None)
    ap.add_argument("--max-edges", type=int, default=0)
    args = ap.parse_args()
    {"census": cmd_census, "graphs": cmd_graphs, "pilot12": cmd_pilot12,
     "calibrate": cmd_calibrate, "subtour": cmd_subtour,
     "sweep": cmd_sweep}[args.mode](args)


if __name__ == "__main__":
    main()
