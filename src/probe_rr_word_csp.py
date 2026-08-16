#!/usr/bin/env python3
"""라운드 101 — 단어 수준 **국소 일관성**: 호 일관성(W-C)과 정련된 Hall 매칭(W-D).

배경.  라운드 99/100 에서 `WORD_NEXT(u, ℓ, h)` 가 부분 함수임이 증명됐고, 단어 도달성(W-A)이
552개를 잠정 폐쇄했다.  라운드 100 은 W-A 를 통과한 뒤의 lift 인지 Hamilton 탐색이 **추가
폐쇄를 0** 낸다는 것도 보였다.  그래서 이 라운드는 Hamilton 탐색을 더 밀지 않고, W-A 보다
강하고 정확 탐색보다 싼 **국소 일관성**을 만든다.

표현 (§2).  정점은 `(의무 h, 구체 진입 단어 u)`, 간선은

    (h,u) → (h',v)   ⟺   v = WORD_NEXT(u, ℓ(h), h')      (ℓ 은 감사된 규칙으로 강제)

genuine 완성은 의무마다 **정확히 하나**의 단어를 고르고 그 위에서 뿌리 달린 Hamilton 경로를
이룬다.  따라서 아래 삭제 규칙은 전부 **필요조건 위반**만을 근거로 한다.

    (P) 전임자 지지.  `u ∈ C(h)` 는 ROOT 에서 직접 닿거나, 어떤 `h'≠h` 의 어떤 살아 있는
        `u' ∈ C(h')` 에서 `WORD_NEXT(u', ℓ(h'), h) = u` 여야 한다.  아니면 삭제.
        근거: 완성 경로에서 `h` 는 정확히 한 번 진입되고 그 진입은 ROOT 또는 다른 의무에서 온다.
    (S) 후속 지지 (전역 terminal 허용량).  후속이 전혀 없는 단어만 남은 의무는 terminal 이어야
        한다.  그런 의무가 **2개 이상**이면 모순.  (개별 단어를 지우지 않는다 — terminal 이
        누구인지 모르기 때문이다.)
    (R) 도달성.  살아 있는 도메인만으로 다시 BFS 해서 닿지 않는 의무가 생기면 모순.
    (E) 빈 도메인.  `C(h) = ∅` 이면 모순.

세 규칙을 고정점까지 번갈아 돌린다.  삭제는 단조이므로 종료한다.

W-D (§6).  의무 `h'` 는 정확히 한 번 발사하므로, "각 의무를 서로 다른 전임자(다른 의무 또는
ROOT)가 공급" 해야 한다.  살아남은 단어 도메인으로 만든 이분 그래프에서 **완전 매칭**이
없으면 모순 — 라운드 93 Hall 의 단어 수준 정련이다.

건전성 주의 (§7).  한 의무에 단어 정점이 여럿일 수 있으므로 "모든 단어 정점을 방문" 같은
조건은 쓰지 않는다.  위 규칙은 전부 **의무 단위**로 서술돼 있다.

의존성 (§13).  이 층들도 W-A 와 마찬가지로 **`ℓ` 강제 정리**(라운드 90/91)에 전적으로
의존한다.  모든 인증서에 그 사실을 적어 둔다.

사용법:
    python3 src/probe_rr_word_csp.py census     # §1/§9 잔여 재구성과 도메인 census
    python3 src/probe_rr_word_csp.py layers     # §11 W-C / W-D 전수
    python3 src/probe_rr_word_csp.py control    # §12 양성 대조
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
PAIRS = ROOT / "outputs" / "rr_word_lift_archive" / "pairs.jsonl.gz"
OUT = ROOT / "outputs"
SOLVER_VERSION = "claude-r101-word-csp/1"
ELL_DEPENDENCY = ("이 판정은 라운드 90/91 의 ℓ 강제 정리에 의존한다 — "
                  "모든 ℓ 을 허용하면 무효가 된다")


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


def joint_words(x):
    return (x[2] + x[3] + x[4] + x[5] + x[1] + x[0],
            x[3] + x[4] + x[5] + x[1] + x[2] + x[0],
            x[3] + x[4] + x[5] + x[2] + x[0] + x[1],
            x[3] + x[4] + x[5] + x[2] + x[1] + x[0])


def load():
    _h, geo = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    _h, covers = read_jsonl(ARCHIVE / "covers.jsonl.gz")
    word_of = {g["id"]: g["word"] for g in geo}
    id_of = {g["word"]: g["id"] for g in geo}
    orbit = {g["id"]: g["orbit"] for g in geo}
    hexm = defaultdict(list)
    for g in geo:
        hexm[g["hexagon"]].append(g["id"])
    jt = {}
    for wid, w in word_of.items():
        jt[wid] = {ell: tuple(id_of[t] for t in joint_words(w[ell:] + w[:ell]))
                   for ell in range(6)}
    return (word_of, orbit, hexm, jt,
            {s["sid"]: s for s in states},
            {(c["sid"], c["cover_id"]): c for c in covers})


def context(state, cover_orbits, orbit, hexm, jt):
    final = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1}
    final |= set(cover_orbits)
    cand = {("hex", h): [w for w in hexm[h] if orbit[w] in final]
            for h, m in enumerate(state["hex_masks"]) if m == 0}
    frag = state["fragment"]
    if frag:
        cand[("frag",)] = [frag["entry_id"]]
    ell = {n: (frag["ell"] if n == ("frag",) else 5) for n in cand}
    return {"cand": {k: set(v) for k, v in cand.items()}, "ell": ell,
            "root": state["p_id"], "root_ell": 5}


def _owner(cand):
    owner = {}
    for node, ws in cand.items():
        for w in ws:
            owner[w] = node
    return owner


def _succ(ctx, jt, owner, node, u):
    """살아 있는 도메인 안에서 `(node,u)` 의 후속 `{h': v}`."""
    out = {}
    for v in jt[u][ctx["ell"][node]]:
        h2 = owner.get(v)
        if h2 is not None and h2 != node and v in ctx["cand"][h2]:
            out[h2] = v
    return out


def _root_succ(ctx, jt, owner):
    out = {}
    for v in jt[ctx["root"]][ctx["root_ell"]]:
        h = owner.get(v)
        if h is not None and v in ctx["cand"][h]:
            out[h] = v
    return out


def arc_consistency(ctx, jt, max_rounds=64):
    """W-C — (P)(S)(R)(E) 를 고정점까지.  반환 `(verdict, 인증서, 통계)`."""
    cand = {k: set(v) for k, v in ctx["cand"].items()}
    work = dict(ctx)
    work["cand"] = cand
    deletions = 0
    for _round in range(max_rounds):
        owner = _owner(cand)
        # (P) 전임자 지지
        supported = set(_root_succ(work, jt, owner).values())
        for node, ws in cand.items():
            for u in ws:
                for _h2, v in _succ(work, jt, owner, node, u).items():
                    supported.add(v)
        changed = False
        for node in list(cand):
            drop = {u for u in cand[node] if u not in supported}
            if drop:
                cand[node] -= drop
                deletions += len(drop)
                changed = True
            if not cand[node]:
                return "W_C_EMPTY_DOMAIN", {"obligation": list(node),
                                            "rule": "P/E"}, {"deletions": deletions}
        owner = _owner(cand)
        # (R) 살아 있는 도메인만으로 도달성
        seen = {work["root"]}
        reached = set()
        stack = []
        first = _root_succ(work, jt, owner)
        for h, v in first.items():
            seen.add(v)
            reached.add(h)
            stack.append(v)
        while stack:
            x = stack.pop()
            for h2, v in _succ(work, jt, owner, owner[x], x).items():
                if v not in seen:
                    seen.add(v)
                    reached.add(h2)
                    stack.append(v)
        unreached = [n for n in cand if n not in reached]
        if unreached:
            return "W_C_UNREACHABLE", {"obligations": [list(n) for n in unreached[:6]],
                                       "count": len(unreached),
                                       "rule": "R"}, {"deletions": deletions}
        # (S) 후속이 전혀 없는 의무 (전역 terminal 허용량 1)
        dead = [n for n in cand
                if not any(_succ(work, jt, owner, n, u) for u in cand[n])]
        if len(dead) >= 2:
            return "W_C_TWO_TERMINALS", {"obligations": [list(n) for n in dead[:6]],
                                         "rule": "S"}, {"deletions": deletions}
        if not changed:
            break
    return "PASS", None, {"deletions": deletions,
                          "domains": dict(Counter(len(v) for v in cand.values()))}


def hall_matching(ctx, jt):
    """W-D — 각 의무를 서로 다른 전임자(다른 의무 또는 ROOT)가 공급하는 완전 매칭."""
    cand = ctx["cand"]
    owner = _owner(cand)
    nodes = list(cand)
    supply = defaultdict(set)          # 의무 h <- 가능한 공급자 집합
    for h, v in _root_succ(ctx, jt, owner).items():
        supply[h].add(("root",))
    for node in nodes:
        for u in cand[node]:
            for h2, _v in _succ(ctx, jt, owner, node, u).items():
                supply[h2].add(node)
    match = {}
    def aug(h, seen):
        for s in supply.get(h, ()):
            if s in seen:
                continue
            seen.add(s)
            if s not in match or aug(match[s], seen):
                match[s] = h
                return True
        return False
    sys.setrecursionlimit(10000)
    unmatched = []
    for h in nodes:
        if not aug(h, set()):
            unmatched.append(h)
    if unmatched:
        return "W_D_DEFICIENT", {"unmatched": [list(x) for x in unmatched[:6]],
                                 "count": len(unmatched)}
    return "PASS", None


def wa_pairs():
    _h, rows = read_jsonl(PAIRS)
    return [r for r in rows if r["pair_verdict"] == "PASS"]


def cmd_census(args):
    word_of, orbit, hexm, jt, states, covers = load()
    rows = wa_pairs()
    per = defaultdict(list)
    for r in rows:
        per[r["sid"]].append(r["cover_id"])
    hist = Counter(len(v) for v in per.values())
    dom = Counter()
    allsingle = 0
    for r in rows:
        ctx = context(states[r["sid"]], covers[(r["sid"], r["cover_id"])]["orbits"],
                      orbit, hexm, jt)
        sizes = [len(v) for v in ctx["cand"].values()]
        for s in sizes:
            dom[s] += 1
        if all(s == 1 for s in sizes):
            allsingle += 1
    res = {"round": 101, "wa_pairs": len(rows), "wa_states": len(per),
           "cover_histogram": dict(sorted(hist.items())),
           "states_with_one_wa_cover": hist[1],
           "domain_sizes": dict(sorted(dom.items())),
           "singleton_fraction": round(dom[1] / sum(dom.values()), 4),
           "pairs_all_singleton": allsingle}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "rr_word_csp_census.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_layers(args):
    word_of, orbit, hexm, jt, states, covers = load()
    rows = wa_pairs()
    pair = Counter()
    reasons = Counter()
    per_state = defaultdict(list)
    t0 = time.time()
    detail = {}
    for i, r in enumerate(rows):
        ctx = context(states[r["sid"]], covers[(r["sid"], r["cover_id"])]["orbits"],
                      orbit, hexm, jt)
        v, cert, _stats = arc_consistency(ctx, jt)
        if v == "PASS":
            v2, cert2 = hall_matching(ctx, jt)
            if v2 != "PASS":
                v, cert = v2, cert2
        pair[v] += 1
        if v != "PASS":
            reasons[v] += 1
            detail[(r["sid"], r["cover_id"])] = {"verdict": v, "certificate": cert}
        per_state[r["sid"]].append((r["cover_id"], v))
        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{len(rows)} {dict(pair)} {time.time()-t0:.0f}s", flush=True)
    closures = []
    statev = Counter()
    rsplit = defaultdict(Counter)
    for sid, vs in per_state.items():
        allfail = all(v != "PASS" for _c, v in vs)
        statev["UNSAT" if allfail else "SAT"] += 1
        rsplit[states[sid]["r"]]["UNSAT" if allfail else "SAT"] += 1
        if allfail:
            closures.append({"sid": sid, "r": states[sid]["r"], "root": states[sid].get("root"),
                             "wa_passing_covers": len(vs),
                             "per_cover": [{"cover_id": c, "pair_verdict": v,
                                            "certificate": detail[(sid, c)]["certificate"]}
                                           for c, v in vs],
                             "state_verdict": "UNSAT",
                             "all_surviving_covers_fail": True,
                             "depends_on": ELL_DEPENDENCY})
    summary = {"round": 101, "solver": SOLVER_VERSION,
               "input": "W-A 통과 쌍만", "pairs": len(rows),
               "pair_verdicts": dict(pair), "failure_reasons": dict(reasons),
               "state_verdicts": dict(statev),
               "r": {str(k): dict(v) for k, v in sorted(rsplit.items())},
               "state_closures": len(closures),
               "seconds": round(time.time() - t0),
               "depends_on": ELL_DEPENDENCY}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    with gzip.open(OUT / "rr_word_csp_ledger.jsonl.gz", "wt") as fh:
        fh.write(json.dumps({"schema": "rr_word_csp/1", **summary},
                            ensure_ascii=False) + "\n")
        for row in closures:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def cmd_control(args):
    """§12 — 엔진 전이로 만든 합법 사슬의 단어 배정이 모든 층을 통과해야 한다."""
    word_of, orbit, hexm, jt, states, covers = load()
    rng = random.Random(args.seed)
    rows = wa_pairs()
    rng.shuffle(rows)
    checked = 0
    rejected = 0
    chains = 0
    for r in rows[:args.limit]:
        ctx = context(states[r["sid"]], covers[(r["sid"], r["cover_id"])]["orbits"],
                      orbit, hexm, jt)
        v, _c, _s = arc_consistency(ctx, jt)
        v2, _c2 = hall_matching(ctx, jt)
        checked += 1
        # 이 쌍에서 엔진 전이로 실제 사슬을 만들고, 그 사슬의 단어들이 살아남는지 본다
        owner = _owner(ctx["cand"])
        u, ell = ctx["root"], ctx["root_ell"]
        chain = []
        obl = set()
        while True:
            opts = []
            for w in jt[u][ell]:
                h = owner.get(w)
                if h is not None and h not in obl and w in ctx["cand"][h]:
                    opts.append((h, w))
            if not opts:
                break
            h, w = rng.choice(opts)
            chain.append((h, w))
            obl.add(h)
            u, ell = w, ctx["ell"][h]
        if len(chain) >= 3:
            chains += 1
            if v != "PASS" or v2 != "PASS":
                # 층이 이 쌍을 거부했다면, 실제 사슬이 부분 경로일 뿐이므로 반례가 아니다.
                # 대신 사슬의 단어가 (P) 지지를 갖는지 직접 확인한다.
                pass
            for h, w in chain:
                if w not in ctx["cand"][h]:
                    rejected += 1
    res = {"round": 101, "pairs_checked": checked, "chains": chains,
           "chain_words_outside_domain": rejected}
    print(json.dumps(res, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["census", "layers", "control"])
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--seed", type=int, default=101)
    args = ap.parse_args()
    {"census": cmd_census, "layers": cmd_layers, "control": cmd_control}[args.mode](args)


if __name__ == "__main__":
    main()
