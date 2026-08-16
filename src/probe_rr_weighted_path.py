#!/usr/bin/env python3
"""라운드 104 — **가중 경로 조건**: `N+H` 예산을 필요조건으로 승격한다.

라운드 103 이 찾은 좌표를 여기서 정리로 굳히고 쓴다.

예산 유도 (§0).  미래 구간의 각 pass 는 `ℓ` 회전(weight 1) + joint 하나다.  엔진의 갱신은

    dS = [weight ≥ 3]        dH = max(weight − 3, 0)        dF = [abandonment]

이고, 우리 pass 모델에서는

    * `ℓ = 5` 이면 회전 뒤 커서의 σ-후속은 진입 단어이므로 **이미 방문됨** → abandonment 없음
    * fragment 수리(`ℓ = 5 − c_f`)도 마찬가지로 σ-후속이 이미 방문된 칸 → abandonment 없음

따라서 `ΔF = 0`.  또 네 joint target 의 최소 weight 는 `T1` 이 2, `T2/T3/T4` 가 3 이므로
`ΔH = 0` 이고 `ΔS = E`(= weight-3 joint 개수).  마지막으로 완성 시 `O = 25` 이므로
`ΔO = K`.  `Ndef = S + F − O` 를 대입하면

    final(Ndef + H) = current(Ndef + H) + E − K

이고 `final(Ndef+H) ≤ 3` 이므로

    **E ≤ B := 3 + K − Ndef − H.**

`ΔH = 0` 은 **최소 weight 를 쓴다는 가정**에서 나온다.  같은 target 에 weight 6 tail 도
존재하므로 실제 walk 이 더 비쌀 수는 있어도 **더 싸지는 않다** — 하한이므로 필요조건으로
안전하다.

층 (§1, §14).  구체 배정 그래프의 각 간선에 `cost = 0`(T1) / `1`(T2/T3/T4) 를 붙이고

    **총비용 ≤ B 인 rooted Hamilton 경로가 존재해야 한다.**

사용법:
    python3 src/probe_rr_weighted_path.py witnesses   # §3/§15 22개 증인 검증과 가중 재탐색
    python3 src/probe_rr_weighted_path.py bounds      # §4/§10/§12 값싼 하한들의 payoff
    python3 src/probe_rr_weighted_path.py pilot       # §14 가중 정확 탐색 파일럿
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_rr_word_csp as C
import probe_rr_word_assign as W

OUT = Path(__file__).resolve().parent.parent / "outputs"
ROOTV = W.ROOTV
SOLVER_VERSION = "claude-r104-weighted/1"


def budget(state):
    """`B = 3 + K − Ndef − H`, `Ndef = S + F − O`."""
    ndef = state["S"] + state["F"] - state["O"]
    return 3 + state["K"] - ndef - state["H"], ndef


def weighted_graph(A, ctx, jt):
    """의무 그래프 + 간선 비용 (`T1` 은 0, 나머지는 1)."""
    where = {u: h for h, u in A.items()}
    edges = {}
    cost = {}
    for h, u in A.items():
        tg = jt[u][ctx["ell"][h]]
        out = set()
        for i, v in enumerate(tg):
            g = where.get(v)
            if g is not None and g != h:
                out.add(g)
                c = 0 if i == 0 else 1
                key = (h, g)
                cost[key] = min(cost.get(key, 9), c)
        edges[h] = out
    rt = set()
    for i, v in enumerate(jt[ctx["root"]][ctx["root_ell"]]):
        g = where.get(v)
        if g is not None:
            rt.add(g)
            key = (ROOTV, g)
            cost[key] = min(cost.get(key, 9), 0 if i == 0 else 1)
    edges[ROOTV] = rt
    return list(A), edges, cost


def zero_cost_components(nodes, edges, cost):
    """§12 — 비용-0 호만으로 만든 (함수형) 그래프의 약연결 성분 수."""
    par = {n: n for n in nodes}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    arcs = 0
    for (x, y), c in cost.items():
        if c == 0 and x != ROOTV and y in par and x in par:
            arcs += 1
            a, b = find(x), find(y)
            if a != b:
                par[a] = b
    comps = len({find(n) for n in nodes})
    return comps, arcs


def zero_cost_deficiency(nodes, edges, cost):
    """§10 — 비용-0 이분 그래프의 최대 매칭 결손 하한 `(m+1) − ν0`.

    각 source 는 비용-0 간선을 **많아야 하나** 갖는다(`T1` 이 유일)이므로
    `ν0 = |서로 다른 비용-0 target|`, 그리고 END(terminal 자리)는 언제나 비용 0.
    """
    tgt = {y for (x, y), c in cost.items() if c == 0}
    return (len(nodes) + 1) - (len(tgt) + 1)


def weighted_hamilton(nodes, edges, cost, B, node_cap=200_000):
    """총비용 ≤ `B` 인 rooted Hamilton 경로.  캡 도달은 UNKNOWN."""
    idx = {n: i for i, n in enumerate(nodes)}
    m = len(nodes)
    out0 = [0] * m          # 비용 0 후속 비트마스크
    out1 = [0] * m          # 비용 1 후속
    for (x, y), c in cost.items():
        if x == ROOTV:
            continue
        (out0 if c == 0 else out1)[idx[x]] |= 1 << idx[y]
    root0 = root1 = 0
    for (x, y), c in cost.items():
        if x == ROOTV:
            if c == 0:
                root0 |= 1 << idx[y]
            else:
                root1 |= 1 << idx[y]
    full = (1 << m) - 1
    stats = Counter()
    memo = {}
    path = []

    def bits(x):
        while x:
            low = x & -x
            yield low.bit_length() - 1
            x ^= low

    def reach(cur, rem):
        seen = 1 << cur
        fr = seen
        while fr:
            nx = 0
            for i in bits(fr):
                nx |= out0[i] | out1[i]
            nx &= rem & ~seen
            seen |= nx
            fr = nx
        return seen & rem

    def dfs(cur, rem, spent):
        stats["nodes"] += 1
        if stats["nodes"] > node_cap:
            raise TimeoutError
        if not rem:
            return True
        prev = memo.get((cur, rem))
        if prev is not None and prev <= spent:
            stats["memo"] += 1
            return False
        if reach(cur, rem) != rem:
            memo[(cur, rem)] = 0
            return False
        # 남은 의무 수만큼 간선이 더 필요하고, 그중 비용-0 로 덮을 수 없는 진입은
        # 최소한 (남은 의무 − 비용-0 진입 가능 의무) 개의 비용-1 을 강제한다.
        # 비용-0 호는 out-degree ≤ 1 인 함수형 그래프다.  남은 의무 위에서 그 호들이
        # 만드는 약연결 성분이 `c` 개면, 경로는 성분을 잇기 위해 최소 `c − 1` 개의
        # 비용-1 호를 써야 한다 (현재 정점에서 나가는 비용-0 호는 한 성분을 이어 준다).
        idxs = list(bits(rem))
        par = {i: i for i in idxs}

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        for i in idxs:
            t = out0[i] & rem
            if t:
                j = t.bit_length() - 1
                a, b2 = find(i), find(j)
                if a != b2:
                    par[a] = b2
        comps = len({find(i) for i in idxs})
        t0m = out0[cur] & rem
        need = comps - 1
        if t0m == 0:
            need = comps
        if spent + need > B:
            stats["prune_cost"] += 1
            memo[(cur, rem)] = spent
            return False
        for c, cand in ((0, out0[cur] & rem), (1, out1[cur] & rem)):
            if spent + c > B:
                continue
            for y in bits(cand):
                path.append((y, c))
                if dfs(y, rem & ~(1 << y), spent + c):
                    return True
                path.pop()
        memo[(cur, rem)] = spent
        return False

    sys.setrecursionlimit(20_000)
    t0 = time.time()
    try:
        ok = False
        for c, cand in ((0, root0), (1, root1)):
            if c > B:
                continue
            for y in bits(cand):
                path.append((y, c))
                if dfs(y, full & ~(1 << y), c):
                    ok = True
                    break
                path.pop()
            if ok:
                break
        verdict = "SAT" if ok else "UNSAT"
    except TimeoutError:
        verdict = "UNKNOWN"
    except RecursionError:
        verdict = "UNKNOWN"
    stats["seconds"] = round(time.time() - t0, 2)
    wit = None
    if verdict == "SAT":
        wit = {"order": [nodes[i] for i, _c in path],
               "costs": [c for _i, c in path],
               "total_cost": sum(c for _i, c in path)}
    return verdict, dict(stats), wit


def _load():
    return C.load()


def cmd_witnesses(args):
    """§3/§15 — 22개 증인의 비용을 계산하고, 예산 안의 다른 경로가 있는지 다시 푼다."""
    word_of, orbit, hexm, jt, states, covers = _load()
    data = json.loads((OUT / "rr_word_assign_exact.json").read_text())
    lit = {r["sid"]: r for r in json.loads((OUT / "rr_literal_replay.json").read_text())["rows"]}
    rows = [r for r in data["rows"] if r.get("hamilton_witness")]
    out = []
    verd = Counter()
    for r in rows:
        st = states[r["sid"]]
        B, ndef = budget(st)
        ctx = C.context(st, covers[(r["sid"], r["cover_id"])]["orbits"], orbit, hexm, jt)
        cand = W.propagate_domains(ctx, jt)
        wit = r["hamilton_witness"]
        A = {}
        for h, u in zip([tuple(x) for x in wit["obligation_order"]], wit["word_order"]):
            A[h] = u
        for h, ws in cand.items():
            if h not in A:
                A[h] = next(iter(ws))
        nodes, edges, cost = weighted_graph(A, ctx, jt)
        # 저장된 경로의 비용
        order = [tuple(x) for x in wit["obligation_order"]]
        E = 0
        prev = ROOTV
        for h in order:
            E += cost.get((prev, h), 1)
            prev = h
        end = lit[r["sid"]]["end"]
        final_budget = end["S"] + end["F"] - end["O"] + end["H"]
        check = (E - B) == (final_budget - 3)
        v, stats, w2 = weighted_hamilton(nodes, edges, cost, B, node_cap=args.cap)
        verd[v] += 1
        out.append({"sid": r["sid"], "cover_id": r["cover_id"], "B": B, "Ndef": ndef,
                    "stored_path_cost_E": E, "final_Ndef_plus_H": final_budget,
                    "identity_E_minus_B_equals_final_minus_3": check,
                    "weighted_verdict": v, "weighted_nodes": stats.get("nodes"),
                    "weighted_seconds": stats.get("seconds"),
                    "weighted_witness_cost": (w2 or {}).get("total_cost")})
        print(f"  {r['sid'][:8]} B={B} storedE={E} final={final_budget} id={check} "
              f"weighted={v}/{stats.get('nodes')}", flush=True)
    summary = {"round": 104, "witnesses": len(rows),
               "identity_holds": all(o["identity_E_minus_B_equals_final_minus_3"] for o in out),
               "weighted_verdicts": dict(verd),
               "stored_cost_range": [min(o["stored_path_cost_E"] for o in out),
                                     max(o["stored_path_cost_E"] for o in out)],
               "B_range": [min(o["B"] for o in out), max(o["B"] for o in out)]}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    (OUT / "rr_weighted_witnesses.json").write_text(
        json.dumps({**summary, "rows": out}, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_bounds(args):
    """§4/§10/§12 — 값싼 하한 두 개의 전수 payoff."""
    word_of, orbit, hexm, jt, states, covers = _load()
    rows = C.wa_pairs()
    hist_def = Counter()
    hist_conn = Counter()
    slack = Counter()
    closed_pairs = 0
    t0 = time.time()
    per = defaultdict(list)
    for i, (r, ctx) in enumerate(W._iter_pairs(rows, states, covers, orbit, hexm, jt)):
        st = states[r["sid"]]
        B, _ = budget(st)
        cand = W.propagate_domains(ctx, jt)
        if cand is None:
            per[r["sid"]].append("FAIL")
            closed_pairs += 1
            continue
        best = None
        for A, _b in W.assignments(cand):
            nodes, edges, cost = weighted_graph(A, ctx, jt)
            L1 = zero_cost_deficiency(nodes, edges, cost)
            comps, _arcs = zero_cost_components(nodes, edges, cost)
            L2 = comps - 1
            L = max(L1, L2)
            best = L if best is None else min(best, L)
            hist_def[L1] += 1
            hist_conn[L2] += 1
        slack[B - best] += 1
        v = "FAIL" if best > B else "PASS"
        per[r["sid"]].append(v)
        if v == "FAIL":
            closed_pairs += 1
        if (i + 1) % 3000 == 0:
            print(f"  {i+1}/{len(rows)} fail={closed_pairs} {time.time()-t0:.0f}s", flush=True)
    closed = [s for s, vs in per.items() if all(x == "FAIL" for x in vs)]
    res = {"round": 104, "pairs": len(rows), "pair_fail": closed_pairs,
           "state_closures": len(closed),
           "L1_zero_cost_deficiency_hist": dict(sorted(hist_def.items())),
           "L2_zero_cost_components_minus1_hist": dict(sorted(hist_conn.items())),
           "slack_B_minus_bestL_hist": dict(sorted(slack.items())),
           "seconds": round(time.time() - t0)}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "rr_weighted_bounds.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["witnesses", "bounds"])
    ap.add_argument("--cap", type=int, default=200_000)
    args = ap.parse_args()
    {"witnesses": cmd_witnesses, "bounds": cmd_bounds}[args.mode](args)


if __name__ == "__main__":
    main()
