#!/usr/bin/env python3
"""라운드 108 — **가설 (H5) 해소**: 550개 tail 전부를 쓰는 완전-joint 가중 인증서.

라운드 107 은 의무 그래프가 weight ≤ 3 joint 네 개로만 만들어진다는 **서술되지 않은 가정
(H5)** 를 드러냈다.  이 파일은 그 가정을 **쓰지 않는다**: 엔진의 indecomposable tail
550개(weight 별 `1,1,3,13,71,461`) 전부에서 의무→의무 호를 만들고, 각 호에 정확한 자원 비용

    cost(w) = [w >= 3] + max(w - 3, 0)        w=2:0  3:1  4:2  5:3  6:4

를 붙여 **총비용 ≤ B** 인 rooted Hamilton 경로를 정확 탐색한다.

핵심 보조정리 (라운드 108, §12).  뿌리 여유 `s := B − L2(ROOT, 전체)` 라 하면 예산 안의 임의
완성에서

    Σ_{무거운 호} (cost − 1)  ≤  s

이다 (총비용 ≥ 무료가 아닌 호의 개수 + Σ(cost−1) ≥ (c−1) + Σ(cost−1), 그리고 총비용 ≤ B).
따라서 `s = 0` 인 인스턴스에서는 **무거운 joint 를 하나도 쓸 수 없다** — 그 인스턴스에서는
(H5) 가 정리로 성립한다.

사용법:
    python3 src/certify_rr_full_joint.py --conditional   # 라운드-107 조건부 1,353 상태
    python3 src/certify_rr_full_joint.py --all           # 6,396 상태 전부 (대조)
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
VERSION = "claude-r108-full-joint/1"


def _load(name, path):
    spec = iu.spec_from_file_location(name, path)
    mod = iu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


core = _load("superperm_port_lift", ROOT / "legacy_research" / "work" / "superperm_port_lift.py")
C = _load("certify_rr_q2_zero", ROOT / "src" / "certify_rr_q2_zero.py")
MAXC = 4                                     # cost(6) = 4


def cost_of(w):
    return (1 if w >= 3 else 0) + max(w - 3, 0)


def joint_tails():
    """weight >= 2 인 indecomposable tail 전부 = 549개 joint."""
    out = []
    for w in range(2, 7):
        for pi in core.tail_permutations(w):
            out.append((w, core.tail_action(w, pi)))
    return out


TAILS = joint_tails()


def min_cost_table(word, ident):
    """`MC[y*720 + t]` = `y` 에서 `t` 로 가는 joint 의 **최소** 자원 비용 (없으면 255).

    550개 tail 전부를 한 번만 전개해 두는 표다.  배정마다 다시 전개하지 않는다.
    """
    mc = bytearray([255]) * 0
    mc = bytearray([255] * (720 * 720))
    for i in range(720):
        y = tuple(int(ch) for ch in word[i])
        base = i * 720
        for w, act in TAILS:
            t = ident["".join(str(x) for x in core.word_after(y, act))]
            c = cost_of(w)
            if c < mc[base + t]:
                mc[base + t] = c
    return mc


def rot_id(word, ident, wid, k):
    y = tuple(int(ch) for ch in word[wid])
    for _ in range(k):
        y = core.word_after(y, core.SIGMA)
    return ident["".join(str(x) for x in y)]


def full_graph(A, ell, root_id, word, ident, mc, rot):
    """의무 그래프 — 550개 tail 전부, 같은 (h,g) 쌍은 가장 싼 비용만."""
    nodes = list(A)
    m = len(nodes)
    ys = [rot[(A[n], ell[n])] for n in nodes]
    tg = [A[n] for n in nodes]
    out = [[0] * m for _ in range(MAXC + 1)]
    for i in range(m):
        base = ys[i] * 720
        for j in range(m):
            if j == i:
                continue
            c = mc[base + tg[j]]
            if c <= MAXC:
                out[c][i] |= 1 << j
    rt = [0] * (MAXC + 1)
    base = rot[(root_id, 5)] * 720
    for j in range(m):
        c = mc[base + tg[j]]
        if c <= MAXC:
            rt[c] |= 1 << j
    return nodes, out, rt


def components(out0, rem):
    """비용-0 호의 약연결 성분 수.  유출 차수 <= 1 이므로 후속 하나만 보면 된다."""
    idxs = []
    x = rem
    while x:
        low = x & -x
        idxs.append(low.bit_length() - 1)
        x ^= low
    par = {i: i for i in idxs}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for i in idxs:
        t = out0[i] & rem
        assert t & (t - 1) == 0, "비용-0 유출 차수 > 1 — 전제 위반"
        if t:
            j = t.bit_length() - 1
            a, b = find(i), find(j)
            if a != b:
                par[a] = b
    return len({find(i) for i in idxs})


def lower_bound(out0, cur, rem, has_free_entry):
    c = components(out0, rem)
    return c - 1 if has_free_entry else c


INF = 10 ** 6


def exit_bound(out, cur, rem):
    """라운드 108 — **성분 탈출 비용 하한** (개수 하한보다 강하고 여전히 건전).

    경로가 `R` 을 덮을 때 쓰인 비용-0 호는 선형 숲이고 각 자유 구간은 비용-0 약연결 성분
    하나 안에 있다.  마지막 정점을 담은 성분을 뺀 **모든 성분에서 비-무료 호가 적어도 하나
    출발**하므로

        총비용 >= 진입비용 + Σ_X minexit(X) − max_X minexit(X),

    `minexit(X)` = `X` 의 정점에서 `R` 안으로 나가는 비-무료 호의 최소 비용.
    모든 `minexit` 가 1 이면 `c − 1` 로 되돌아간다.
    """
    idxs = []
    x = rem
    while x:
        low = x & -x
        idxs.append(low.bit_length() - 1)
        x ^= low
    par = {i: i for i in idxs}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    out0 = out[0]
    for i in idxs:
        t = out0[i] & rem
        assert t & (t - 1) == 0, "비용-0 유출 차수 > 1 — 전제 위반"
        if t:
            j = t.bit_length() - 1
            a, b = find(i), find(j)
            if a != b:
                par[a] = b
    minexit = {}
    for i in idxs:
        best = INF
        for c in range(1, MAXC + 1):
            if out[c][i] & rem:
                best = c
                break
        r = find(i)
        if best < minexit.get(r, INF):
            minexit[r] = best
    vals = [minexit.get(r, INF) for r in {find(j) for j in idxs}]
    if vals.count(INF) > 1:
        return INF
    if out0[cur] & rem:
        entry = 0
    else:
        entry = INF
        for c in range(1, MAXC + 1):
            if out[c][cur] & rem:
                entry = c
                break
    if entry >= INF:
        return INF
    tot = sum(v for v in vals if v < INF)
    if INF in vals:
        return entry + tot
    return entry + tot - max(vals)


def free_structure(out0, m):
    """함수형 비용-0 그래프의 요약: 후속 배열 · 역인접 · 호 개수 · 고리 표식.

    유출 차수 <= 1 이므로 각 정점의 비용-0 호는 많아야 하나이고, 호를 그 **출발 정점**으로
    가리킬 수 있다.  약연결 성분 수는 `m − (호 개수) + (고리 개수)` 다.
    """
    succ = [-1] * m
    for i in range(m):
        t = out0[i]
        assert t & (t - 1) == 0, "비용-0 유출 차수 > 1 — 전제 위반"
        if t:
            succ[i] = t.bit_length() - 1
    pred = [[] for _ in range(m)]
    arcs = 0
    for i, j in enumerate(succ):
        if j >= 0:
            pred[j].append(i)
            arcs += 1
    # 고리 찾기 (함수형이므로 성분마다 많아야 하나)
    cyc_id = [-1] * m
    color = [0] * m
    cycles = 0
    for start in range(m):
        if color[start]:
            continue
        path = []
        v = start
        while v >= 0 and color[v] == 0:
            color[v] = 1
            path.append(v)
            v = succ[v]
        if v >= 0 and color[v] == 1:
            k = path.index(v)
            for w in path[k:]:
                cyc_id[w] = cycles
            cycles += 1
        for w in path:
            color[w] = 2
    return succ, pred, arcs, cycles, cyc_id


def heavy_arc_excluded(u, v, cost, B, m, succ, pred, arcs, cycles, cyc_id):
    """라운드 108 — **강제-호 하한**: 호 `u→v` 를 쓰는 완성의 총비용 하한이 `B` 를 넘는가.

    경로가 `u→v` 를 쓰면 `u` 의 비용-0 후속 호와 `v` 로 들어오는 모든 비용-0 호는 쓸 수
    없다 (각 정점은 후속도 선행도 하나뿐이다).  그 호들을 지운 `G0''` 의 약연결 성분 수를
    `c''` 라 하면 선형 숲 논증이 그대로 적용돼

        총비용 >= (c'' − 1) + (cost − 1)

    이다.  이 값이 `B` 를 넘으면 **어떤 완성도 이 호를 쓸 수 없다.**
    """
    removed = set()
    if succ[u] >= 0:
        removed.add(u)
    removed.update(pred[v])
    a2 = arcs - len(removed)
    broken = {cyc_id[w] for w in removed if cyc_id[w] >= 0}
    c2 = m - a2 + (cycles - len(broken))
    return (c2 - 1) + (cost - 1) > B


def search(out, rt, B, stats, node_cap=2_000_000, excess_budget=None):
    m = len(out[0])
    full = (1 << m) - 1
    any_out = [0] * m
    for i in range(m):
        v = 0
        for c in range(MAXC + 1):
            v |= out[c][i]
        any_out[i] = v
    memo = {}
    local = [0]
    heavy_seen = Counter()

    def reach(cur, rem):
        seen = 0
        front = any_out[cur] & rem
        while front:
            seen |= front
            nxt = 0
            f = front
            while f:
                low = f & -f
                nxt |= any_out[low.bit_length() - 1]
                f ^= low
            front = nxt & rem & ~seen
        return seen

    def dfs(cur, rem, spent, heavy, exc):
        stats["nodes"] += 1
        local[0] += 1
        if local[0] > node_cap:
            raise TimeoutError
        if not rem:
            heavy_seen.update(heavy)
            return True
        # 초과-예산 가지치기가 켜지면 남은 문제는 (cur, rem, 남은 비용, 남은 초과) 에
        # 의존한다.  spent 단독 지배는 불건전하므로 exc 를 메모 키에 넣는다.
        key = (cur, rem, exc)
        prev = memo.get(key)
        if prev is not None and prev <= spent:
            return False
        # 무거운 호가 아직 남아 있으면 그래프가 거의 완전해서 도달성 가지치기가 무의미하다.
        # (가지치기를 **건너뛰는 것**은 언제나 건전하다 — 완전성만 지키면 된다.)
        if excess_budget is None or exc >= excess_budget:
            if reach(cur, rem) != rem:
                memo[key] = 0
                return False
        lb = exit_bound(out, cur, rem)
        if spent + lb > B:
            stats["prune_cost"] += 1
            memo[key] = spent
            return False
        for c in range(MAXC + 1):
            if spent + c > B:
                break
            ne = exc + (c - 1 if c >= 2 else 0)
            if excess_budget is not None and ne > excess_budget:
                break
            t = out[c][cur] & rem
            while t:
                low = t & -t
                y = low.bit_length() - 1
                t ^= low
                nh = heavy if c < 2 else heavy + (c,)
                if dfs(y, rem & ~(1 << y), spent + c, nh, ne):
                    return True
        memo[key] = spent
        return False

    sys.setrecursionlimit(20000)
    try:
        for c in range(MAXC + 1):
            if c > B:
                break
            t = rt[c]
            while t:
                low = t & -t
                y = low.bit_length() - 1
                t ^= low
                e0 = c - 1 if c >= 2 else 0
                if excess_budget is not None and e0 > excess_budget:
                    continue
                if dfs(y, full & ~(1 << y), c, () if c < 2 else (c,), e0):
                    return "SAT", dict(heavy_seen)
        return "UNSAT", {}
    except (TimeoutError, RecursionError):
        return "UNKNOWN", {}


def root_bound(out0, rt0):
    m = len(out0)
    return lower_bound(out0, None, (1 << m) - 1, bool(rt0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditional", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only-sids", default="")
    ap.add_argument("--node-cap", type=int, default=2_000_000)
    ap.add_argument("--out", default="rr_full_joint_certificate.json")
    args = ap.parse_args()
    t0 = time.time()
    word, orb, hexm, jt = C.geometry()
    ident = {w: i for i, w in word.items()}
    mc = min_cost_table(word, ident)
    rot = {(i, k): rot_id(word, ident, i, k) for i in range(720) for k in range(6)}
    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    _h, covers = C.read_jsonl(C.ARCHIVE / "covers.jsonl.gz")
    _h, hall = C.read_jsonl(C.ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        passing[h["sid"]].append(h["cover_id"])

    # 라운드-107 조건부 블록: 뿌리 하한만으로 닫히지 **않은** 상태
    with gzip.open(OUT / "rr_q2_no_hall_certificate.jsonl.gz", "rt") as fh:
        fh.readline()
        rows = [json.loads(line) for line in fh]
    per = defaultdict(list)
    for r in rows:
        per[r["sid"]].append(r["reason"])
    conditional = sorted(s for s, v in per.items() if not all(x == "root_bound" for x in v))
    robust = sorted(s for s, v in per.items() if all(x == "root_bound" for x in v))
    targets = conditional if args.conditional else (sorted(passing) if args.all else conditional)
    if args.only_sids:
        want = set(json.loads(Path(args.only_sids).read_text())["sids"])
        targets = [t for t in sorted(want)]
    if args.limit:
        targets = targets[:args.limit]

    stats = Counter()
    counts = Counter()
    slack = Counter()
    heavy_total = Counter()
    per_state = defaultdict(list)
    outrows = []
    done = 0
    for sid in targets:
        st = S[sid]
        B = 3 + st["K"] - (st["S"] + st["F"] - st["O"]) - st["H"]
        for cid in sorted(passing[sid]):
            dom, ell, root = C.domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
            alive = unknown = 0
            best_s = None
            hv = {}
            for A in C.assignments(dom):
                counts["assignments"] += 1
                # 1단계: **가벼운** 그래프만 싸게 만들어 뿌리 여유 s 를 잰다.  비용-0 호는
                # 어떤 이동 집합에서도 `T1` 뿐이므로 s 는 완전-joint 값과 같다.
                _n, lout0, lout1, lr0, lr1 = C.weighted_graph(A, ell, root, jt)
                s = B - root_bound(lout0, lr0)
                slack[s] += 1
                best_s = s if best_s is None else max(best_s, s)
                if s < 0:
                    counts["assignment_UNSAT"] += 1
                    counts["closed_by_root_bound"] += 1
                    continue
                if s == 0:
                    # 무거운-호 예산 보조정리: 무거운 호를 하나도 쓸 수 없다 →
                    # 가벼운 탐색이 **완전**하다.  (H5) 가 이 인스턴스에서는 정리다.
                    counts["maxcost_allowed_1"] += 1
                    counts["assignments_where_H5_is_a_theorem"] += 1
                    v = C.solve(lout0, lout1, lr0, lr1, B, stats, node_cap=2_000_000)
                    counts[f"assignment_{v}"] += 1
                    if v == "SAT":
                        alive += 1
                    elif v == "UNKNOWN":
                        unknown += 1
                    continue
                nodes, out, rt = full_graph(A, ell, root, word, ident, mc, rot)
                # 강제-호 하한으로 무거운 호를 통째로 배제할 수 있는지 먼저 본다.
                m_ = len(nodes)
                succ, pred, arcs_, cycles_, cyc_id = free_structure(out[0], m_)
                keep0 = min(MAXC, s + 1)
                all_excluded = True
                for cc in range(2, keep0 + 1):
                    for i in range(m_):
                        t = out[cc][i]
                        while t and all_excluded:
                            low = t & -t
                            j = low.bit_length() - 1
                            t ^= low
                            if not heavy_arc_excluded(i, j, cc, B, m_, succ, pred,
                                                      arcs_, cycles_, cyc_id):
                                all_excluded = False
                        if not all_excluded:
                            break
                    if not all_excluded:
                        break
                if all_excluded:
                    counts["assignments_where_forced_arc_bound_kills_all_heavy"] += 1
                    counts["assignments_where_H5_is_a_theorem"] += 1
                    counts["maxcost_allowed_1"] += 1
                    v = C.solve(lout0, lout1, lr0, lr1, B, stats, node_cap=2_000_000)
                    counts[f"assignment_{v}"] += 1
                    if v == "SAT":
                        alive += 1
                    elif v == "UNKNOWN":
                        unknown += 1
                    continue
                # 라운드-108 무거운-호 예산 보조정리: cost - 1 <= s 인 호만 쓸 수 있다.
                keep = min(MAXC, s + 1)
                counts[f"maxcost_allowed_{keep}"] += 1
                if keep == 1:
                    counts["assignments_where_H5_is_a_theorem"] += 1
                for cc in range(keep + 1, MAXC + 1):
                    out[cc] = [0] * len(out[cc])
                    rt[cc] = 0
                v, hh = search(out, rt, B, stats, node_cap=args.node_cap, excess_budget=s)
                counts[f"assignment_{v}"] += 1
                if v == "SAT":
                    alive += 1
                    hv = hh
                elif v == "UNKNOWN":
                    unknown += 1
                    for k in hh:
                        heavy_total[k] += hh[k]
            verdict = "FAIL" if (alive == 0 and unknown == 0) else ("SAT" if alive else "UNKNOWN")
            counts[f"pair_{verdict}"] += 1
            per_state[sid].append(verdict)
            outrows.append({"sid": sid, "cover_id": cid, "B": B, "verdict": verdict,
                            "max_root_slack": best_s, "heavy_used": hv})
        done += 1
        if done % 5 == 0:
            print(f"  {done}/{len(targets)} states assign={counts['assignments']} "
                  f"{time.time()-t0:.0f}s", flush=True)

    survivors = [s for s, v in per_state.items() if any(x != "FAIL" for x in v)]
    rep = {
        "round": 108, "certifier": VERSION,
        "population": ("라운드-107 조건부 블록" if targets is conditional or args.conditional
                       else "전체"),
        "robust_states_round107": len(robust), "conditional_states_round107": len(conditional),
        "states_processed": len(targets),
        "assignments": counts["assignments"],
        "assignment_verdicts": {k.split("_", 1)[1]: v for k, v in counts.items()
                                if k.startswith("assignment_")},
        "closed_by_root_bound_alone": counts["closed_by_root_bound"],
        "pair_verdicts": {k.split("_", 1)[1]: v for k, v in counts.items()
                          if k.startswith("pair_")},
        "root_slack_histogram": dict(sorted(slack.items())),
        "max_arc_cost_allowed": {k.split("_")[-1]: v for k, v in counts.items()
                                 if k.startswith("maxcost_allowed_")},
        "assignments_where_H5_is_a_theorem": counts["assignments_where_H5_is_a_theorem"],
        "assignments_where_forced_arc_bound_kills_all_heavy": counts["assignments_where_forced_arc_bound_kills_all_heavy"],
        "max_arc_cost_allowed": {k.split("_")[-1]: v for k, v in counts.items()
                                 if k.startswith("maxcost_allowed_")},
        "assignments_where_H5_is_a_theorem": counts["assignments_where_H5_is_a_theorem"],
        "assignments_where_forced_arc_bound_kills_all_heavy": counts["assignments_where_forced_arc_bound_kills_all_heavy"],
        "assignments_with_zero_or_negative_slack": sum(v for k, v in slack.items() if k <= 0),
        "state_survivors": len(survivors), "survivor_sids": survivors[:20],
        "heavy_edges_in_surviving_paths": dict(heavy_total),
        "search_nodes": stats["nodes"], "cap_hits": counts["assignment_UNKNOWN"],
        "tails_used": len(TAILS) + 1,
        "seconds": round(time.time() - t0),
    }
    (OUT / args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    with gzip.open(OUT / "rr_full_joint_rows.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"schema": "rr_full_joint/1", "rows": len(outrows)},
                            ensure_ascii=False) + "\n")
        for r in outrows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
