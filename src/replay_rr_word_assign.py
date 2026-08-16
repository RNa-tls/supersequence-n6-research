#!/usr/bin/env python3
"""라운드 103 §5–§8 — 라운드-102 W-E 결과의 **두 번째 독립 구현 재생**.

`probe_rr_word_assign`(라운드 102)도 `replay_rr_word_lift`(라운드 100)도 import 하지 않는다.
표준 라이브러리만 쓰고, 기하는 순열 문자열에서 직접 계산하며, 도메인 전파·배정 열거·
A/B2/D4/D1 를 **전부 이 파일 안에서 새로 구현**한다.

검증 대상:

    k 히스토그램 (raw / 전파 후), 배정 총수
    배정 사망 층 A / B2 / D4 / D1
    쌍 PASS / FAIL, 상태 폐쇄 178

사용법:
    python3 src/replay_rr_word_assign.py
"""

from __future__ import annotations

import gzip
import itertools
import json
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
PAIRS = ROOT / "outputs" / "rr_word_lift_archive" / "pairs.jsonl.gz"
OUT = ROOT / "outputs"
RT = ("root",)


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        head = json.loads(fh.readline())
        return head, [json.loads(line) for line in fh]


def geometry():
    _h, geo = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    wid = {g["word"]: g["id"] for g in geo}
    tgt = {}
    for g in geo:
        w = g["word"]
        row = {}
        for e in range(6):
            x = w[e:] + w[:e]
            row[e] = (wid[x[2] + x[3] + x[4] + x[5] + x[1] + x[0]],
                      wid[x[3] + x[4] + x[5] + x[1] + x[2] + x[0]],
                      wid[x[3] + x[4] + x[5] + x[2] + x[0] + x[1]],
                      wid[x[3] + x[4] + x[5] + x[2] + x[1] + x[0]])
        tgt[g["id"]] = row
    hx = defaultdict(list)
    orb = {}
    for g in geo:
        hx[g["hexagon"]].append(g["id"])
        orb[g["id"]] = g["orbit"]
    return tgt, hx, orb


def domains(state, cover, hx, orb):
    fin = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1} | set(cover)
    d = {("hex", h): {w for w in hx[h] if orb[w] in fin}
         for h, m in enumerate(state["hex_masks"]) if m == 0}
    fr = state["fragment"]
    if fr:
        d[("frag",)] = {fr["entry_id"]}
    e = {n: (fr["ell"] if n == ("frag",) else 5) for n in d}
    return d, e, state["p_id"]


def prop(dom, ell, root, tgt):
    d = {k: set(v) for k, v in dom.items()}
    while True:
        own = {w: n for n, ws in d.items() for w in ws}
        keep = {v for v in tgt[root][5] if v in own}
        for n, ws in d.items():
            for u in ws:
                for v in tgt[u][ell[n]]:
                    if v in own and own[v] != n:
                        keep.add(v)
        ch = False
        for n in d:
            drop = d[n] - keep
            if drop:
                d[n] -= drop
                ch = True
            if not d[n]:
                return None
        if not ch:
            return d


def graphs(d, ell, root, tgt):
    fixed = {n: next(iter(v)) for n, v in d.items() if len(v) == 1}
    binv = [(n, sorted(v)) for n, v in d.items() if len(v) == 2]
    for pick in itertools.product((0, 1), repeat=len(binv)):
        A = dict(fixed)
        for (n, ws), c in zip(binv, pick):
            A[n] = ws[c]
        loc = {u: n for n, u in A.items()}
        ed = {n: {loc[v] for v in tgt[u][ell[n]] if v in loc and loc[v] != n}
              for n, u in A.items()}
        ed[RT] = {loc[v] for v in tgt[root][5] if v in loc}
        yield A, list(A), ed


def unreached(nodes, ed):
    seen = {RT}
    q = deque([RT])
    while q:
        x = q.popleft()
        for y in ed.get(x, ()):
            if y not in seen:
                seen.add(y)
                q.append(y)
    return [n for n in nodes if n not in seen]


def bad_terminals(nodes, ed):
    if not ed.get(RT):
        return True
    if sum(1 for n in nodes if not ed.get(n)) >= 2:
        return True
    idx, low, on, stk, comps, cnt = {}, {}, set(), [], [], [0]
    for r0 in [RT] + nodes:
        if r0 in idx:
            continue
        work = [(r0, iter(ed.get(r0, ())))]
        idx[r0] = low[r0] = cnt[0]
        cnt[0] += 1
        stk.append(r0)
        on.add(r0)
        while work:
            u, it = work[-1]
            adv = False
            for w in it:
                if w not in idx:
                    idx[w] = low[w] = cnt[0]
                    cnt[0] += 1
                    stk.append(w)
                    on.add(w)
                    work.append((w, iter(ed.get(w, ()))))
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
                    w = stk.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == u:
                        break
                comps.append(comp)
    cid = {v: i for i, c in enumerate(comps) for v in c}
    sinks = sum(1 for i, c in enumerate(comps)
                if all(cid[y] == i for v in c for y in ed.get(v, ())))
    return sinks >= 2


