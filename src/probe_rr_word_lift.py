#!/usr/bin/env python3
"""라운드 99 — **단어 lift**: 의무 경로를 구체 단어열로 들어올리는 문제의 형식화와 정리.

라운드 98 은 의무 그래프(육각형 수준)에서 rooted Hamilton 경로를 87개 찾았고, 검증한 증인
4개가 전부 **단어 수준으로 들어올려지지 않는다**는 것을 관찰했다.  이 모듈은 그 관찰을
정리로 승격시킨다.

핵심 정리 (기하, 전수 4,320/4,320, 예외 0):

    임의의 단어 `u` 와 임의의 `ℓ ∈ {0..5}` 에 대해, `σ^ℓ(u)` 의 네 joint target 은
    **서로 다른 네 육각형**에 있고, 그중 어느 것도 `u` 자신의 육각형이 아니다.

따름정리 (**결정적 lift**):

    `WORD_NEXT(u, ℓ, h)` — "구체 단어 `u` 에서 출발해 목표 육각형 `h` 로 들어가는 구체 진입
    단어" — 는 **부분 함수**다.  값이 있으면 유일하다.

`ℓ` 은 이미 강제돼 있으므로(빈 육각형 5, fragment 수리 `5−c_f`; 라운드 90/91 감사 완료),
**고정된 의무 경로 + 고정된 현재 단어 ⟹ 구체 단어열은 많아야 하나**다.  즉 라운드 98 이 본
"단계마다 가능한 단어 ≤ 1" 은 구현 artifact 가 아니라 정리다.

건전성.  단어 수준 관계는 육각형 수준 관계의 **부분집합**이다 — source 단어를 실제 진입
단어로 고정할 뿐 새 제약을 추가하지 않는다.  따라서 육각형 모델이 과대근사인 한 단어 모델도
과대근사이고, **위반만** 폐쇄 근거가 된다.

사용법:
    python3 src/probe_rr_word_lift.py geometry     # §3 전수 기하 검사
    python3 src/probe_rr_word_lift.py control      # §7 양성 대조 (엔진이 만든 사슬 재수용)
    python3 src/probe_rr_word_lift.py witnesses    # §2/§6 보존된 Hamilton 증인 전부 lift
    python3 src/probe_rr_word_lift.py pilot        # §9/§11 lift 인지 DFS 대 그래프 DFS
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
import probe_rr_exact_hamilton as EH  # noqa: E402

ROOTV = EH.ROOTV
OUT = Path(__file__).resolve().parent.parent / "outputs"
SOLVER_VERSION = "claude-r99-word-lift/1"


# --------------------------------------------------------------------- §3 기하

def geometry_census(geo):
    """모든 `(u, ℓ)` 에서 네 joint target 의 육각형이 서로 다른지 전수 확인."""
    hexes = Counter()
    same_hex_as_source = 0
    max_per_hexagon = 0
    for u in range(len(geo)):
        for ell in range(6):
            tg = geo[u]["joint_targets"][str(ell)]
            owners = Counter(geo[v]["hexagon"] for v in tg)
            hexes[len(owners)] += 1
            max_per_hexagon = max(max_per_hexagon, max(owners.values()))
            if geo[u]["hexagon"] in owners:
                same_hex_as_source += 1
    return {"contexts": len(geo) * 6,
            "distinct_target_hexagons": dict(hexes),
            "max_targets_in_one_hexagon": max_per_hexagon,
            "targets_in_source_hexagon": same_hex_as_source,
            "word_next_is_a_partial_function": max_per_hexagon == 1}


# --------------------------------------------------- §1/§4 lift 문맥과 전이 관계

def lift_context(state, cover, geo, hex_words):
    """§1 이 요구한 데이터를 한 곳에 모은다.

    보존 항목: 구체 단어 `id`/문자열, 궤도, 위상(= port), `ℓ`, joint target, 방문 창 제한
    (빈 육각형만 의무), 등록 port 제한(최종 궤도), fragment 점유와 `c_f`.
    """
    final = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1} | set(cover)
    empty = [h for h, m in enumerate(state["hex_masks"]) if m == 0]
    cand = {("hex", h): [w for w in hex_words[h] if geo[w]["orbit"] in final] for h in empty}
    frag = state["fragment"]
    if frag:
        cand[("frag",)] = [frag["entry_id"]]
    ell_of = {}
    for node in cand:
        ell_of[node] = frag["ell"] if node == ("frag",) else 5
    owner = {}
    for node, ws in cand.items():
        for w in ws:
            owner[w] = node
    return {"final_orbits": final, "cand": cand, "ell": ell_of, "owner": owner,
            "root_word": state["p_id"], "root_ell": 5,
            "fragment": frag, "empty": empty}


def word_next(ctx, geo, u, ell):
    """`WORD_NEXT(u, ℓ)` — 목표 의무별로 구체 진입 단어 (정리에 의해 의무당 최대 1개)."""
    out = {}
    for v in geo[u]["joint_targets"][str(ell)]:
        node = ctx["owner"].get(v)
        if node is None:
            continue                      # 최종 궤도가 아니거나 빈 육각형이 아니다
        assert node not in out, "WORD_NEXT 가 함수가 아니다 — 기하 정리 위반"
        out[node] = v
    return out


# --------------------------------------------------------------- §5 경로 lift DP

FAIL_REASONS = {
    "B_no_compatible_word_in_target": "목표 의무에 호환 단어가 없다 (joint target 이 그 육각형에 없음)",
    "B2_target_word_not_in_final_orbit": "joint target 은 그 육각형에 있으나 최종 궤도가 아니다",
    "C_target_word_already_used": "그 구체 단어를 경로 앞부분에서 이미 썼다",
    "A_source_word_wrong": "직전 구체 단어에서 이 의무로 가는 joint 자체가 없다",
}


def lift_path(ctx, geo, path):
    """고정된 의무 경로를 구체 단어열로 들어올린다.  `W_i` 는 정리에 의해 크기 ≤ 1."""
    frontier = {ctx["root_word"]}
    ell = ctx["root_ell"]
    widths, chain = [], []
    used = set()
    for depth, node in enumerate(path):
        node = tuple(node)
        nxt = set()
        for u in frontier:
            got = word_next(ctx, geo, u, ell)
            v = got.get(node)
            if v is not None and v not in used:
                nxt.add(v)
        widths.append(len(nxt))
        if not nxt:
            reason = _classify(ctx, geo, frontier, ell, node, used)
            return {"lift": "LIFT_FAIL", "failed_at": depth, "widths": widths,
                    "chain": chain, "reason": reason,
                    "prev_word": sorted(frontier)[0] if frontier else None,
                    "target": list(node),
                    "candidates_in_target": [
                        {"id": w, "word": geo[w]["word"], "orbit": geo[w]["orbit"],
                         "phase": geo[w]["phase"]} for w in ctx["cand"].get(node, ())],
                    }
        frontier = nxt
        v = next(iter(nxt))
        used.add(v)
        chain.append({"depth": depth, "node": list(node), "word_id": v,
                      "word": geo[v]["word"], "orbit": geo[v]["orbit"],
                      "phase": geo[v]["phase"], "ell_used": ell})
        ell = ctx["ell"][node]
    return {"lift": "LIFT_PASS", "widths": widths, "chain": chain,
            "max_width": max(widths) if widths else 0}


def _classify(ctx, geo, frontier, ell, node, used):
    """§14 — 실패 사유 분류."""
    reasons = Counter()
    for u in frontier:
        targets = geo[u]["joint_targets"][str(ell)]
        in_hex = [v for v in targets
                  if (node[0] == "hex" and geo[v]["hexagon"] == node[1])
                  or (node[0] == "frag" and v == ctx["cand"][node][0])]
        if not in_hex:
            reasons["A_source_word_wrong"] += 1
            continue
        for v in in_hex:
            if ctx["owner"].get(v) is None:
                reasons["B2_target_word_not_in_final_orbit"] += 1
            elif v in used:
                reasons["C_target_word_already_used"] += 1
            else:
                reasons["B_no_compatible_word_in_target"] += 1
    return dict(reasons)


# ------------------------------------------------- §9 lift 인지 정확 탐색

def word_adjacency(ctx, geo):
    """후보 단어마다 `{목표 의무: 목표 단어}` 를 미리 계산한다 (정리에 의해 함수)."""
    adj = {}
    for node, words in ctx["cand"].items():
        for w in words:
            adj[w] = word_next(ctx, geo, w, ctx["ell"][node])
    adj[ctx["root_word"]] = word_next(ctx, geo, ctx["root_word"], ctx["root_ell"])
    return adj


def lift_aware_search(ctx, geo, node_cap=1_000_000, prune=True, memo_on=True):
    """구체 단어를 상태에 넣은 **완전** rooted Hamilton 탐색.

    정리에 의해 상태는 `(현재 구체 단어, 남은 의무 집합)` 이면 충분하다 — 단어 집합이 아니라
    단어 하나.  캡 도달은 UNKNOWN 이고 절대 UNSAT 이 아니다.

    `prune=True` 이면 남은 부분문제에 대한 두 필요조건을 건다 — (i) 남은 의무가 현재 단어에서
    **단어 전이로** 도달 가능, (ii) 남은 부분그래프에서 유출 0 의무 ≤ 1.  둘 다 그래프 수준
    가지치기의 단어 수준 판박이고 건전하다.
    """
    nodes = list(ctx["cand"])
    idx = {n: i for i, n in enumerate(nodes)}
    full = (1 << len(nodes)) - 1
    stats = Counter()
    memo = set()
    path = []
    adj = word_adjacency(ctx, geo)

    def reach_mask(u, rem):
        seen_words = {u}
        got = 0
        stack = [u]
        while stack:
            x = stack.pop()
            for node, v in adj.get(x, {}).items():
                b = 1 << idx[node]
                if rem & b and v not in seen_words:
                    seen_words.add(v)
                    got |= b
                    stack.append(v)
        return got

    def dead_count(rem):
        n = 0
        for node in nodes:
            b = 1 << idx[node]
            if not rem & b:
                continue
            w = ctx["cand"][node]
            alive = False
            for word in w:
                for nn in adj.get(word, {}):
                    if rem & (1 << idx[nn]) and nn != node:
                        alive = True
                        break
                if alive:
                    break
            if not alive:
                n += 1
                if n >= 2:
                    return n
        return n

    def rec(u, ell, rem):
        stats["nodes"] += 1
        if stats["nodes"] > node_cap:
            raise TimeoutError
        if not rem:
            return True
        key = (u, rem)
        if memo_on and key in memo:
            stats["prune_memo"] += 1
            return False
        opts = []
        for node, v in adj.get(u, {}).items():
            b = 1 << idx[node]
            if rem & b:
                opts.append((node, v, b))
        if not opts:
            stats["prune_dead_end"] += 1
            if memo_on:
                memo.add(key)
            return False
        if prune:
            if reach_mask(u, rem) != rem:
                stats["prune_reach"] += 1
                if memo_on:
                    memo.add(key)
                return False
            if dead_count(rem) >= 2:
                stats["prune_two_terminals"] += 1
                if memo_on:
                    memo.add(key)
                return False
        for node, v, b in opts:
            path.append((node, v))
            if rec(v, ctx["ell"][node], rem & ~b):
                return True
            path.pop()
        if memo_on:
            memo.add(key)
        return False

    sys.setrecursionlimit(20_000)
    t0 = time.time()
    try:
        ok = rec(ctx["root_word"], ctx["root_ell"], full)
        verdict = "SAT" if ok else "UNSAT"
    except TimeoutError:
        verdict = "UNKNOWN"
    except RecursionError:
        verdict = "UNKNOWN"
    stats["seconds"] = round(time.time() - t0, 2)
    witness = None
    if verdict == "SAT":
        witness = [{"node": list(n), "word_id": v, "word": geo[v]["word"]} for n, v in path]
    return verdict, dict(stats), witness


def lift_aware_search_iterative(ctx, geo, node_cap=1_000_000):
    """§16 — **두 번째 구현**(명시 스택, memo 없음, 다른 순서).  교차 검증용."""
    nodes = list(ctx["cand"])
    idx = {n: i for i, n in enumerate(nodes)}
    full = (1 << len(nodes)) - 1
    count = 0
    t0 = time.time()
    stack = [(ctx["root_word"], ctx["root_ell"], full, None)]
    frames = [None]
    try:
        stack = [(ctx["root_word"], ctx["root_ell"], full, iter(()))]
        u, ell, rem, _it = stack[0]
        work = [(u, ell, rem, iter(sorted(word_next(ctx, geo, u, ell).items())))]
        while work:
            count += 1
            if count > node_cap:
                return "UNKNOWN", {"nodes": count, "seconds": round(time.time() - t0, 2)}
            u, ell, rem, it = work[-1]
            if not rem:
                return "SAT", {"nodes": count, "seconds": round(time.time() - t0, 2)}
            advanced = False
            for node, v in it:
                b = 1 << idx[node]
                if rem & b:
                    nrem = rem & ~b
                    nell = ctx["ell"][node]
                    work.append((v, nell, nrem,
                                 iter(sorted(word_next(ctx, geo, v, nell).items()))))
                    advanced = True
                    break
            if not advanced:
                work.pop()
        return "UNSAT", {"nodes": count, "seconds": round(time.time() - t0, 2)}
    except RecursionError:
        return "UNKNOWN", {"nodes": count, "seconds": round(time.time() - t0, 2)}


# --------------------------------------------------------------------- 모드

def _load():
    geo, hexw, states, covers, hall = PC.load()
    by_id = {s["sid"]: s for s in states}
    cov = {(c["sid"], c["cover_id"]): c for c in covers}
    return geo, hexw, by_id, cov


def cmd_geometry(args):
    geo, _hexw, _b, _c = _load()
    res = geometry_census(geo)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "rr_word_lift_geometry.json").write_text(
        json.dumps({"round": 99, **res}, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_control(args):
    """§7 — 엔진의 전이 함수로 직접 만든 합법 사슬을 DP 가 반드시 받아들여야 한다."""
    geo, hexw, by_id, cov = _load()
    rng = random.Random(args.seed)
    trials = 0
    rejected = 0
    lengths = Counter()
    for g, _nodes, _edges in EH.load_graphs():
        st = by_id[g["sid"]]
        ctx = lift_context(st, cov[(g["sid"], g["cover_id"])]["orbits"], geo, hexw)
        for _ in range(args.per_state):
            u, ell = ctx["root_word"], ctx["root_ell"]
            chain, used, obl = [], set(), set()
            while True:
                opts = [(n, v) for n, v in word_next(ctx, geo, u, ell).items()
                        if n not in obl and v not in used]
                if not opts:
                    break
                n, v = rng.choice(opts)
                chain.append((n, v))
                used.add(v)
                obl.add(n)
                u, ell = v, ctx["ell"][n]
            if len(chain) < 3:
                continue
            trials += 1
            lengths[len(chain)] += 1
            res = lift_path(ctx, geo, [list(n) for n, _v in chain])
            if res["lift"] != "LIFT_PASS":
                rejected += 1
                print("REJECTED a legal engine-built chain:", g["sid"][:8], res["failed_at"])
            else:
                got = [c["word_id"] for c in res["chain"]]
                if got != [v for _n, v in chain]:
                    rejected += 1
                    print("DP recovered a different chain:", g["sid"][:8])
        if trials >= args.limit:
            break
    res = {"round": 99, "chains": trials, "rejected": rejected,
           "length_hist": dict(sorted(lengths.items()))}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "rr_word_lift_control.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def preserved_paths():
    """라운드 98 이 보존한 그래프-Hamilton 증인 전부 (sid, cover_id, path, 출처)."""
    seen = {}
    for name in ("rr_exact_hamilton_easy_stratum.json", "rr_exact_hamilton_sweep_100k.json"):
        path = OUT / name
        if not path.exists():
            continue
        for row in json.loads(path.read_text())["rows"]:
            if row["verdict"] == "SAT" and row.get("hamilton_path"):
                seen.setdefault(row["sid"], (row["cover_id"], row["hamilton_path"], name))
    wit = OUT / "rr_exact_hamilton_sat_witnesses.json"
    if wit.exists():
        for row in json.loads(wit.read_text())["rows"]:
            seen.setdefault(row["sid"], (row["cover_id"], row["hamilton_path"], "sat_witnesses"))
    return seen


def cmd_witnesses(args):
    """§2/§6 — 보존된 모든 그래프-Hamilton 증인에 lift DP."""
    geo, hexw, by_id, cov = _load()
    rows, verdicts = [], Counter()
    depth_hist, reason_hist, width_hist = Counter(), Counter(), Counter()
    for sid, (cid, path, src) in sorted(preserved_paths().items()):
        ctx = lift_context(by_id[sid], cov[(sid, cid)]["orbits"], geo, hexw)
        res = lift_path(ctx, geo, path)
        verdicts[res["lift"]] += 1
        width_hist[max(res["widths"]) if res["widths"] else 0] += 1
        row = {"sid": sid, "cover_id": cid, "source": src, "m": len(path),
               "lift": res["lift"], "max_width": max(res["widths"]) if res["widths"] else 0,
               "branching_depths": sum(1 for w in res["widths"] if w > 1)}
        if res["lift"] == "LIFT_FAIL":
            depth_hist[res["failed_at"]] += 1
            for k, v in res["reason"].items():
                reason_hist[k] += v
            row.update({"failed_at": res["failed_at"], "reason": res["reason"],
                        "prev_word": res["prev_word"], "target": res["target"],
                        "candidates_in_target": res["candidates_in_target"],
                        "chain_prefix": res["chain"]})
        else:
            row["chain"] = res["chain"]
        rows.append(row)
    summary = {"round": 99, "witnesses": len(rows), "verdicts": dict(verdicts),
               "failure_depth_hist": dict(sorted(depth_hist.items())),
               "max_width_hist": dict(sorted(width_hist.items())),
               "reason_hist": dict(reason_hist)}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    with gzip.open(OUT / "rr_word_lift_witnesses.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"schema": "rr_word_lift_witnesses/1", **summary,
                             "note": "lift 실패는 그 경로만 죽인다 — 상태 폐쇄가 아니다"},
                            ensure_ascii=False) + "\n")
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def cmd_pilot(args):
    """§9/§11 — lift 인지 완전 탐색 대 그래프 전용 DFS."""
    geo, hexw, by_id, cov = _load()
    targets = set(EH.PILOT_UNKNOWN) | set(json.loads(
        (OUT / "rr_exact_hamilton_sat_witnesses.json").read_text()).get("rows", [])
        and {r["sid"][:8] for r in json.loads(
            (OUT / "rr_exact_hamilton_sat_witnesses.json").read_text())["rows"]})
    rows, verdicts, agree = [], Counter(), Counter()
    t0 = time.time()
    n = 0
    for g, nodes, edges in EH.load_graphs():
        short = g["sid"][:8]
        pick = short in targets or n < args.limit
        if not pick:
            continue
        ctx = lift_context(by_id[g["sid"]], cov[(g["sid"], g["cover_id"])]["orbits"], geo, hexw)
        v1, s1, w1 = lift_aware_search(ctx, geo, node_cap=args.cap)
        v2, s2 = lift_aware_search_iterative(ctx, geo, node_cap=args.cap)
        gv, gs, _gp = EH.solve_both(nodes, edges, args.cap, want_path=False)
        verdicts[v1] += 1
        agree[(v1, v2)] += 1
        rows.append({"sid": g["sid"], "cover_id": g["cover_id"], "r": g["r"], "m": g["m"],
                     "graph_hash": g["graph_hash"], "solver": SOLVER_VERSION,
                     "lift_aware": {"verdict": v1, **s1},
                     "second_implementation": {"verdict": v2, **s2},
                     "graph_only": {"verdict": gv, "nodes": gs["nodes"],
                                    "direction": gs["direction"], "seconds": gs["seconds"]},
                     "witness": w1})
        n += 1
        if n % 20 == 0:
            print(f"  {n} {dict(verdicts)} {time.time()-t0:.0f}s", flush=True)
        if n >= args.limit + len(targets):
            break
    res = {"round": 99, "solver": SOLVER_VERSION, "node_cap": args.cap,
           "states": len(rows), "lift_aware_verdicts": dict(verdicts),
           "two_implementations_agree": {f"{a}/{b}": c for (a, b), c in agree.items()},
           "rows": rows, "seconds": round(time.time() - t0)}
    (OUT / "rr_word_lift_pilot.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1))


def word_static(ctx, geo):
    """§15 — 단어 수준의 **값싼 정적 필요조건** (그래프 수준 층 A/B2 의 판박이).

      W-A   모든 의무가 현재 구체 단어에서 **단어 전이로** 도달 가능해야 한다.
      W-B2  단어 전이로 다른 의무에 못 가는 의무는 최대 1개 (끝점은 하나).
      W-IN  모든 의무는 어딘가에서 **단어 전이로 진입 가능**해야 한다.

    전부 genuine 완성이 단어 사슬이라는 사실에서 곧바로 나온다 — 위반만 폐쇄 근거다.
    """
    adj = word_adjacency(ctx, geo)
    nodes = list(ctx["cand"])
    idx = {n: i for i, n in enumerate(nodes)}
    full = (1 << len(nodes)) - 1
    seen = {ctx["root_word"]}
    got = 0
    stack = [ctx["root_word"]]
    while stack:
        x = stack.pop()
        for node, v in adj.get(x, {}).items():
            if v not in seen:
                seen.add(v)
                got |= 1 << idx[node]
                stack.append(v)
    unreachable = [list(n) for n in nodes if not got & (1 << idx[n])]
    dead = [list(n) for n in nodes
            if not any(nn != n for w in ctx["cand"][n] for nn in adj.get(w, {}))]
    incoming = {nn for d in adj.values() for nn in d}
    no_in = [list(n) for n in nodes if n not in incoming]
    if unreachable:
        return "W_A_FAIL", {"unreachable": unreachable[:8], "count": len(unreachable)}
    if len(dead) >= 2:
        return "W_B2_FAIL", {"dead_out": dead[:8], "count": len(dead)}
    if no_in:
        return "W_IN_FAIL", {"no_incoming": no_in[:8], "count": len(no_in)}
    return "PASS", None


def cmd_static(args):
    """§15 — 잔여 전체에 단어 수준 정적 조건.  상태 폐쇄는 **모든 잔여 cover 실패**뿐."""
    geo, hexw, states, covers, hall = PC.load()
    by_id = {s["sid"]: s for s in states}
    cov = {(c["sid"], c["cover_id"]): c for c in covers}
    pair = Counter()
    statev = Counter()
    rsplit = defaultdict(Counter)
    rows = []
    t0 = time.time()
    for i, (sid, st, keep) in enumerate(
            EH.prehamilton_pairs(geo, hexw, states, covers, hall)):
        per = []
        for cid, _nodes, _edges in keep:
            ctx = lift_context(st, cov[(sid, cid)]["orbits"], geo, hexw)
            verdict, cert = word_static(ctx, geo)
            pair[verdict] += 1
            per.append({"cover_id": cid, "pair_verdict": verdict, "certificate": cert})
        allfail = all(p["pair_verdict"] != "PASS" for p in per)
        sv = "UNSAT" if allfail else "SAT"
        statev[sv] += 1
        rsplit[st["r"]][sv] += 1
        if allfail:
            rows.append({"sid": sid, "root": st.get("root"), "c": st.get("c"), "r": st["r"],
                         "surviving_covers": len(per), "unique_path": len(per) == 1,
                         "per_cover": per, "state_verdict": "UNSAT",
                         "all_surviving_covers_fail": True,
                         "solver": SOLVER_VERSION})
        if (i + 1) % 500 == 0:
            print(f"  {i+1} pair={dict(pair)} state={dict(statev)} "
                  f"{time.time()-t0:.0f}s", flush=True)
    summary = {"round": 99, "solver": SOLVER_VERSION,
               "pair": dict(pair), "state": dict(statev),
               "r": {str(k): dict(v) for k, v in sorted(rsplit.items())},
               "state_closed": len(rows),
               "unique_path_closures": sum(1 for r in rows if r["unique_path"]),
               "seconds": round(time.time() - t0)}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    with gzip.open(OUT / "rr_word_lift_static_ledger.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"schema": "rr_word_lift_static/1", **summary,
            "conditions": {"W-A": "모든 의무가 현재 구체 단어에서 단어 전이로 도달 가능",
                           "W-B2": "단어 전이로 다른 의무에 못 가는 의무 <= 1",
                           "W-IN": "모든 의무는 단어 전이로 진입 가능"},
            "state_rule": "state_closed = 모든 잔여 cover 가 FAIL",
            "provisional": "감사 잔여 4,782 는 변경하지 않는다; Codex 감사 없음"},
            ensure_ascii=False) + "\n")
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["geometry", "control", "witnesses", "pilot", "static"])
    ap.add_argument("--seed", type=int, default=99)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--per-state", type=int, default=3)
    ap.add_argument("--cap", type=int, default=1_000_000)
    args = ap.parse_args()
    if args.mode == "geometry":
        cmd_geometry(args)
    elif args.mode == "control":
        cmd_control(args)
    elif args.mode == "witnesses":
        cmd_witnesses(args)
    elif args.mode == "static":
        cmd_static(args)
    else:
        cmd_pilot(args)


if __name__ == "__main__":
    main()
