#!/usr/bin/env python3
"""라운드 106 — Q2 잔여 0 인증서의 **독립 검증기** (§17).

`certify_rr_q2_zero.py` 를 import 하지 않는다.  기하·도메인·전파·배정·가중 그래프·정확 탐색을
전부 **다시 구현**하고, 인증서 파일이 주장하는 모든 행을 재판정한다.  구현 차이를 실제로
만들기 위해 이 파일은

  * 성분 수를 union-find 가 아니라 **사슬 추적**으로 센다,
  * 탐색을 인접 비트마스크가 아니라 **인접 리스트 + 비용 오름차순** 으로 돈다,
  * 메모 키를 `(cur, rem)` 이 아니라 `(cur, frozenset)` 으로 잡는다,

즉 같은 정리를 쓰되 같은 코드를 쓰지 않는다.

성공 조건 — 전부 만족해야 한다:
  1. 인증서의 모든 행이 재판정에서 같은 판정을 받는다 (UNKNOWN 허용 안 함).
  2. Hall 통과 상태 전부가 인증서에 나타난다 (누락 0).
  3. 어떤 상태도 살아남은 cover 를 갖지 않는다 → **remaining states = 0**.
어긋나면 큰 소리로 실패한다.

사용법:
    python3 src/verify_rr_q2_zero.py
    python3 src/verify_rr_q2_zero.py --limit 200     # 개발용 부분 검증
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
OUT = ROOT / "outputs"
VERSION = "claude-r106-verifier/1"


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        head = json.loads(fh.readline())
        return head, [json.loads(line) for line in fh]


# --------------------------------------------------------------------- 기하 재구성

def rot(w, e):
    return w[e:] + w[:e]


def targets(w):
    """네 joint target 문자열.  T1 이 유일한 비용-0 (weight 2) target 이다."""
    return [w[2] + w[3] + w[4] + w[5] + w[1] + w[0],
            w[3] + w[4] + w[5] + w[1] + w[2] + w[0],
            w[3] + w[4] + w[5] + w[2] + w[0] + w[1],
            w[3] + w[4] + w[5] + w[2] + w[1] + w[0]]


def build():
    _h, geo = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    ident = {g["word"]: g["id"] for g in geo}
    word = {g["id"]: g["word"] for g in geo}
    orbit = {g["id"]: g["orbit"] for g in geo}
    hexof = {g["id"]: g["hexagon"] for g in geo}
    inhex = defaultdict(list)
    for g in geo:
        inhex[g["hexagon"]].append(g["id"])
    tgt = {}
    for i, w in word.items():
        tgt[i] = [[ident[t] for t in targets(rot(w, e))] for e in range(6)]
        for e in range(6):
            hs = {hexof[v] for v in tgt[i][e]}
            if len(hs) != 4 or hexof[i] in hs:
                raise SystemExit("기하 정리 위반")
    return word, orbit, hexof, inhex, tgt


# ------------------------------------------------------------------ 문맥 / 전파 재구성

def context(state, cover, orbit, inhex):
    live = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1}
    live.update(cover)
    dom = {}
    for h, m in enumerate(state["hex_masks"]):
        if m == 0:
            dom[("hex", h)] = {w for w in inhex[h] if orbit[w] in live}
    ell = {n: 5 for n in dom}
    fr = state["fragment"]
    if fr:
        dom[("frag",)] = {fr["entry_id"]}
        ell[("frag",)] = fr["ell"]
    return dom, ell, state["p_id"]


def prune(dom, ell, root, tgt):
    """전임자 지지 규칙 고정점 — 인증기와 같은 필요조건, 다른 순서."""
    dom = {k: set(v) for k, v in dom.items()}
    for _ in range(200):
        owner = {}
        for n, ws in dom.items():
            for w in ws:
                owner[w] = n
        supported = set()
        for v in tgt[root][5]:
            if v in owner:
                supported.add(v)
        for n, ws in dom.items():
            for u in ws:
                for v in tgt[u][ell[n]]:
                    if v in owner and owner[v] != n:
                        supported.add(v)
        shrunk = False
        for n in list(dom):
            new = dom[n] & supported
            if new != dom[n]:
                dom[n] = new
                shrunk = True
            if not dom[n]:
                return None
        if not shrunk:
            return dom
    raise SystemExit("전파가 수렴하지 않았다")


def reachable(dom, ell, root, tgt):
    owner = {w: n for n, ws in dom.items() for w in ws}
    hit = set()
    seen = set()
    front = [v for v in tgt[root][5] if v in owner]
    while front:
        nxt = []
        for v in front:
            if v in seen:
                continue
            seen.add(v)
            hit.add(owner[v])
            nxt.extend(u for u in tgt[v][ell[owner[v]]] if u in owner and u not in seen)
        front = nxt
    return len(hit) == len(dom)


# ------------------------------------------------------------------- 그래프 / 탐색

def graph(A, ell, root, tgt):
    """인접 **리스트** 표현: adj[n] = [(cost, m), ...]."""
    home = {u: n for n, u in A.items()}
    adj = {n: [] for n in A}
    for n, u in A.items():
        for i, v in enumerate(tgt[u][ell[n]]):
            m = home.get(v)
            if m is None or m == n:
                continue
            adj[n].append((0 if i == 0 else 1, m))
    start = []
    for i, v in enumerate(tgt[root][5]):
        m = home.get(v)
        if m is not None:
            start.append((0 if i == 0 else 1, m))
    for n in adj:
        adj[n].sort()
    start.sort()
    return adj, start


def zero_succ(adj):
    """비용-0 후속.  가설(유출 차수 ≤ 1) 위반이면 즉시 실패한다."""
    z = {}
    for n, outs in adj.items():
        cand = [m for c, m in outs if c == 0]
        if len(cand) > 1:
            raise SystemExit(f"가설 위반: {n} 의 비용-0 유출 차수 {len(cand)}")
        if cand:
            z[n] = cand[0]
    return z


def components(z, rem):
    """사슬 추적으로 비용-0 약연결 성분 수 (union-find 미사용)."""
    back = defaultdict(list)
    for a in rem:
        b = z.get(a)
        if b in rem:
            back[b].append(a)
    seen = set()
    comps = 0
    for s in rem:
        if s in seen:
            continue
        comps += 1
        stack = [s]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            b = z.get(v)
            if b in rem and b not in seen:
                stack.append(b)
            for a in back.get(v, ()):
                if a not in seen:
                    stack.append(a)
    return comps


def search(adj, start, B, cap=2_000_000):
    z = zero_succ(adj)
    allv = frozenset(adj)
    nodes = [0]
    memo = {}

    def bound(cur, rem):
        c = components(z, rem)
        return c - 1 if z.get(cur) in rem else c

    def go(cur, rem, spent):
        nodes[0] += 1
        if nodes[0] > cap:
            raise TimeoutError
        if not rem:
            return True
        key = (cur, rem)
        prev = memo.get(key)
        if prev is not None and prev <= spent:
            return False
        # 도달성
        seen = {cur}
        front = [cur]
        while front:
            nx = []
            for v in front:
                for _c, m in adj[v]:
                    if m in rem and m not in seen:
                        seen.add(m)
                        nx.append(m)
            front = nx
        if len(seen & rem) != len(rem):
            memo[key] = 0
            return False
        if spent + bound(cur, rem) > B:
            memo[key] = spent
            return False
        for c, m in adj[cur]:
            if m in rem and spent + c <= B:
                if go(m, rem - {m}, spent + c):
                    return True
        memo[key] = spent
        return False

    sys.setrecursionlimit(20_000)
    try:
        for c, m in start:
            if c <= B and go(m, allv - {m}, c):
                return "SAT", nodes[0]
        return "UNSAT", nodes[0]
    except (TimeoutError, RecursionError):
        return "UNKNOWN", nodes[0]


def assignments(dom):
    fixed = {n: next(iter(v)) for n, v in dom.items() if len(v) == 1}
    free = [(n, sorted(v)) for n, v in dom.items() if len(v) > 1]
    for n, v in free:
        if len(v) > 2:
            raise SystemExit("도메인 크기 > 2 — 인증서 가정 위반")
    for pick in itertools.product((0, 1), repeat=len(free)):
        A = dict(fixed)
        for (n, ws), c in zip(free, pick):
            A[n] = ws[c]
        yield A


# ------------------------------------------------------------------------- 실행

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cert", default="rr_q2_zero_certificate.jsonl.gz")
    args = ap.parse_args()
    t0 = time.time()
    _word, orbit, _hexof, inhex, tgt = build()
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    _h, covers = read_jsonl(ARCHIVE / "covers.jsonl.gz")
    _h, hall = read_jsonl(ARCHIVE / "hall_results.jsonl.gz")
    head, rows = read_jsonl(OUT / args.cert)
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    claimed = {(r["sid"], r["cover_id"]): r for r in rows}

    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])

    stat = Counter()
    alive_states = set()
    missing = []
    processed = 0
    for sid in sorted(passing):
        st = S[sid]
        B = 3 + st["K"] - (st["S"] + st["F"] - st["O"]) - st["H"]
        for cid in sorted(passing[sid]):
            dom, ell, root = context(st, CV[(sid, cid)]["orbits"], orbit, inhex)
            if not reachable(dom, ell, root, tgt):
                stat["closed_by_word_reachability"] += 1
                if (sid, cid) in claimed:
                    stat["ERROR_cert_row_for_wa_failed_pair"] += 1
                continue
            row = claimed.get((sid, cid))
            if row is None:
                missing.append([sid, cid])
                continue
            if row["B"] != B:
                stat["ERROR_budget_mismatch"] += 1
            d = prune(dom, ell, root, tgt)
            if d is None:
                stat["reverified_empty_domain"] += 1
                if row["verdict"] != "FAIL":
                    stat["ERROR_verdict_mismatch"] += 1
                continue
            worst = "FAIL"
            for A in assignments(d):
                adj, start = graph(A, ell, root, tgt)
                v, n = search(adj, start, B)
                stat["assignments"] += 1
                stat["nodes"] += n
                stat[f"assignment_{v}"] += 1
                if v != "UNSAT":
                    worst = v
                    break
            if worst != "FAIL":
                stat["ERROR_pair_not_closed"] += 1
                alive_states.add(sid)
            if worst != row["verdict"]:
                stat["ERROR_verdict_mismatch"] += 1
            stat["pairs_reverified"] += 1
        processed += 1
        if processed % 250 == 0:
            print(f"  {processed} states pairs={stat['pairs_reverified']} "
                  f"assign={stat['assignments']} {time.time()-t0:.0f}s", flush=True)
        if args.limit and processed >= args.limit:
            break

    errors = {k: v for k, v in stat.items() if k.startswith("ERROR")}
    report = {"round": 106, "verifier": VERSION, "certificate_header": head,
              "states_walked": processed, "missing_certificate_rows": len(missing),
              "missing_examples": missing[:5],
              "stats": {k: v for k, v in sorted(stat.items())},
              "errors": errors, "remaining_states": len(alive_states),
              "seconds": round(time.time() - t0)}
    (OUT / "rr_q2_zero_verify.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if errors or missing:
        raise SystemExit("검증 실패 — 인증서를 신뢰할 수 없다")
    if stat["assignment_UNKNOWN"]:
        raise SystemExit("UNKNOWN 발생 — 완전 소진이 아니다")
    if alive_states:
        raise SystemExit(f"remaining states = {len(alive_states)}")
    if not args.limit:
        print("VERIFIED — remaining states = 0")
    else:
        print(f"PARTIAL VERIFY OK ({processed} states) — remaining states = 0")


if __name__ == "__main__":
    main()