def comps_without(verts, adj, drop):
    seen = {drop}
    n = 0
    for v in verts:
        if v in seen:
            continue
        n += 1
        seen.add(v)
        q = deque([v])
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    q.append(y)
    return n


def separator_fails(nodes, ed):
    verts = [RT] + nodes
    ok = set(verts)
    adj = {v: set() for v in verts}
    for x in verts:
        for y in ed.get(x, ()):
            if y in ok:
                adj[x].add(y)
                adj[y].add(x)
    return any(comps_without(verts, adj, v) > 2 for v in verts)


def forced_fails(nodes, ed):
    verts = [RT] + nodes
    ns = set(nodes)
    out = {v: {y for y in ed.get(v, ()) if y in ns} for v in verts}
    inn = {v: set() for v in verts}
    for v in verts:
        for y in out[v]:
            inn[y].add(v)
    inn[RT] = set()
    forced = {}
    ch = True
    while ch:
        ch = False
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
                ch = True
                for w in list(out[u]):
                    if w != v:
                        out[u].discard(w)
                        inn[w].discard(u)
                for z in list(inn[v]):
                    if z != u:
                        inn[v].discard(z)
                        out[z].discard(v)
        dead = [v for v in verts if not out[v]]
        if RT in dead or len(dead) >= 2:
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
            if RT not in cyc and len(cyc) < len(nodes):
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
        if b == RT:
            rep[a] = b
        else:
            rep[b] = a
    grp = defaultdict(list)
    for v in verts:
        grp[find(v)].append(v)
    if len(grp) <= 2:
        return False
    rg = find(RT)
    n2 = [g for g in grp if g != rg]
    e2 = defaultdict(set)
    for x in verts:
        for y in out.get(x, ()):
            a, b = find(x), find(y)
            if a != b:
                e2[RT if a == rg else a].add(RT if b == rg else b)
    return separator_fails(n2, dict(e2))


def main() -> None:
    t0 = time.time()
    tgt, hx, orb = geometry()
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    _h, covers = read_jsonl(ARCHIVE / "covers.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    _h, allp = read_jsonl(PAIRS)
    rows = [p for p in allp if p["pair_verdict"] == "PASS"]
    kraw, kprop, layer, pair = Counter(), Counter(), Counter(), Counter()
    total = 0
    per = defaultdict(list)
    for i, r in enumerate(rows):
        st = S[r["sid"]]
        dom, ell, root = domains(st, CV[(r["sid"], r["cover_id"])]["orbits"], hx, orb)
        kraw[sum(1 for v in dom.values() if len(v) == 2)] += 1
        d = prop(dom, ell, root, tgt)
        if d is None:
            kprop[-1] += 1
            pair["FAIL"] += 1
            layer["empty_domain"] += 1
            per[r["sid"]].append("FAIL")
            continue
        kprop[sum(1 for v in d.values() if len(v) == 2)] += 1
        alive = 0
        for _A, nodes, ed in graphs(d, ell, root, tgt):
            total += 1
            if unreached(nodes, ed):
                layer["A"] += 1
            elif bad_terminals(nodes, ed):
                layer["B2"] += 1
            elif forced_fails(nodes, ed):
                layer["D4"] += 1
            elif separator_fails(nodes, ed):
                layer["D1"] += 1
            else:
                alive += 1
        v = "PASS" if alive else "FAIL"
        pair[v] += 1
        per[r["sid"]].append(v)
        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{len(rows)} {dict(pair)} {time.time()-t0:.0f}s", flush=True)
    closed = sorted(s for s, vs in per.items() if all(v == "FAIL" for v in vs))
    res = {"round": 103, "implementation": "claude-r103-independent-we-replay/1",
           "pairs": len(rows), "assignments": total,
           "k_raw": dict(sorted(kraw.items())), "k_propagated": dict(sorted(kprop.items())),
           "assignments_killed_by_layer": dict(layer),
           "pair_verdicts": dict(pair),
           "state_closures": len(closed), "seconds": round(time.time() - t0)}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "rr_word_assign_replay.json").write_text(
        json.dumps({**res, "closed_sids": closed}, ensure_ascii=False, indent=1),
        encoding="utf-8")


if __name__ == "__main__":
    main()
