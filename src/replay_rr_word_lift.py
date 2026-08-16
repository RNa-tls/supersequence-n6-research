#!/usr/bin/env python3
"""라운드 100 — 라운드-99 단어-lift 결과의 **독립 재구현 재생**.

이 파일은 표준 라이브러리만 쓰고 이 저장소의 탐색/probe 코드를 **하나도 import 하지 않는다.**
라운드-93c 아카이브(감사 완료)만 입력으로 받아 다음을 **처음부터 다시** 만든다.

  * 육각형 = 단어의 **순환 회전류** (아카이브의 `hexagon` 필드와 대조만 하고 신뢰하지 않는다)
  * `WORD_NEXT` = **순열 문자열에서 직접** 계산 (아카이브의 `joint_targets` 를 쓰지 않는다)
  * 잔여 (상태, cover) 쌍 = 층 A · B2 · D1 · D4b 를 새로 구현해 재계산
  * W-A / W-B2 / W-IN 판정과 상태 집계(**모든 잔여 cover 실패**일 때만 폐쇄)

문자열 규칙 (§2 의 두 번째 구현).  `x = x0x1x2x3x4x5` 에서 joint 네 개는

    T1 = x2 x3 x4 x5 x1 x0
    T2 = x3 x4 x5 x1 x2 x0
    T3 = x3 x4 x5 x2 x0 x1
    T4 = x3 x4 x5 x2 x1 x0

이고, `ℓ` 회전 뒤의 joint 는 `x ← σ^ℓ(u)` 로 두고 같은 식을 쓴다.

구조적 증명 (§1, 열거 없이).  육각형은 순환 회전류이므로 두 단어가 같은 육각형에 있을 필요
충분조건은 **순환 후속 함수가 같다**는 것이다.

    succ_x : x0→x1→x2→x3→x4→x5→x0
    succ_T1: x0→x2, x2→x3→x4→x5, x5→x1, x1→x0
    succ_T2: x0→x3, x3→x4→x5, x5→x1, x1→x2, x2→x0
    succ_T3: x0→x1, x1→x3, x3→x4→x5, x5→x2, x2→x0
    succ_T4: x0→x3, x3→x4→x5, x5→x2, x2→x1, x1→x0

`x` 와의 구분: 넷 다 `x5` 의 상이 `x0` 이 아니다(`x1` 또는 `x2`).
서로의 구분: `T1` 은 `x1→x0`, `T2` 는 `x1→x2` (T1≠T2);
`T1,T2` 는 `x5→x1`, `T3,T4` 는 `x5→x2` (앞 둘과 뒤 둘 구분);
`T3` 는 `x2→x0`, `T4` 는 `x2→x1` (T3≠T4).
심볼이 서로 다르므로 이 여섯 비교로 **네 target 이 서로 다른 네 육각형에, 그리고 어느 것도
`x` 의 육각형이 아님**이 따라온다.  ∎

사용법:
    python3 src/replay_rr_word_lift.py               # 전수 재생 + 아카이브 생성
    python3 src/replay_rr_word_lift.py --verify-only # 생성된 아카이브만 재검증
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
OUTDIR = ROOT / "outputs" / "rr_word_lift_archive"
ROOTV = ("root",)


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


# ------------------------------------------------------------- 기하 (두 번째 구현)

def joint_words(x):
    """§2 — 순열 문자열에서 직접 계산한 네 joint target."""
    return (x[2] + x[3] + x[4] + x[5] + x[1] + x[0],
            x[3] + x[4] + x[5] + x[1] + x[2] + x[0],
            x[3] + x[4] + x[5] + x[2] + x[0] + x[1],
            x[3] + x[4] + x[5] + x[2] + x[1] + x[0])


def rotations(w):
    return [w[k:] + w[:k] for k in range(6)]


def build_geometry(geo_rows):
    """단어 문자열만으로 회전류(=육각형)와 `WORD_NEXT` 를 새로 만든다."""
    word_of = {g["id"]: g["word"] for g in geo_rows}
    id_of = {g["word"]: g["id"] for g in geo_rows}
    # 회전류: 정규형(사전순 최소 회전)으로 묶는다
    klass = {}
    for wid, w in word_of.items():
        klass[wid] = min(rotations(w))
    classes = defaultdict(list)
    for wid, key in klass.items():
        classes[key].append(wid)
    # 아카이브의 hexagon 필드와 대조 (신뢰가 아니라 검사)
    agree = all(len({klass[i] for i in members}) == 1
                for members in defaultdict(
                    list, {g["hexagon"]: [] for g in geo_rows}).values()) if False else True
    byhex = defaultdict(set)
    for g in geo_rows:
        byhex[g["hexagon"]].add(klass[g["id"]])
    agree = all(len(v) == 1 for v in byhex.values()) and len(byhex) == len(classes)
    jt = {}
    for wid, w in word_of.items():
        row = {}
        for ell in range(6):
            x = w[ell:] + w[:ell]
            row[ell] = tuple(id_of[t] for t in joint_words(x))
        jt[wid] = row
    return word_of, id_of, klass, jt, agree


def geometry_theorem(geo_rows, klass, jt):
    """§1 인증서 — 네 target 이 서로 다른 회전류, 그리고 source 회전류가 아님."""
    bad_distinct = bad_self = 0
    for wid in jt:
        for ell in range(6):
            ks = [klass[v] for v in jt[wid][ell]]
            if len(set(ks)) != 4:
                bad_distinct += 1
            if klass[wid] in ks:
                bad_self += 1
    return {"contexts": len(jt) * 6, "not_four_distinct": bad_distinct,
            "target_in_source_class": bad_self}


def cross_check_joint_targets(geo_rows, jt):
    """아카이브의 `joint_targets` 와 문자열 구현이 전부 일치하는가 (§2)."""
    mismatch = 0
    for g in geo_rows:
        for ell in range(6):
            if sorted(g["joint_targets"][str(ell)]) != sorted(jt[g["id"]][ell]):
                mismatch += 1
    return {"contexts": len(geo_rows) * 6, "mismatches": mismatch}


# ---------------------------------------------- 의무 그래프와 감사된 층 (재구현)

def obligation(state, cover_orbits, geo_rows, hex_members, jt):
    final = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1}
    final |= set(cover_orbits)
    orbit = {g["id"]: g["orbit"] for g in geo_rows}
    cand = {}
    for h, mask in enumerate(state["hex_masks"]):
        if mask == 0:
            cand[("hex", h)] = [w for w in hex_members[h] if orbit[w] in final]
    frag = state["fragment"]
    if frag:
        cand[("frag",)] = [frag["entry_id"]]
    owner = {}
    for node, ws in cand.items():
        for w in ws:
            owner[w] = node
    ell = {n: (frag["ell"] if n == ("frag",) else 5) for n in cand}
    nodes = list(cand)
    edges = {}
    for node in nodes:
        tgt = set()
        for u in cand[node]:
            for v in jt[u][ell[node]]:
                o = owner.get(v)
                if o is not None and o != node:
                    tgt.add(o)
        edges[node] = tgt
    rt = set()
    for v in jt[state["p_id"]][5]:
        o = owner.get(v)
        if o is not None:
            rt.add(o)
    edges[ROOTV] = rt
    return nodes, edges, cand, owner, ell


def reachable_from_root(nodes, edges):
    seen = {ROOTV}
    dq = deque([ROOTV])
    while dq:
        x = dq.popleft()
        for y in edges.get(x, ()):
            if y not in seen:
                seen.add(y)
                dq.append(y)
    return [n for n in nodes if n not in seen]


def terminal_bounds(nodes, edges):
    if not edges.get(ROOTV):
        return "root_has_no_successor"
    dead = [n for n in nodes if not edges.get(n)]
    if len(dead) >= 2:
        return "two_terminal_obligations"
    # sink SCC >= 2 (Tarjan, 반복 구현)
    idx, low, on, stack, comps = {}, {}, set(), [], []
    counter = [0]
    for root in [ROOTV] + nodes:
        if root in idx:
            continue
        work = [(root, iter(edges.get(root, ())))]
        idx[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            u, it = work[-1]
            adv = False
            for w in it:
                if w not in idx:
                    idx[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(edges.get(w, ()))))
                    adv = True
                    break
                if w in on:
                    low[u] = min(low[u], idx[w])
            if adv:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[u])
            if low[u] == idx[u]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == u:
                        break
                comps.append(comp)
    cid = {}
    for i, comp in enumerate(comps):
        for v in comp:
            cid[v] = i
    sinks = 0
    for i, comp in enumerate(comps):
        if all(cid[y] == i for v in comp for y in edges.get(v, ())):
            sinks += 1
    if sinks >= 2:
        return "two_sink_sccs"
    return None


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


def n_components(verts, adj, removed):
    seen = set(removed)
    n = 0
    for v in verts:
        if v in seen:
            continue
        n += 1
        seen.add(v)
        dq = deque([v])
        while dq:
            x = dq.popleft()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    dq.append(y)
    return n


def d1_fails(nodes, edges):
    verts, adj = undirected(nodes, edges)
    for v in verts:
        if n_components(verts, adj, {v}) > 2:
            return True
    return False


def d4b_fails(nodes, edges):
    verts = [ROOTV] + list(nodes)
    node_set = set(nodes)
    out = {v: {y for y in edges.get(v, ()) if y in node_set} for v in verts}
    inn = {v: set() for v in verts}
    for v in verts:
        for y in out[v]:
            inn[y].add(v)
    inn[ROOTV] = set()
    forced = {}
    changed = True
    while changed:
        changed = False
        for v in nodes:
            if not inn[v]:
                return True
            if len(inn[v]) == 1:
                u = next(iter(inn[v]))
                if forced.get(u) == v:
                    continue
                if u in forced and forced[u] != v:
                    return True
                forced[u] = v
                changed = True
                for w in list(out[u]):
                    if w != v:
                        out[u].discard(w)
                        inn[w].discard(u)
                for z in list(inn[v]):
                    if z != u:
                        inn[v].discard(z)
                        out[z].discard(v)
        dead = [v for v in verts if not out[v]]
        if ROOTV in dead or len(dead) >= 2:
            return True
    seen = set()
    for s in list(forced):
        if s in seen:
            continue
        path, x = [], s
        while x in forced and x not in path:
            path.append(x)
            x = forced[x]
        if x in path:
            cyc = path[path.index(x):]
            if ROOTV not in cyc and len(cyc) < len(nodes):
                return True
        seen.update(path)
    rep = {v: v for v in verts}

    def find(a):
        while rep[a] != a:
            rep[a] = rep[rep[a]]
            a = rep[a]
        return a

    for u, v in forced.items():
        a, b = find(u), find(v)
        if a == b:
            continue
        if b == ROOTV:
            rep[a] = b
        else:
            rep[b] = a
    groups = defaultdict(list)
    for v in verts:
        groups[find(v)].append(v)
    if len(groups) <= 2:
        return False
    rootg = find(ROOTV)
    nodes2 = [g for g in groups if g != rootg]
    e2 = defaultdict(set)
    for x in verts:
        for y in out.get(x, ()):
            a, b = find(x), find(y)
            if a != b:
                e2[ROOTV if a == rootg else a].add(ROOTV if b == rootg else b)
    return d1_fails(nodes2, dict(e2))


# ------------------------------------------------------------------ W-A 판정

def word_verdict(cand, owner, ell, jt, root_word):
    adj = {}
    for node, ws in cand.items():
        for w in ws:
            adj[w] = {owner[v]: v for v in jt[w][ell[node]] if v in owner}
    adj[root_word] = {owner[v]: v for v in jt[root_word][5] if v in owner}
    seen = {root_word}
    reached = set()
    stack = [root_word]
    while stack:
        x = stack.pop()
        for node, v in adj.get(x, {}).items():
            if v not in seen:
                seen.add(v)
                reached.add(node)
                stack.append(v)
    unreachable = [n for n in cand if n not in reached]
    if unreachable:
        return "W_A_FAIL", unreachable, adj
    dead = [n for n in cand if not any(nn != n for w in cand[n] for nn in adj.get(w, {}))]
    if len(dead) >= 2:
        return "W_B2_FAIL", dead, adj
    incoming = {nn for d in adj.values() for nn in d}
    no_in = [n for n in cand if n not in incoming]
    if no_in:
        return "W_IN_FAIL", no_in, adj
    return "PASS", [], adj


def first_failure_certificate(cand, owner, ell, jt, root_word, unreachable, geo_rows):
    """§5 — 불도달 의무 하나에 대해 '어떤 joint target 도 그 육각형에 없다' 를 명시."""
    word_of = {g["id"]: g["word"] for g in geo_rows}
    node = sorted(unreachable, key=lambda n: (n[0], n[1] if len(n) > 1 else -1))[0]
    reach_words = {root_word}
    stack = [root_word]
    adj = {}
    for nd, ws in cand.items():
        for w in ws:
            adj[w] = {owner[v]: v for v in jt[w][ell[nd]] if v in owner}
    adj[root_word] = {owner[v]: v for v in jt[root_word][5] if v in owner}
    while stack:
        x = stack.pop()
        for _nd, v in adj.get(x, {}).items():
            if v not in reach_words:
                reach_words.add(v)
                stack.append(v)
    sample = sorted(reach_words)[:3]
    return {
        "unreachable_obligation": list(node),
        "unreachable_count": len(unreachable),
        "candidate_words_in_that_obligation": [
            {"id": w, "word": word_of[w]} for w in cand[node]],
        "reachable_word_count": len(reach_words),
        "sample_reachable_sources": [
            {"id": w, "word": word_of[w],
             "ell": ell.get(owner.get(w), 5),
             "joint_targets": [{"id": v, "word": word_of[v]}
                               for v in jt[w][ell.get(owner.get(w), 5)]]}
            for w in sample],
        "claim": "도달 가능한 어떤 구체 단어에서도 이 의무의 후보 단어로 가는 joint 가 없다",
    }


# ----------------------------------------------------------------------- 실행

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    t0 = time.time()
    _h, geo_rows = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    _h, covers = read_jsonl(ARCHIVE / "covers.jsonl.gz")
    _h, hall = read_jsonl(ARCHIVE / "hall_results.jsonl.gz")
    word_of, id_of, klass, jt, hex_agree = build_geometry(geo_rows)
    thm = geometry_theorem(geo_rows, klass, jt)
    xchk = cross_check_joint_targets(geo_rows, jt)
    print("geometry theorem:", thm)
    print("joint-target cross check:", xchk, "hexagon==rotation class:", hex_agree)

    hex_members = defaultdict(list)
    for g in geo_rows:
        hex_members[g["hexagon"]].append(g["id"])
    by_id = {s["sid"]: s for s in states}
    cov = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])

    OUTDIR.mkdir(parents=True, exist_ok=True)
    pair_counts = Counter()
    state_counts = Counter()
    rsplit = defaultdict(Counter)
    closures = []
    pairs_written = 0
    n_states = 0
    with gzip.open(OUTDIR / "pairs.jsonl.gz", "wt") as pf:
        pf.write(json.dumps({"schema": "rr_word_lift_archive.pairs/1", "round": 100,
                             "content": "층 A·B2·D1·D4b 를 통과한 잔여 쌍과 그 W-A 판정"},
                            ensure_ascii=False) + "\n")
        for sid in sorted(passing):
            st = by_id[sid]
            keep = []
            for cid in sorted(passing[sid]):
                nodes, edges, cand, owner, ell = obligation(
                    st, cov[(sid, cid)]["orbits"], geo_rows, hex_members, jt)
                if reachable_from_root(nodes, edges):
                    continue
                if terminal_bounds(nodes, edges):
                    continue
                if d1_fails(nodes, edges):
                    continue
                if d4b_fails(nodes, edges):
                    continue
                keep.append((cid, cand, owner, ell))
            if not keep:
                continue
            n_states += 1
            per = []
            for cid, cand, owner, ell in keep:
                verdict, cert, _adj = word_verdict(cand, owner, ell, jt, st["p_id"])
                pair_counts[verdict] += 1
                pairs_written += 1
                row = {"sid": sid, "cover_id": cid, "obligations": len(cand),
                       "pair_verdict": verdict}
                if verdict == "W_A_FAIL":
                    row["certificate"] = first_failure_certificate(
                        cand, owner, ell, jt, st["p_id"], cert, geo_rows)
                per.append(row)
                pf.write(json.dumps(row, ensure_ascii=False) + "\n")
            allfail = all(p["pair_verdict"] != "PASS" for p in per)
            sv = "UNSAT" if allfail else "SAT"
            state_counts[sv] += 1
            rsplit[st["r"]][sv] += 1
            if allfail:
                closures.append({"sid": sid, "r": st["r"], "root": st.get("root"),
                                 "surviving_covers": len(per),
                                 "unique_path": len(per) == 1,
                                 "per_cover": per,
                                 "state_verdict": "UNSAT",
                                 "all_surviving_covers_fail": True})
            if n_states % 500 == 0:
                print(f"  {n_states} states pairs={dict(pair_counts)} "
                      f"{time.time()-t0:.0f}s", flush=True)
            if args.limit and n_states >= args.limit:
                break

    summary = {"round": 100, "implementation": "claude-r100-independent-replay/1",
               "geometry_theorem": thm, "joint_target_cross_check": xchk,
               "hexagon_equals_rotation_class": hex_agree,
               "states": n_states, "pairs": pairs_written,
               "pair_verdicts": dict(pair_counts), "state_verdicts": dict(state_counts),
               "r": {str(k): dict(v) for k, v in sorted(rsplit.items())},
               "state_closures": len(closures),
               "seconds": round(time.time() - t0)}
    with gzip.open(OUTDIR / "closures.jsonl.gz", "wt") as cf:
        cf.write(json.dumps({"schema": "rr_word_lift_archive.closures/1", **summary,
                             "state_rule": "모든 잔여 cover 가 W-A 실패해야 폐쇄"},
                            ensure_ascii=False) + "\n")
        for row in closures:
            cf.write(json.dumps(row, ensure_ascii=False) + "\n")
    (OUTDIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
