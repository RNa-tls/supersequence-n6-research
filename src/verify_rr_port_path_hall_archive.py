#!/usr/bin/env python3
"""라운드 93c — PORT-PATH HALL 감사 아카이브 **독립 검증기** (표준 라이브러리만).

이 파일은 이 저장소의 탐색·frontier·probe 코드를 **하나도 import 하지 않는다.**
`outputs/rr_port_path_hall_archive/` 의 파일만 읽어서

  1. 상태 행을 검증하고 (마스크 크기, `P = Σ popcount(orbit_masks)`, `D = 5O − P`,
     현재 육각형에 방문 칸이 정확히 1개, fragment 점유와 수리 `ℓ = 5 − c_f` 등),
  2. (상태, cover) 마다 Hall 그래프를 **처음부터 다시** 만들고,
  3. 저장된 SAT 매칭의 모든 간선을 실제 기하에 대조해 검증하고,
  4. 모든 cover 에 대해 최대 매칭을 다시 계산하고,
  5. cover 하나라도 통과하면 상태 SAT, 전부 실패해야 UNSAT 으로 분류하고,
  6. 저장된 Hall 결손 인증서 `|N(X)| < |X|` 를 직접 확인하고,
  7. 총계와 결손 히스토그램을 재현한다.

Hall 그래프 재구성 규칙 (아카이브만으로 결정된다).

    최종 궤도 = open_orbits 의 궤도 ∪ cover 의 궤도
    빈 육각형 = hex_masks[h] == 0 인 h
    육각형 h 의 진입 후보 = 육각형이 h 이고 궤도가 최종 궤도인 단어
    왼쪽  = 빈 육각형 전부 (+ fragment 가 있으면 fragment)
    슬롯  = 현재 pass + 왼쪽
    후속  = 현재 pass 는 p 에서 ℓ=5, fragment 는 진입 단어에서 ℓ=5−c_f,
            빈 육각형은 진입 후보들에서 ℓ=5 (joint_targets 표를 그대로 사용)
    간선  = 슬롯의 후속 집합이 왼쪽 노드의 진입 후보와 만나면 연결

사용법: `python3 src/verify_rr_port_path_hall_archive.py [--archive DIR] [--limit N]`
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parent.parent / "outputs" / "rr_port_path_hall_archive"


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        rows = [json.loads(line) for line in fh]
    return header, rows


def popcount(x):
    return bin(x).count("1")


def build_geometry(rows):
    by_id = {r["id"]: r for r in rows}
    hex_words = defaultdict(list)
    for r in rows:
        hex_words[r["hexagon"]].append(r["id"])
    return by_id, hex_words


def check_state(s, geo, hex_words):
    """상태 행 자체의 정합성 — 아카이브 안에서만 검사한다."""
    problems = []
    if len(s["hex_masks"]) != 120 or len(s["orbit_masks"]) != 144:
        problems.append("mask_shape")
    P = sum(popcount(m) for m in s["orbit_masks"])
    O = sum(1 for m in s["orbit_masks"] if m)
    if P != s["P"] or O != s["O"]:
        problems.append("P_or_O_mismatch")
    if s["D"] != 5 * O - P:
        problems.append("D_identity")
    p = geo[s["p_id"]]
    if p["hexagon"] != s["current_hex"]:
        problems.append("current_hex")
    if popcount(s["hex_masks"][s["current_hex"]]) != 1:
        problems.append("current_hex_not_singleton")
    if not (s["hex_masks"][p["hexagon"]] >> p["hex_index"] & 1):
        problems.append("endpoint_not_visited")
    if not (s["orbit_masks"][p["orbit"]] >> p["phase"] & 1):
        problems.append("endpoint_not_registered")
    empty = sum(1 for m in s["hex_masks"] if m == 0)
    if empty != s["empty_hexes"]:
        problems.append("empty_count")
    frag = s["fragment"]
    if frag:
        h = frag["hex"]
        if popcount(s["hex_masks"][h]) != frag["c_f"]:
            problems.append("fragment_occupancy")
        if frag["ell"] != 5 - frag["c_f"]:
            problems.append("fragment_ell")
        e = geo[frag["entry_id"]]
        if e["hexagon"] != h or (s["hex_masks"][h] >> e["hex_index"] & 1):
            problems.append("fragment_entry_visited_or_wrong_hex")
        if [e["orbit"], e["phase"]] != frag["port"]:
            problems.append("fragment_port")
    # 121 - P == 빈 육각형 + fragment 수
    if 121 - P != empty + (1 if frag else 0):
        problems.append("pass_count_identity")
    return problems


def hall_graph(s, cover, geo, hex_words):
    final = {q for q in range(144) if int(s["open_orbits"], 16) >> q & 1} | set(cover)
    empty = [h for h, m in enumerate(s["hex_masks"]) if m == 0]
    cand = {h: [w for w in hex_words[h] if geo[w]["orbit"] in final] for h in empty}
    frag = s["fragment"]
    left = [("hex", h) for h in empty] + ([("frag",)] if frag else [])
    slots = [("cur",)] + left

    def succ(slot):
        if slot == ("cur",):
            return set(geo[s["p_id"]]["joint_targets"]["5"])
        if slot == ("frag",):
            return set(geo[frag["entry_id"]]["joint_targets"][str(frag["ell"])])
        out = set()
        for u in cand[slot[1]]:
            out.update(geo[u]["joint_targets"]["5"])
        return out

    succ_map = {sl: succ(sl) for sl in slots}
    adjacency = {}
    for node in left:
        targets = set(cand[node[1]]) if node[0] == "hex" else {frag["entry_id"]}
        adjacency[node] = [sl for sl in slots if sl != node and (succ_map[sl] & targets)]
    return left, slots, cand, adjacency


def max_matching(left, adjacency):
    matched, pair = {}, {}
    for x in left:
        seen = set()

        def augment(node):
            for y in adjacency[node]:
                if y in seen:
                    continue
                seen.add(y)
                if y not in matched or augment(matched[y]):
                    matched[y] = node
                    pair[node] = y
                    return True
            return False

        augment(x)
    return pair


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", default=str(ARCHIVE))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--example", help="sid 접두사 — 그 상태의 Hall 위반을 단어 수준으로 펼쳐 보인다")
    args = ap.parse_args()
    root = Path(args.archive)
    _, geo_rows = read_jsonl(root / "geometry.jsonl.gz")
    geo, hex_words = build_geometry(geo_rows)
    _, states = read_jsonl(root / "states.jsonl.gz")
    _, covers = read_jsonl(root / "covers.jsonl.gz")
    _, stored_hall = read_jsonl(root / "hall_results.jsonl.gz")
    _, sat_rows = read_jsonl(root / "sat_witnesses.jsonl.gz")
    _, unsat_rows = read_jsonl(root / "unsat_certificates.jsonl.gz")
    if args.limit:
        states = states[:args.limit]
        keep = {s["sid"] for s in states}
        covers = [c for c in covers if c["sid"] in keep]
    print(f"geometry {len(geo_rows)} words | states {len(states)} | covers {len(covers)}")

    if args.example:
        target = [s for s in states if s["sid"].startswith(args.example)]
        if not target:
            print("no such sid")
            return
        s = target[0]
        pred = defaultdict(set)
        for g in geo_rows:
            for ell, targets in g["joint_targets"].items():
                for t in targets:
                    pred[t].add((g["id"], int(ell)))
        mine = [c for c in covers if c["sid"] == s["sid"]]
        print(f"\n=== {s['sid'][:8]} covers={len(mine)} p={s['p']} ===")
        for c in mine:
            left, slots, cand, adjacency = hall_graph(s, c["orbits"], geo, hex_words)
            pair = max_matching(left, adjacency)
            unmatched = [x for x in left if x not in pair]
            print(f"cover {c['cover_id']} deficit={len(left)-len(pair)} unmatched={unmatched}")
            for node in unmatched:
                if node[0] != "hex":
                    continue
                h = node[1]
                print(f"  hexagon {h}: final-orbit candidate words {cand[h]}")
                for u in cand[h]:
                    print(f"   entry word {geo[u]['word']} (orbit {geo[u]['orbit']}, "
                          f"phase {geo[u]['phase']}) — all predecessors:")
                    for (y, ell) in sorted(pred[u]):
                        g = geo[y]
                        visited = bool(s["hex_masks"][g["hexagon"]] >> g["hex_index"] & 1)
                        final = (int(s["open_orbits"], 16) >> g["orbit"] & 1) or g["orbit"] in c["orbits"]
                        if ell != 5 and not (s["fragment"] and y == s["fragment"]["entry_id"]
                                             and ell == s["fragment"]["ell"]):
                            continue
                        print(f"     {g['word']} orbit {g['orbit']} hex {g['hexagon']} ell={ell} "
                              f"visited={visited} in_final_orbits={bool(final)}")
            break
        return

    state_problems = Counter()
    for s in states:
        for p in check_state(s, geo, hex_words):
            state_problems[p] += 1
    print(f"state row problems: {dict(state_problems) or 'none'}")

    by_sid = defaultdict(list)
    for c in covers:
        by_sid[c["sid"]].append(c)
    stored_by = {(h["sid"], h["cover_id"]): h for h in stored_hall}
    sat_by = {w["sid"]: w for w in sat_rows}
    unsat_by = {u["sid"]: u for u in unsat_rows}

    agg, deficit_hist, passing_hist = Counter(), Counter(), Counter()
    mismatches, witness_bad, cert_bad = Counter(), 0, 0
    for s in states:
        sid = s["sid"]
        verdict = "UNSAT"
        passing_hist[len(by_sid[sid])] += 1
        results = []
        for c in sorted(by_sid[sid], key=lambda x: x["cover_id"]):
            left, slots, cand, adjacency = hall_graph(s, c["orbits"], geo, hex_words)
            pair = max_matching(left, adjacency)
            deficit = len(left) - len(pair)
            results.append((c["cover_id"], deficit, left, adjacency, pair))
            stored = stored_by.get((sid, c["cover_id"]))
            if stored and (stored["deficit"] != deficit or stored["left"] != len(left)):
                mismatches["hall_result"] += 1
            if deficit == 0:
                verdict = "SAT"
            else:
                deficit_hist[deficit] += 1
        agg[verdict] += 1
        if verdict == "SAT":
            w = sat_by.get(sid)
            if not w:
                witness_bad += 1
            else:
                cover = next(c for c in by_sid[sid] if c["cover_id"] == w["cover_id"])
                left, slots, cand, adjacency = hall_graph(s, cover["orbits"], geo, hex_words)
                used, ok = set(), True
                for l, sl in w["matching"]:
                    ln, sn = tuple(l), tuple(sl)
                    if sn in used or sn not in adjacency.get(ln, []):
                        ok = False
                        break
                    used.add(sn)
                if not ok or len(w["matching"]) != len(left):
                    witness_bad += 1
        else:
            u = unsat_by.get(sid)
            if not u or u["covers"] != len(by_sid[sid]):
                cert_bad += 1
                continue
            for cert in u["certificates"]:
                hv = cert.get("hall_violator")
                if not hv:
                    cert_bad += 1
                    continue
                cover = next(c for c in by_sid[sid] if c["cover_id"] == cert["cover_id"])
                left, slots, cand, adjacency = hall_graph(s, cover["orbits"], geo, hex_words)
                X = [tuple(x) for x in hv["X"]]
                N = set()
                for x in X:
                    N.update(map(tuple, adjacency[x]))
                if len(N) >= len(X):
                    cert_bad += 1
    print(f"\nreplayed aggregate: {dict(agg)}")
    print(f"all failing-cover deficits: {dict(sorted(deficit_hist.items()))}")
    print(f"passing-cover histogram: {dict(sorted(passing_hist.items())[:8])} ...")
    print(f"stored-vs-recomputed hall mismatches: {dict(mismatches) or 'none'}")
    print(f"bad SAT witnesses: {witness_bad} | bad UNSAT certificates: {cert_bad}")

    summary = json.load(open(root / "summary.json"))
    print("\nexported summary:", summary["aggregate"], summary["all_failing_cover_deficits"])
    same = (dict(agg) == summary["aggregate"] and
            {str(k): v for k, v in sorted(deficit_hist.items())} == summary["all_failing_cover_deficits"])
    print("독립 재현 일치:", same)


if __name__ == "__main__":
    main()
