#!/usr/bin/env python3
"""라운드 106 — Q2 잔여 0 **인증서**를 처음부터 다시 계산한다 (표준 라이브러리만).

이 파일은 `probe_rr_*` / `replay_rr_*` 어느 것도 import 하지 않는다.  라운드-93c 아카이브만
읽어 기하·필터·배정·가중 판정을 전부 새로 만든다.  마지막에 잔여가 0 이 아니면 **크게
실패**한다.

--------------------------------------------------------------------------------------
정리 1 (제한 성분 하한).  유향 그래프 `G` 의 간선에 비용 0/1 이 붙어 있고, ROOT 밖의 모든
정점 `v` 가 **비용-0 유출 차수 ≤ 1** 이라 하자.  정점 부분집합 `R` 위에서 비용-0 호들이
만드는 **약연결 성분**의 개수를 `c(R)` 이라 하면, 현재 정점 `x ∉ R` 에서 출발해 `R` 을 정확히
한 번씩 지나는 임의의 경로는 비용-1 호를 최소

        c(R) − 1        (`x` 에서 `R` 로 가는 비용-0 호가 있을 때)
        c(R)            (없을 때)

개 쓴다.

증명.  경로는 진입 호 1개와 내부 호 `|R|−1` 개를 쓴다.  내부 호 중 비용 0 인 것들의 집합
`F` 는 경로의 부분집합이므로 **선형 숲**이고, `|F| = y` 이면 그 성분 수는 `|R| − y` 다.
`F` 의 각 성분은 비용-0 호로 연결돼 있으므로 하나의 약연결 성분 안에 들어간다.  약연결 성분은
모두 덮여야 하므로 `|R| − y ≥ c(R)`, 즉 `y ≤ |R| − c(R)`.  따라서 내부 비용-1 호는
`(|R|−1) − y ≥ c(R) − 1` 개다.  진입 호가 비용 1 일 수밖에 없으면 하나 더 든다. ∎

**유출 차수 ≤ 1 이 왜 필요한가.**  이 가설이 없으면 `F` 의 성분이 약연결 성분을 세분한다는
사실은 여전히 참이지만, 구현이 성분을 세는 방식(정점마다 후속 하나만 병합)이 약연결 성분을
**과대계수**한다.  라운드 105 는 제한을 풀면 실제로 `솔버 UNSAT / 참 SAT` 반례가 나온다는
것을 전수 열거로 확인했다(42,052 쌍 중 111건).  아래 `_zero_out_degree_ok` 가 매 탐색
노드에서 가설을 확인한다.

정리 2 (Q2 에서 가설이 성립).  고정된 단어 배정에서 의무 `h` 의 진입 단어 `u` 는 하나이고,
강제된 `ℓ` 에서 `T1(u,ℓ)` 은 **문자열 하나**다.  그 단어가 속한 의무도 많아야 하나이므로
`h` 의 비용-0 유출 차수는 0 또는 1 이다.  게다가 라운드-99 기하 정리에 의해 네 joint target
은 **서로 다른 네 육각형**에 있으므로 다른 `T_i` 가 같은 의무로 겹쳐 들어오는 일도 없다. ∎

정리 3 (예산).  미래 pass 마다 `dS = [w ≥ 3]`, `dH = max(w−3,0)`, `dF = [abandonment]` 이고,
완성은 `O = 25` 를 만족해야 하므로 `ΔO = K = 25 − O`.  `ΔF = 0`(정리 4), `ΔH ≥ 0` 을 `= 0`
으로 **낙관적으로 완화**하면 `Ndef = S + F − O` 에서

        final(Ndef + H) = current(Ndef + H) + E − K,      E = weight-3 joint 개수

이고 `final(Ndef+H) ≤ 3` 이므로  **E ≤ B := 3 + K − Ndef − H.** ∎

정리 4 (`ΔF = 0`).  `ℓ = 5` pass 는 회전 뒤 커서의 σ-후속이 진입 단어이므로 이미 방문됐다.
fragment 수리(`ℓ = 5 − c_f`)는 회전이 조각의 미방문 부분을 정확히 채우고 끝나므로 σ-후속이
조각의 **이미 방문된** 칸이다.  두 경우 모두 abandonment 가 아니다.
(주의: `ℓ < 5` 라고 해서 일반적으로 참이 아니다 — 라운드 105 가 반증했다.  여기서 쓰는 것은
fragment 경계에 대한 명제뿐이고, 유한 인증서는 5,732/5,732 이다.)

입력 모집단 (§8).  이 인증서는 **라운드-93c 아카이브의 Hall 통과 쌍 전부**(`deficit = 0`)에서
출발한다.  라운드 96–102 의 층 A·B2·D1·D4b 로 이미 걸러진 19,176 쌍이 아니라 그 **상위집합**인
27,095 쌍 / 5,030 상태다.  상위집합에서 붕괴가 일어나면 그 층들에 대한 의존이 사라지므로
인증서가 더 강해진다.  아카이브 모집단으로 제한한 소계도 함께 보고해 4,230 / 15,781 과
대조한다(대조용일 뿐 판정에는 쓰지 않는다).

사용법:
    python3 src/certify_rr_q2_zero.py            # 전수 재계산
    python3 src/certify_rr_q2_zero.py --limit N  # 앞쪽 N 상태만 (개발용)
    python3 src/certify_rr_q2_zero.py --no-memo  # §12 메모 없는 대조 (--limit 과 함께)
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
OUT = ROOT / "outputs"
RT = ("root",)
VERSION = "claude-r106-certifier/1"


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        head = json.loads(fh.readline())
        return head, [json.loads(line) for line in fh]


# ------------------------------------------------------------------ 기하 (문자열)

def joint_words(x):
    return (x[2] + x[3] + x[4] + x[5] + x[1] + x[0],
            x[3] + x[4] + x[5] + x[1] + x[2] + x[0],
            x[3] + x[4] + x[5] + x[2] + x[0] + x[1],
            x[3] + x[4] + x[5] + x[2] + x[1] + x[0])


def geometry(audit=None):
    _h, geo = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    wid = {g["word"]: g["id"] for g in geo}
    word = {g["id"]: g["word"] for g in geo}
    orb = {g["id"]: g["orbit"] for g in geo}
    hexm = defaultdict(list)
    for g in geo:
        hexm[g["hexagon"]].append(g["id"])
    jt = {}
    for i, w in word.items():
        jt[i] = {e: tuple(wid[t] for t in joint_words(w[e:] + w[:e])) for e in range(6)}
    # 정리 2 의 기하 전제: 네 target 이 서로 다른 육각형 + 아카이브 표와의 대조
    hx = {g["id"]: g["hexagon"] for g in geo}
    ctx = mismatch = 0
    for g in geo:
        i = g["id"]
        for e in range(6):
            hs = [hx[v] for v in jt[i][e]]
            assert len(set(hs)) == 4, "기하 정리 위반: 네 joint target 이 4개 육각형이 아니다"
            assert hx[i] not in hs, "기하 정리 위반: target 이 source 육각형에 있다"
            ctx += 1
            if list(jt[i][e]) != list(g["joint_targets"][str(e)]):
                mismatch += 1
    # 육각형 = 회전류
    for h, ws in hexm.items():
        assert len(ws) == 6
        base = word[sorted(ws)[0]]
        assert {word[w] for w in ws} == {base[k:] + base[:k] for k in range(6)}
    if audit is not None:
        audit["geometry_contexts"] = ctx
        audit["geometry_archive_mismatches"] = mismatch
        audit["hexagon_is_rotation_class"] = True
    return word, orb, hexm, jt


# ------------------------------------------------------------------ 상태와 도메인

def domains(state, cover_orbits, orb, hexm):
    fin = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1} | set(cover_orbits)
    d = {("hex", h): {w for w in hexm[h] if orb[w] in fin}
         for h, m in enumerate(state["hex_masks"]) if m == 0}
    fr = state["fragment"]
    if fr:
        d[("frag",)] = {fr["entry_id"]}
    ell = {n: (fr["ell"] if n == ("frag",) else 5) for n in d}
    return d, ell, state["p_id"]


def propagate(dom, ell, root, jt):
    d = {k: set(v) for k, v in dom.items()}
    while True:
        own = {w: n for n, ws in d.items() for w in ws}
        keep = {v for v in jt[root][5] if v in own}
        for n, ws in d.items():
            for u in ws:
                for v in jt[u][ell[n]]:
                    if v in own and own[v] != n:
                        keep.add(v)
        changed = False
        for n in d:
            drop = d[n] - keep
            if drop:
                d[n] -= drop
                changed = True
            if not d[n]:
                return None
        if not changed:
            return d


def word_reachable_all(dom, ell, root, jt):
    """W-A — 모든 의무가 현재 구체 단어에서 단어 전이로 도달 가능한가."""
    own = {w: n for n, ws in dom.items() for w in ws}
    seen = {root}
    reached = set()
    stack = []
    for v in jt[root][5]:
        if v in own and v not in seen:
            seen.add(v)
            reached.add(own[v])
            stack.append(v)
    while stack:
        x = stack.pop()
        for v in jt[x][ell[own[x]]]:
            if v in own and v not in seen:
                seen.add(v)
                reached.add(own[v])
                stack.append(v)
    return len(reached) == len(dom)


def assignments(d):
    fixed = {n: next(iter(v)) for n, v in d.items() if len(v) == 1}
    binv = [(n, sorted(v)) for n, v in d.items() if len(v) == 2]
    assert all(len(v) <= 2 for v in d.values()), "도메인 크기 > 2"
    for pick in itertools.product((0, 1), repeat=len(binv)):
        A = dict(fixed)
        for (n, ws), c in zip(binv, pick):
            A[n] = ws[c]
        yield A


def weighted_graph(A, ell, root, jt):
    loc = {u: n for n, u in A.items()}
    nodes = list(A)
    idx = {n: i for i, n in enumerate(nodes)}
    m = len(nodes)
    out0 = [0] * m
    out1 = [0] * m
    for n, u in A.items():
        tg = jt[u][ell[n]]
        for i, v in enumerate(tg):
            g = loc.get(v)
            if g is None or g == n:
                continue
            if i == 0:
                out0[idx[n]] |= 1 << idx[g]
            else:
                out1[idx[n]] |= 1 << idx[g]
    r0 = r1 = 0
    for i, v in enumerate(jt[root][5]):
        g = loc.get(v)
        if g is None:
            continue
        if i == 0:
            r0 |= 1 << idx[g]
        else:
            r1 |= 1 << idx[g]
    return nodes, out0, out1, r0, r1


# ------------------------------------------------------------------ 가중 정확 탐색

def solve(out0, out1, r0, r1, B, stats, node_cap=2_000_000, use_memo=True,
          use_reach=True, use_bound=True):
    m = len(out0)
    full = (1 << m) - 1
    memo = {} if use_memo else None
    # 정리 2 의 가설을 그래프 전체에서 먼저 확인한다.
    for i in range(m):
        t = out0[i]
        stats["precondition_checks"] += 1
        if t & (t - 1):
            stats["precondition_violations"] += 1
            raise AssertionError("비용-0 유출 차수 > 1")

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

    def lower_bound(cur, rem):
        """정리 1 — 남은 집합의 비용-0 약연결 성분 수에서 나오는 하한."""
        idxs = list(bits(rem))
        par = {i: i for i in idxs}

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        for i in idxs:
            t = out0[i] & rem
            stats["dynamic_precondition_checks"] += 1
            if t & (t - 1):
                stats["precondition_violations"] += 1
                raise AssertionError("잔여 그래프에서 비용-0 유출 차수 > 1")
            if t:
                j = t.bit_length() - 1
                a, b = find(i), find(j)
                if a != b:
                    par[a] = b
        c = len({find(i) for i in idxs})
        return c - 1 if (out0[cur] & rem) else c

    def dfs(cur, rem, spent):
        stats["nodes"] += 1
        if stats["nodes"] > node_cap:
            raise TimeoutError
        if not rem:
            return True
        if memo is not None:
            prev = memo.get((cur, rem))
            if prev is not None and prev <= spent:
                return False
        if use_reach and reach(cur, rem) != rem:
            if memo is not None:
                memo[(cur, rem)] = 0
            return False
        if use_bound and spent + lower_bound(cur, rem) > B:
            stats["prune_cost"] += 1
            if memo is not None:
                memo[(cur, rem)] = spent
            return False
        for c, cand in ((0, out0[cur] & rem), (1, out1[cur] & rem)):
            if spent + c > B:
                continue
            for y in bits(cand):
                if dfs(y, rem & ~(1 << y), spent + c):
                    return True
        if memo is not None:
            memo[(cur, rem)] = spent
        return False

    sys.setrecursionlimit(20_000)
    try:
        for c, cand in ((0, r0), (1, r1)):
            if c > B:
                continue
            for y in bits(cand):
                if dfs(y, full & ~(1 << y), c):
                    return "SAT"
        return "UNSAT"
    except TimeoutError:
        return "UNKNOWN"
    except RecursionError:
        return "UNKNOWN"


# ------------------------------------------------------------------------- 실행

def root_lower_bound(out0, r0):
    """뿌리에서의 정리-1 하한 (진단용).  ROOT 는 성분에 넣지 않는다."""
    m = len(out0)
    par = list(range(m))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for i, t in enumerate(out0):
        if t:
            j = t.bit_length() - 1
            a, b = find(i), find(j)
            if a != b:
                par[a] = b
    c = len({find(i) for i in range(m)})
    return c - 1 if r0 else c


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-memo", action="store_true")
    ap.add_argument("--budget-delta", type=int, default=0,
                    help="§16 구제 진단: B 를 이만큼 키운다 (인증서로 쓰지 않는다)")
    ap.add_argument("--out", default="rr_q2_zero_certificate.json")
    ap.add_argument("--cert-out", default="rr_q2_zero_certificate.jsonl.gz")
    args = ap.parse_args()
    t0 = time.time()
    audit = {}
    word, orb, hexm, jt = geometry(audit)
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    _h, covers = read_jsonl(ARCHIVE / "covers.jsonl.gz")
    _h, hall = read_jsonl(ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])
    audit["archive_states"] = len(states)
    audit["hall_pairs_total"] = len(hall)
    audit["hall_passing_pairs"] = sum(len(v) for v in passing.values())
    audit["hall_passing_states"] = len(passing)

    # §7 — K 를 상태 레코드에서 독립적으로 재검증한다.
    kbad = [s["sid"] for s in states if s["K"] != 25 - s["O"]]
    audit["K_equals_25_minus_O_violations"] = len(kbad)
    audit["budget_histogram"] = dict(sorted(Counter(
        3 + s["K"] - (s["S"] + s["F"] - s["O"]) - s["H"] for s in states).items()))

    # 대조용 (판정에는 쓰지 않는다): 라운드-100 아카이브의 A·B2·D1·D4b 통과 모집단
    pop = set()
    try:
        _h, apairs = read_jsonl(OUT / "rr_word_lift_archive" / "pairs.jsonl.gz")
        pop = {(p["sid"], p["cover_id"]) for p in apairs}
    except OSError:
        pass

    stats = Counter()
    counts = Counter()
    rows = []
    per_state = defaultdict(list)
    sub_state = defaultdict(list)      # 아카이브 모집단으로 제한
    root_margin = Counter()
    node_hist = []
    branch_nodes = []
    processed = 0
    for sid in sorted(passing):
        st = S[sid]
        B = 3 + st["K"] - (st["S"] + st["F"] - st["O"]) - st["H"] + args.budget_delta
        kept = []
        for cid in sorted(passing[sid]):
            dom, ell, root = domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
            counts["wa_input_pairs"] += 1
            if not word_reachable_all(dom, ell, root, jt):
                counts["wa_fail_pairs"] += 1
                continue
            kept.append((cid, dom, ell, root))
        if not kept:
            counts["wa_closed_states"] += 1
            continue
        counts["wa_states"] += 1
        counts["wa_pairs"] += len(kept)
        if any((sid, cid) in pop for cid, *_ in kept):
            counts["wa_states_in_archive_pop"] += 1
        counts["wa_pairs_in_archive_pop"] += sum(1 for cid, *_ in kept if (sid, cid) in pop)
        for cid, dom, ell, root in kept:
            d = propagate(dom, ell, root, jt)
            if d is None:
                counts["pair_FAIL"] += 1
                counts["pair_FAIL_by_propagate"] += 1
                per_state[sid].append("FAIL")
                rows.append({"sid": sid, "cover_id": cid, "B": B, "obligations": len(dom),
                             "assignments": 0, "min_root_bound": None,
                             "verdict": "FAIL", "reason": "empty_domain"})
                if (sid, cid) in pop:
                    sub_state[sid].append("FAIL")
                continue
            alive = unknown = 0
            best_lb = None
            n0 = stats["nodes"]
            a0 = counts["assignments"]
            for A in assignments(d):
                counts["assignments"] += 1
                nodes, out0, out1, r0, r1 = weighted_graph(A, ell, root, jt)
                lb = root_lower_bound(out0, r0)
                best_lb = lb if best_lb is None else min(best_lb, lb)
                v = solve(out0, out1, r0, r1, B, stats, use_memo=not args.no_memo)
                counts[f"assignment_{v}"] += 1
                if v == "SAT":
                    alive += 1
                elif v == "UNKNOWN":
                    unknown += 1
            used = stats["nodes"] - n0
            node_hist.append(used)
            root_margin[best_lb - B] += 1
            if best_lb > B:
                counts["pairs_closed_by_root_bound"] += 1
            else:
                branch_nodes.append(used)
            verdict = "FAIL" if (alive == 0 and unknown == 0) else ("SAT" if alive else "UNKNOWN")
            counts[f"pair_{verdict}"] += 1
            per_state[sid].append(verdict)
            rows.append({"sid": sid, "cover_id": cid, "B": B, "obligations": len(d),
                         "assignments": counts["assignments"] - a0,
                         "min_root_bound": best_lb, "verdict": verdict,
                         "reason": "root_bound" if best_lb > B else "exhaustive_search"})
            if (sid, cid) in pop:
                sub_state[sid].append(verdict)
        processed += 1
        if processed % 250 == 0:
            print(f"  {processed} states pairs={counts['wa_pairs']} "
                  f"assign={counts['assignments']} {time.time()-t0:.0f}s", flush=True)
        if args.limit and processed >= args.limit:
            break

    survivors = [s for s, vs in per_state.items() if any(v != "FAIL" for v in vs)]
    sub_surv = [s for s, vs in sub_state.items() if any(v != "FAIL" for v in vs)]
    node_hist.sort()
    branch_nodes.sort()

    def med(xs):
        return xs[len(xs) // 2] if xs else 0

    report = {
        "round": 106, "certifier": VERSION,
        "population": "라운드-93c Hall 통과 쌍 전부 (A·B2·D1·D4b 를 쓰지 않은 상위집합)",
        "budget_delta": args.budget_delta, "memo": not args.no_memo,
        "audit": audit,
        "wa_input_pairs": counts["wa_input_pairs"],
        "wa_fail_pairs": counts["wa_fail_pairs"],
        "wa_closed_states": counts["wa_closed_states"],
        "wa_states": counts["wa_states"], "wa_pairs": counts["wa_pairs"],
        "wa_states_in_archive_pop": counts["wa_states_in_archive_pop"],
        "wa_pairs_in_archive_pop": counts["wa_pairs_in_archive_pop"],
        "assignments": counts["assignments"],
        "assignment_verdicts": {k.split("_", 1)[1]: v for k, v in counts.items()
                                if k.startswith("assignment_")},
        "pair_verdicts": {k.split("_", 1)[1]: v for k, v in counts.items()
                          if k.startswith("pair_") and not k.endswith("by_propagate")},
        "pairs_failed_by_propagation_alone": counts["pair_FAIL_by_propagate"],
        "state_survivors": len(survivors),
        "state_survivors_archive_pop": len(sub_surv),
        "pairs_closed_by_root_bound": counts["pairs_closed_by_root_bound"],
        "pairs_needing_branching": counts["wa_pairs"] - counts["pairs_closed_by_root_bound"],
        "search_nodes_total": stats["nodes"],
        "search_nodes_max_per_pair": node_hist[-1] if node_hist else 0,
        "search_nodes_median_per_pair": med(node_hist),
        "branching_pairs_nodes_max": branch_nodes[-1] if branch_nodes else 0,
        "branching_pairs_nodes_median": med(branch_nodes),
        "branching_pairs_nodes_total": sum(branch_nodes),
        "precondition_checks": stats["precondition_checks"],
        "dynamic_precondition_checks": stats["dynamic_precondition_checks"],
        "precondition_violations": stats["precondition_violations"],
        "cap_hits": counts["assignment_UNKNOWN"],
        "root_margin_histogram": dict(sorted(root_margin.items())),
        "seconds": round(time.time() - t0),
    }
    (OUT / args.out).write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.cert_out:
        with gzip.open(OUT / args.cert_out, "wt") as fh:
            head = {"schema": "rr_q2_zero_certificate/1", "certifier": VERSION,
                    "rows": len(rows), "states": report["wa_states"],
                    "state_survivors": report["state_survivors"],
                    "note": "각 행은 (상태, cover) 쌍의 가중 판정이다. FAIL = 예산 안의 "
                            "rooted Hamilton 경로 없음."}
            fh.write(json.dumps(head, ensure_ascii=False) + "\n")
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if report["precondition_violations"]:
        raise SystemExit("전제 위반 — 인증서 무효")
    if report["cap_hits"]:
        raise SystemExit("캡 도달 — 완전 소진이 아니다")
    if report["state_survivors"] != 0 and not (args.limit or args.budget_delta):
        raise SystemExit(f"잔여가 0 이 아니다: {report['state_survivors']}")
    print("CERTIFICATE OK — 남은 상태 0")


if __name__ == "__main__":
    main()
