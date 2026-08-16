#!/usr/bin/env python3
"""라운드 99 — 단어-lift 결과의 **독립 재생 검증기**.

이 저장소의 탐색·probe 코드를 **하나도 import 하지 않는다.** 표준 라이브러리만으로
라운드-93c 아카이브와 라운드-99 원장만 읽어 다음을 처음부터 다시 계산한다.

 1. 기하 정리: 모든 `(단어, ℓ)` 에서 네 joint target 이 서로 다른 육각형에 있는가.
    (이것이 `WORD_NEXT` 를 부분 함수로 만든다.)
 2. 원장의 모든 폐쇄 행에 대해 cand/단어 인접을 재구성하고 W-A/W-B2/W-IN 을 다시 판정.
 3. 불도달 인증서 직접 확인 — 나열된 의무가 정말 현재 단어에서 닿지 않는가.
 4. 보존된 SAT 증인(단어 사슬)의 **모든 단계를 기하에 대조**.

주의: 이것은 같은 저자(Claude)의 두 번째 구현이므로 **독립 감사가 아니다.** 오류 탐지용이다.

사용법:
    python3 src/verify_rr_word_lift.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
OUT = ROOT / "outputs"


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


def load():
    _h, geo = read_jsonl(ARCHIVE / "geometry.jsonl.gz")
    by_id = {g["id"]: g for g in geo}
    hex_words = {}
    for g in geo:
        hex_words.setdefault(g["hexagon"], []).append(g["id"])
    _h, states = read_jsonl(ARCHIVE / "states.jsonl.gz")
    _h, covers = read_jsonl(ARCHIVE / "covers.jsonl.gz")
    return by_id, hex_words, {s["sid"]: s for s in states}, \
        {(c["sid"], c["cover_id"]): c for c in covers}


def check_geometry(geo):
    bad = 0
    for u in geo:
        for ell in range(6):
            tg = geo[u]["joint_targets"][str(ell)]
            if len({geo[v]["hexagon"] for v in tg}) != len(tg):
                bad += 1
            if geo[u]["hexagon"] in {geo[v]["hexagon"] for v in tg}:
                bad += 1
    return {"contexts": len(geo) * 6, "violations": bad}


def build(state, cover_orbits, geo, hex_words):
    final = {q for q in range(144) if int(state["open_orbits"], 16) >> q & 1}
    final |= set(cover_orbits)
    cand = {}
    for h, mask in enumerate(state["hex_masks"]):
        if mask == 0:
            cand[("hex", h)] = [w for w in hex_words[h] if geo[w]["orbit"] in final]
    frag = state["fragment"]
    if frag:
        cand[("frag",)] = [frag["entry_id"]]
    owner = {}
    for node, words in cand.items():
        for w in words:
            owner[w] = node
    ell = {n: (frag["ell"] if n == ("frag",) else 5) for n in cand}
    return cand, owner, ell, state["p_id"]


def nexts(geo, owner, u, ell):
    got = {}
    for v in geo[u]["joint_targets"][str(ell)]:
        node = owner.get(v)
        if node is None:
            continue
        if node in got:
            raise AssertionError("WORD_NEXT is not a function")
        got[node] = v
    return got


def verdict_for(geo, cand, owner, ell, root_word):
    adj = {}
    for node, words in cand.items():
        for w in words:
            adj[w] = nexts(geo, owner, w, ell[node])
    adj[root_word] = nexts(geo, owner, root_word, 5)
    reached, seen, stack = set(), {root_word}, [root_word]
    while stack:
        x = stack.pop()
        for node, v in adj.get(x, {}).items():
            if v not in seen:
                seen.add(v)
                reached.add(node)
                stack.append(v)
    unreachable = [n for n in cand if n not in reached]
    dead = [n for n in cand
            if not any(nn != n for w in cand[n] for nn in adj.get(w, {}))]
    incoming = {nn for d in adj.values() for nn in d}
    no_in = [n for n in cand if n not in incoming]
    if unreachable:
        return "W_A_FAIL", unreachable
    if len(dead) >= 2:
        return "W_B2_FAIL", dead
    if no_in:
        return "W_IN_FAIL", no_in
    return "PASS", []


def verify_chain(geo, cand, owner, ell, root_word, chain):
    """SAT 증인: 모든 단계가 합법 joint 이고 의무마다 단어 하나씩인가."""
    u, cur_ell = root_word, 5
    used_nodes, used_words = set(), set()
    for step in chain:
        node = tuple(step["node"])
        v = step["word_id"]
        if v not in geo[u]["joint_targets"][str(cur_ell)]:
            return False, f"step {node}: {v} is not a joint target of {u} at ell={cur_ell}"
        if owner.get(v) != node:
            return False, f"step {node}: word {v} does not belong to that obligation"
        if node in used_nodes or v in used_words:
            return False, f"step {node}: repeated obligation or word"
        used_nodes.add(node)
        used_words.add(v)
        u, cur_ell = v, ell[node]
    if used_nodes != set(cand):
        return False, f"covered {len(used_nodes)} of {len(cand)} obligations"
    return True, "ok"


def main() -> None:
    geo, hex_words, states, covers = load()
    report = {"geometry": check_geometry(geo)}
    print("geometry:", report["geometry"])

    ledger = OUT / "rr_word_lift_static_ledger.jsonl.gz"
    mismatches, checked, cert_bad = 0, 0, 0
    if ledger.exists():
        with gzip.open(ledger, "rt") as fh:
            fh.readline()
            for line in fh:
                row = json.loads(line)
                st = states[row["sid"]]
                for per in row["per_cover"]:
                    cand, owner, ell, p = build(
                        st, covers[(row["sid"], per["cover_id"])]["orbits"], geo, hex_words)
                    got, cert = verdict_for(geo, cand, owner, ell, p)
                    checked += 1
                    if got != per["pair_verdict"]:
                        mismatches += 1
                    if per["certificate"] and per["pair_verdict"] == "W_A_FAIL":
                        listed = {tuple(x) for x in per["certificate"]["unreachable"]}
                        if not listed <= set(cert):
                            cert_bad += 1
    report["static_ledger"] = {"pairs_rechecked": checked, "verdict_mismatches": mismatches,
                               "bad_certificates": cert_bad}
    print("static ledger:", report["static_ledger"])

    wit = OUT / "rr_word_lift_pilot.json"
    ok_chains, bad_chains = 0, 0
    if wit.exists():
        for row in json.loads(wit.read_text())["rows"]:
            if not row.get("witness"):
                continue
            st = states[row["sid"]]
            cid = row.get("cover_id")
            if cid is None:
                continue
            cand, owner, ell, p = build(st, covers[(row["sid"], cid)]["orbits"], geo, hex_words)
            good, why = verify_chain(geo, cand, owner, ell, p, row["witness"])
            if good:
                ok_chains += 1
            else:
                bad_chains += 1
                print("BAD WITNESS", row["sid"][:8], why)
    report["sat_witness_chains"] = {"verified": ok_chains, "rejected": bad_chains}
    print("sat witness chains:", report["sat_witness_chains"])

    (OUT / "rr_word_lift_verification.json").write_text(
        json.dumps({"round": 99, "note": "같은 저자의 두 번째 구현 — 독립 감사가 아니다",
                    **report}, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = report["geometry"]["violations"] + mismatches + cert_bad + bad_chains
    print("TOTAL PROBLEMS:", bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
