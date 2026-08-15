#!/usr/bin/env python3
"""라운드 93c — PORT-PATH HALL 감사 아카이브 내보내기.

Codex 는 라운드 93 의 Hall 필요조건과 등록 의미론은 건전하다고 확인했으나, 보존된 원장에
**상태·cover 별 인증서가 부족해** 1,366 / 5,030 을 독립 재현하지 못했다.  이 모듈은 그
부족분을 채운다 — frontier 재구성 없이, 그리고 이 저장소의 탐색 코드를 import 하지 않고도
검증기가 전부 재구성할 수 있도록.

내보내는 것 (`outputs/rr_port_path_hall_archive/`).

geometry.jsonl.gz    720 단어의 고정 번호 — 순열 문자열, 궤도, 위상, 육각형, 육각형 내 위치,
                     그리고 `ℓ = 0..5` 각각에 대한 4개 joint target.  Hall 그래프의 기하는
                     전부 이 표에서 재구성된다.
states.jsonl.gz      6,396 상태의 리터럴 자료 — `p`, `hex_masks`, `orbit_masks`, `F/S/H`,
                     `O/P/D`, `c/r/K/b`, `U`, 열린 궤도, 현재 육각형, fragment 육각형과 점유,
                     수리 진입 단어·port·`ℓ`.  전임자가 이미 방문됐는지 판정할 수 있다.
covers.jsonl.gz      상태마다 라운드-92 결합 조건을 통과하는 **모든 서로 다른 cover 집합**
                     (도출 중복 제거).  UNSAT 상태에서는 절대 첫 성공에서 끊지 않는다.
hall_results.jsonl.gz (상태, cover) 쌍마다 Hall 판정 — 매칭 크기, 결손, 그리고 UNSAT 이면
                     König 로 뽑은 **결손 부분집합 X** (`|N(X)| < |X|`).
sat_witnesses.jsonl.gz SAT 상태마다 통과 cover 와 **완전한 매칭**(왼쪽 의무 → 전임 슬롯).
unsat_certificates.jsonl.gz UNSAT 상태마다 **모든** cover 에 대한 결손 인증서.
SCHEMA.md            스키마와 재구성 규칙.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.setrecursionlimit(20000)
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "rr_port_path_hall_archive"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PP = _load("probe_rr_port_path", "src/probe_rr_port_path.py")
SL = PP.SL
ssp = PP.ssp
core, OP, HP, NORB = PP.core, PP.OP, PP.HP, PP.NORB
WORDS = PP.WORDS
WORD_ID = {w: i for i, w in enumerate(WORDS)}


def write(path, rows, header):
    with gzip.open(path, "wt") as fh:
        fh.write(json.dumps(header, ensure_ascii=False) + "\n")
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def geometry_rows():
    for w in WORDS:
        q, f = OP[w]
        h, b = HP[w]
        yield dict(id=WORD_ID[w], word="".join(str(x) for x in w), orbit=q, phase=f,
                   hexagon=h, hex_index=b,
                   joint_targets={str(ell): [WORD_ID[t] for t in PP.joint_targets(w, ell)]
                                  for ell in range(6)})


def hall_instance(state, open_bits, S, frag):
    """Hall 그래프를 명시적으로 만든다 — 검증기가 하는 것과 같은 규칙."""
    final = {q for q in range(NORB) if open_bits >> q & 1} | set(S)
    counts = [bin(m).count("1") for m in state.hex_masks]
    empty = [h for h, c in enumerate(counts) if c == 0]
    cand = {h: [w for w in PP.HEX_WORDS[h] if OP[w][0] in final] for h in empty}
    left = [("hex", h) for h in empty] + ([("frag",)] if frag else [])
    slots = [("cur",)] + left

    def succ(slot):
        if slot == ("cur",):
            return set(PP.NEXT5[state.p])
        if slot == ("frag",):
            return set(PP.joint_targets(frag["entry_word"], frag["ell"]))
        out = set()
        for u in cand[slot[1]]:
            out.update(PP.NEXT5[u])
        return out

    succ_map = {s: succ(s) for s in slots}
    adjacency = {}
    for node in left:
        targets = set(cand[node[1]]) if node[0] == "hex" else {frag["entry_word"]}
        adjacency[node] = [s for s in slots if s != node and (succ_map[s] & targets)]
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
    return pair, matched


def hall_violator(left, adjacency, pair):
    """König: 매칭되지 않은 왼쪽 정점에서 교대 경로로 닿는 왼쪽 집합 X (|N(X)| < |X|)."""
    unmatched = [x for x in left if x not in pair]
    if not unmatched:
        return None
    matched_by = {y: x for x, y in pair.items()}
    X, seen_right, stack = set(unmatched), set(), list(unmatched)
    while stack:
        x = stack.pop()
        for y in adjacency[x]:
            if y in seen_right:
                continue
            seen_right.add(y)
            nxt = matched_by.get(y)
            if nxt is not None and nxt not in X:
                X.add(nxt)
                stack.append(nxt)
    return sorted(X), sorted(seen_right)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exclude", required=True, help="이미 닫힌 sid 목록 JSON")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    closed = set(json.load(open(args.exclude)))
    rows = [r for r in ssp.po.load_states() if r["sid"] not in closed]
    if args.limit:
        rows = rows[:args.limit]
    print(f"input states: {len(rows)}", flush=True)

    write(OUT / "geometry.jsonl.gz", geometry_rows(),
          dict(schema="rr_port_path_hall/geometry/1", words=720,
               note="id 는 이 파일의 고정 번호. joint_targets[ell] 은 sigma^ell 후 4개 joint 의 target id."))

    state_rows, cover_rows, hall_rows, sat_rows, unsat_rows = [], [], [], [], []
    agg, passing_hist = Counter(), Counter()
    all_fail_def, unsat_cover_def, unsat_min_def, hall_pass_hist = (
        Counter(), Counter(), Counter(), Counter())
    t0 = time.time()
    for i, r in enumerate(rows):
        st = r["state"]
        sl = SL.short_local(st, r["open_orbits"])
        frag = None
        if sl["budget"]:
            port = tuple(sl["source_ports"][0])
            entry = next(w for w in WORDS if OP[w] == port)
            frag = dict(hex=sl["hex"], c_f=sl["c_f"], ell=sl["ell"], entry_word=entry,
                        entry_id=WORD_ID[entry], port=list(port))
        counts = [bin(m).count("1") for m in st.hex_masks]
        state_rows.append(dict(
            sid=r["sid"], root=r["root"], idx=r.get("idx"),
            p="".join(str(x) for x in st.p), p_id=WORD_ID[st.p],
            hex_masks=list(st.hex_masks), orbit_masks=list(st.orbit_masks),
            F=st.F, S=st.S, H=st.H, O=st.O, P=st.P, D=st.D,
            c=r["c"], r=1 - sl["budget"], K=r["K"], b=r["b"],
            U=hex(r["U"]), open_orbits=hex(r["open_orbits"]),
            current_hex=HP[st.p][0], empty_hexes=sum(1 for c in counts if c == 0),
            fragment=None if not frag else dict(hex=frag["hex"], c_f=frag["c_f"],
                                                ell=frag["ell"], entry_id=frag["entry_id"],
                                                port=frag["port"]),
            short_local_fresh_targets=sl["fresh_target_orbits"]))

        # --- 라운드-92 결합 조건을 통과하는 모든 서로 다른 cover 집합 (첫 성공에서 끊지 않음)
        passing = []
        seen = set()

        def on_cover(S, _r=r, _sl=sl):
            key = tuple(sorted(S))
            if key in seen:
                return False
            seen.add(key)
            ok, T = SL.feasible(list(key), _r["open_orbits"], _sl, "local")
            if ok:
                passing.append((key, tuple(T or ())))
            return False

        scan = ssp.scan_covers(r, on_cover)
        assert scan["complete"], r["sid"]
        passing_hist[len(passing)] += 1

        state_verdict, sat_witness = "UNSAT", None
        for cid, (S, T) in enumerate(passing):
            cover_rows.append(dict(sid=r["sid"], cover_id=cid, orbits=list(S),
                                   short_used=list(T), round92_model="local"))
            left, slots, cand, adjacency = hall_instance(st, r["open_orbits"], set(S), frag)
            pair, _ = max_matching(left, adjacency)
            deficit = len(left) - len(pair)
            row = dict(sid=r["sid"], cover_id=cid, left=len(left), slots=len(slots),
                       matched=len(pair), deficit=deficit,
                       verdict="SAT" if deficit == 0 else "UNSAT")
            if deficit:
                X, NX = hall_violator(left, adjacency, pair)
                row["hall_violator"] = dict(
                    X=[list(x) for x in X], size=len(X),
                    neighbourhood=[list(y) for y in NX], neighbourhood_size=len(NX))
            hall_rows.append(row)
            if deficit:
                all_fail_def[deficit] += 1
            if deficit == 0 and state_verdict == "UNSAT":
                state_verdict = "SAT"
                sat_witness = dict(
                    sid=r["sid"], cover_id=cid, orbits=list(S),
                    matching=[[list(l), list(pair[l])] for l in left])
        if state_verdict == "SAT":
            sat_rows.append(sat_witness)
        else:
            certs = [h for h in hall_rows if h["sid"] == r["sid"]]
            unsat_rows.append(dict(sid=r["sid"], covers=len(passing),
                                   certificates=[dict(cover_id=h["cover_id"],
                                                      deficit=h["deficit"],
                                                      hall_violator=h.get("hall_violator"))
                                                 for h in certs]))
            for h in certs:
                unsat_cover_def[h["deficit"]] += 1
            unsat_min_def[min(h["deficit"] for h in certs)] += 1
        agg[state_verdict] += 1
        hall_pass_hist[sum(1 for h in hall_rows if h["sid"] == r["sid"] and h["deficit"] == 0)] += 1
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(rows)} {dict(agg)} covers={len(cover_rows)} "
                  f"{time.time()-t0:.0f}s", flush=True)

    write(OUT / "states.jsonl.gz", state_rows,
          dict(schema="rr_port_path_hall/states/1", states=len(state_rows),
               note="hex_masks[h] 의 비트 b 는 geometry 의 (hexagon=h, hex_index=b) 단어가 방문됨을 뜻한다. "
                    "orbit_masks[q] 의 비트 f 는 (orbit=q, phase=f) port 가 등록됨을 뜻한다."))
    write(OUT / "covers.jsonl.gz", cover_rows,
          dict(schema="rr_port_path_hall/covers/1", covers=len(cover_rows),
               note="상태별 라운드-92 통과 cover 집합 전부. 도출 중복은 제거했고 첫 성공에서 끊지 않았다."))
    write(OUT / "hall_results.jsonl.gz", hall_rows,
          dict(schema="rr_port_path_hall/hall_results/1", pairs=len(hall_rows)))
    write(OUT / "sat_witnesses.jsonl.gz", sat_rows,
          dict(schema="rr_port_path_hall/sat_witnesses/1", states=len(sat_rows)))
    write(OUT / "unsat_certificates.jsonl.gz", unsat_rows,
          dict(schema="rr_port_path_hall/unsat_certificates/1", states=len(unsat_rows)))
    summary = dict(states=len(rows), aggregate=dict(agg),
                   cover_rows=len(cover_rows),
                   round92_passing_cover_histogram={str(k): v for k, v in sorted(passing_hist.items())},
                   hall_passing_cover_histogram={str(k): v for k, v in sorted(hall_pass_hist.items())},
                   all_failing_cover_deficits={str(k): v for k, v in sorted(all_fail_def.items())},
                   unsat_state_cover_deficits={str(k): v for k, v in sorted(unsat_cover_def.items())},
                   unsat_state_min_deficit={str(k): v for k, v in sorted(unsat_min_def.items())},
                   deficit_note="라운드 93 이 보고한 {1:812,...} 는 상태마다 '마지막으로 평가된 cover' 의 결손이었다 — 완전 통계가 아니다. 의미 있는 상태별 통계는 unsat_state_min_deficit 이다.",
                   seconds=round(time.time() - t0))
    json.dump(summary, open(OUT / "summary.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:2000])


if __name__ == "__main__":
    main()
