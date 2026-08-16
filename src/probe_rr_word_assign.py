#!/usr/bin/env python3
"""라운드 102 — **이진 단어 배정** 열거와 구체 단어 그래프 위의 정확 경로 조건.

라운드 101 의 측정: 모든 의무의 진입 단어 후보 `|C(h)|` 는 **최대 2**, 96.9 % 가 singleton.
이 라운드는 국소 필터를 더 만들지 않고, 크기 2 인 의무 `k` 개에 대해 **2^k 개의 배정을 전부
열거**한 뒤 각 배정이 만드는 **구체 단어 그래프**에 이미 증명된 경로 조건을 건다.

`k` 는 실측으로 **최대 4** 다 (전수 15,781 쌍).  따라서 전 모집단 열거가 가능하다.

건전성 (§3).  cover `S` 에 genuine 완성이 있으면 그 완성이 각 의무에 실제로 쓰는 진입 단어가
배정 `A` 를 주고, 완성 경로는 `G_A` 의 뿌리 달린 Hamilton 경로다.  따라서

    모든 배정 `A` 가 Hamilton 불가능  ⟹  cover 불가능.

`G_A` 의 간선은 `h → g  ⟺  WORD_NEXT(U_h, ℓ_h, g) = U_g` 로 **정확한 구체 단어 일치**만 쓴다.

층 (§5, §6).  배정마다 이미 증명된 그래프 필요조건을 순서대로 건다.

    A   ROOT 에서 모든 의무 도달 (라운드 94 층 A)
    B2  sink SCC 하나 / 유출 0 의무 ≤ 1 (라운드 94)
    D4  강제-간선 전파 + 축약 분리자 (라운드 97)
    D1  `c(U(G)−v) ≤ 2` (라운드 96)

    W-E FAIL ⟺ **모든** 배정이 위 중 하나에 걸린다.

주의 (§7).  배정 하나가 A/B2/D1/D4 를 통과한다고 Hamilton 경로가 있는 것은 아니다.
살아남은 배정은 전부 보존하고 정확 탐색으로 넘긴다.

의존성.  W-A 와 마찬가지로 라운드 90/91 의 `ℓ` 강제 정리에 의존한다.

사용법:
    python3 src/probe_rr_word_assign.py census    # §1 k 히스토그램 (raw / 전파 후)
    python3 src/probe_rr_word_assign.py we        # §5/§6 전수 W-E
    python3 src/probe_rr_word_assign.py exact     # §8 살아남은 배정에 정확 Hamilton
    python3 src/probe_rr_word_assign.py control   # §16 양성 대조
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_rr_word_csp as C            # 표준 라이브러리만, 문자열 기하
import replay_rr_word_lift as R          # 표준 라이브러리만, 감사된 그래프 조건

OUT = Path(__file__).resolve().parent.parent / "outputs"
ROOTV = ("root",)
SOLVER_VERSION = "claude-r102-word-assign/1"
ELL_DEPENDENCY = C.ELL_DEPENDENCY


# ------------------------------------------------------------------ 전파와 배정

def propagate_domains(ctx, jt, max_rounds=64):
    """§4 — 라운드-101 의 (P) 규칙만 건전한 전처리로 쓴다.  삭제 인증서는 지지 부재."""
    cand = {k: set(v) for k, v in ctx["cand"].items()}
    for _ in range(max_rounds):
        owner = C._owner(cand)
        work = {"cand": cand, "ell": ctx["ell"], "root": ctx["root"],
                "root_ell": ctx["root_ell"]}
        supported = set(C._root_succ(work, jt, owner).values())
        for node, ws in cand.items():
            for u in ws:
                for _h, v in C._succ(work, jt, owner, node, u).items():
                    supported.add(v)
        changed = False
        for node in list(cand):
            drop = {u for u in cand[node] if u not in supported}
            if drop:
                cand[node] -= drop
                changed = True
            if not cand[node]:
                return None                       # 빈 도메인 — cover 불가능
        if not changed:
            break
    return cand


def assignments(cand):
    """`|C(h)| = 2` 인 의무들에 대해 `2^k` 배정을 전부 생성한다."""
    fixed = {h: next(iter(v)) for h, v in cand.items() if len(v) == 1}
    binary = [(h, sorted(v)) for h, v in cand.items() if len(v) == 2]
    for choice in itertools.product(*[range(2) for _ in binary]):
        A = dict(fixed)
        for (h, ws), c in zip(binary, choice):
            A[h] = ws[c]
        yield A, {h: ws[c] for (h, ws), c in zip(binary, choice)}


def graph_of(A, ctx, jt):
    """§2 — 배정 `A` 의 구체 단어 그래프 (의무 정점, 정확 단어 일치 간선)."""
    where = {u: h for h, u in A.items()}
    nodes = list(A)
    edges = {}
    for h, u in A.items():
        tgt = set()
        for v in jt[u][ctx["ell"][h]]:
            g = where.get(v)
            if g is not None and g != h:
                tgt.add(g)
        edges[h] = tgt
    rt = set()
    for v in jt[ctx["root"]][ctx["root_ell"]]:
        g = where.get(v)
        if g is not None:
            rt.add(g)
    edges[ROOTV] = rt
    return nodes, edges


LAYER_ORDER = ("A", "B2", "D4", "D1")


def assignment_verdict(nodes, edges):
    """§5 — 이미 증명된 조건을 싼 순서로.  반환 `(verdict, 걸린 층)`."""
    if R.reachable_from_root(nodes, edges):
        return "FAIL", "A"
    if R.terminal_bounds(nodes, edges):
        return "FAIL", "B2"
    if R.d4b_fails(nodes, edges):
        return "FAIL", "D4"
    if R.d1_fails(nodes, edges):
        return "FAIL", "D1"
    return "PASS", None


# ------------------------------------------------------------------ 정확 탐색

def hamilton(nodes, edges, node_cap=200_000):
    """구체 배정 그래프 위의 완전 rooted Hamilton 탐색.  캡은 UNKNOWN."""
    idx = {n: i for i, n in enumerate(nodes)}
    m = len(nodes)
    out = [0] * m
    for h, ys in edges.items():
        if h == ROOTV:
            continue
        for y in ys:
            out[idx[h]] |= 1 << idx[y]
    root_out = 0
    for y in edges.get(ROOTV, ()):
        root_out |= 1 << idx[y]
    full = (1 << m) - 1
    stats = Counter()
    memo = set()
    path = []

    def bits(x):
        while x:
            low = x & -x
            yield low.bit_length() - 1
            x ^= low

    def reach(cur, rem):
        seen = 1 << cur
        frontier = seen
        while frontier:
            nxt = 0
            for i in bits(frontier):
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
            return False
        cand = out[cur] & rem
        if not cand or reach(cur, rem) != rem:
            memo.add(key)
            return False
        dead = 0
        for i in bits(rem):
            if not out[i] & (rem & ~(1 << i)):
                dead += 1
                if dead >= 2:
                    memo.add(key)
                    return False
        for y in sorted(bits(cand), key=lambda z: bin(out[z] & rem).count("1")):
            path.append(y)
            if dfs(y, rem & ~(1 << y)):
                return True
            path.pop()
        memo.add(key)
        return False

    sys.setrecursionlimit(20_000)
    try:
        ok = False
        for y in sorted(bits(root_out), key=lambda z: bin(out[z] & full).count("1")):
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
    witness = [nodes[i] for i in path] if verdict == "SAT" else None
    return verdict, dict(stats), witness


# ------------------------------------------------------------------------ 모드

def _iter_pairs(rows, states, covers, orbit, hexm, jt):
    for r in rows:
        ctx = C.context(states[r["sid"]], covers[(r["sid"], r["cover_id"])]["orbits"],
                        orbit, hexm, jt)
        yield r, ctx


def cmd_census(args):
    word_of, orbit, hexm, jt, states, covers = C.load()
    rows = C.wa_pairs()
    kraw, kprop = Counter(), Counter()
    for r, ctx in _iter_pairs(rows, states, covers, orbit, hexm, jt):
        kraw[sum(1 for v in ctx["cand"].values() if len(v) == 2)] += 1
        cand = propagate_domains(ctx, jt)
        kprop[-1 if cand is None else sum(1 for v in cand.values() if len(v) == 2)] += 1
    res = {"round": 102, "pairs": len(rows),
           "k_raw": dict(sorted(kraw.items())), "k_propagated": dict(sorted(kprop.items())),
           "sum_2k_raw": sum(2 ** k * n for k, n in kraw.items()),
           "sum_2k_propagated": sum(2 ** k * n for k, n in kprop.items() if k >= 0),
           "max_k": max(kraw)}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "rr_word_assign_census.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_we(args):
    word_of, orbit, hexm, jt, states, covers = C.load()
    rows = C.wa_pairs()
    pair = Counter()
    layer = Counter()
    assign_total = 0
    survivors = Counter()
    per_state = defaultdict(list)
    detail = []
    t0 = time.time()
    for i, (r, ctx) in enumerate(_iter_pairs(rows, states, covers, orbit, hexm, jt)):
        cand = propagate_domains(ctx, jt)
        if cand is None:
            pair["FAIL"] += 1
            layer["empty_domain"] += 1
            per_state[r["sid"]].append((r["cover_id"], "FAIL"))
            detail.append({"sid": r["sid"], "cover_id": r["cover_id"],
                           "verdict": "FAIL", "reason": "empty_domain"})
            continue
        alive = []
        died = Counter()
        n_as = 0
        for A, binary in assignments(cand):
            n_as += 1
            nodes, edges = graph_of(A, ctx, jt)
            v, why = assignment_verdict(nodes, edges)
            if v == "PASS":
                alive.append(binary)
            else:
                died[why] += 1
        assign_total += n_as
        survivors[len(alive)] += 1
        for k2, c in died.items():
            layer[k2] += c
        verdict = "FAIL" if not alive else "PASS"
        pair[verdict] += 1
        per_state[r["sid"]].append((r["cover_id"], verdict))
        detail.append({"sid": r["sid"], "cover_id": r["cover_id"], "verdict": verdict,
                       "assignments": n_as, "surviving": len(alive),
                       "died_by_layer": dict(died),
                       "surviving_binary_choices": [
                           {str(list(h)): u for h, u in b.items()} for b in alive[:8]]})
        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{len(rows)} pair={dict(pair)} assigns={assign_total} "
                  f"{time.time()-t0:.0f}s", flush=True)
    statev = Counter()
    rsplit = defaultdict(Counter)
    closures = []
    for sid, vs in per_state.items():
        allfail = all(v == "FAIL" for _c, v in vs)
        statev["UNSAT" if allfail else "SAT"] += 1
        rsplit[states[sid]["r"]]["UNSAT" if allfail else "SAT"] += 1
        if allfail:
            closures.append(sid)
    summary = {"round": 102, "solver": SOLVER_VERSION, "pairs": len(rows),
               "assignments_enumerated": assign_total,
               "pair_verdicts": dict(pair),
               "assignments_killed_by_layer": dict(layer),
               "surviving_assignment_histogram": dict(sorted(survivors.items())),
               "state_verdicts": dict(statev),
               "r": {str(k): dict(v) for k, v in sorted(rsplit.items())},
               "state_closures": len(closures),
               "seconds": round(time.time() - t0),
               "depends_on": ELL_DEPENDENCY}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    with gzip.open(OUT / "rr_word_assign_we.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"schema": "rr_word_assign_we/1", **summary,
                             "state_rule": "state_closed = 모든 W-A 통과 cover 가 W-E FAIL"},
                            ensure_ascii=False) + "\n")
        for row in detail:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.write(json.dumps({"record": "state_closures", "sids": sorted(closures)},
                            ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["census", "we"])
    args = ap.parse_args()
    {"census": cmd_census, "we": cmd_we}[args.mode](args)


if __name__ == "__main__":
    main()
