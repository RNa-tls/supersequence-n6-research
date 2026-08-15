#!/usr/bin/env python3
"""라운드 90 — 단일 short pass 정리와 유일-cover 19개 상태의 부검.

라운드 85 는 "앞으로 `ell < 5` 인 매크로 edge 는 **최대 2개**"를 증명했다(현재 pass 와
fragment 수리).  이 모듈은 리터럴 체크포인트 상태에서 그 예산이 실제로는 더 작고, 게다가
**출발 port 와 회전 길이까지 고정**된다는 것을 보인다.

정리 (단일 short pass).
    `F = 1 = TARGET_F` 이고 현재 육각형에 방문 칸이 정확히 1개(= 현재 endpoint)인
    도달가능 상태에서, 모든 합법적 완성에 대하여

      (i)   pass 는 한 육각형 안의 연속된 `ell + 1` 칸을 방문하고 joint 로 떠난다.
      (ii)  `F = TARGET_F` 이므로 앞으로 abandonment 는 불가능하다.  즉 떠나는 칸 `w` 는
            `sigma(w)` 가 이미 방문된 칸이어야 한다.
      (iii) 120 육각형 · `P = 121` pass · 모든 육각형은 pass 를 최소 1회 받으므로
            **정확히 한 육각형만 2회** 받는다.  fragment 는 이미 1회 받았고 아직 불완전하니
            그 육각형이 바로 그 하나이며, 나머지 육각형은 정확히 1회씩 받는다.
      (iv)  따라서 fragment 를 제외한 모든 미래 pass 는 육각형을 통째로 채워야 하므로
            `ell = 5` 이고, 현재 pass 도(방문 1칸) `ell = 5` 다.
      (v)   fragment `h_f` 의 방문 칸이 `c_f` 개(연속)라면, 남은 `6 - c_f` 칸을 한 pass 가
            모두 방문해야 하므로 그 pass 의 시작 칸은 **유일하게** `v_{c_f}` (방문 블록의
            바로 다음 칸)이고 회전 길이는 정확히 `ell = 5 - c_f` 다.

    결론: 미래의 `ell < 5` 매크로 edge 는 fragment 가 있으면 **정확히 1개**, 없으면 **0개**이며,
    있을 때 그 출발 port 와 `ell` 은 상태가 결정한다.  목표 후보는 그 port 에서 `ell` 회전 후
    4개 joint 로 갈 수 있는 궤도뿐이다.

판정 모델 M2.
    * fresh-orbit opening 은 등록 port 에서 출발하고 각 port 는 1회만 발사한다 (라운드 87)
    * opening 은 반드시 Z3(weight 3) joint 다 (라운드 83 blocked-w2 보조정리)
    * source 궤도는 최종 열린 집합 `A ∪ S` 안에 있고 그 시점에 이미 열려 있어야 한다
      (부모 구조가 `A`-rooted ⟺ 사이클 없음)
    * 위 정리에 의해 opening 은 모두 `G5`(ell = 5) 이며, 예외는 고정된 수리 edge 하나뿐

    M2 는 라운드 88 의 결합 조건보다 강하다: 예산이 2 에서 1(또는 0)로 줄고, 그 1개의
    출발 port·회전 길이·목표 후보까지 고정되며, 도달성과 매칭을 **하나의 배정**이 동시에
    만족해야 한다.  과대근사(안전)로 남겨둔 것: `E1`/`E2` 수리와 재진입이 소비하는 port 를
    세지 않고, opening 출발 port 가 빈 육각형에 있어야 한다는 조건도 걸지 않는다.

사용법:
    python3 src/probe_rr_single_short_pass.py census      # 전제·예산 census (리터럴 상태)
    python3 src/probe_rr_single_short_pass.py pin         # 고정 short edge 산출
    python3 src/probe_rr_single_short_pass.py decide      # M2 판정 (--sids 로 제한 가능)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.setrecursionlimit(20000)
ROOT = Path(__file__).resolve().parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


po = _load("probe_rr_port_occupancy", "probe_rr_port_occupancy.py")
cap = _load("probe_rr_source_capacity", "probe_rr_source_capacity.py")
exact = po.exact
core = po.core
macro = po.macro
slack = cap.slack
NORB = po.NORB
BLOCKBITS = slack.BLOCKBITS
SRC = cap.SRC                     # (q, f) -> ell = 5 Z3 로 열리는 target 궤도 집합
OP = exact.ORBIT_PHASE
HP = exact.HEX_POSITION
HEX_WORD = {(h, b): w for w, (h, b) in HP.items()}
pc = int.bit_count
NODE_CAP = 20_000_000
COVER_CAP = 200_000


# --------------------------------------------------------------- 정리의 전제


def hexagon_profile(state):
    """(부분 육각형 목록, 현재 육각형, 빈 육각형 수) — 리터럴 상태에서 직접."""
    counts = [pc(m) for m in state.hex_masks]
    current = HP[state.p][0]
    partial = [h for h, c in enumerate(counts) if 0 < c < 6]
    fragments = [h for h in partial if h != current]
    return counts, current, fragments, sum(1 for c in counts if c == 0)


def pinned_short_edge(state):
    """정리 (v): 고정된 수리 pass 의 출발 단어·port·ell·목표 후보.  fragment 가 없으면 None."""
    counts, current, fragments, _ = hexagon_profile(state)
    if counts[current] != 1 or state.F != 1:
        return None, "premise_failed"
    if not fragments:
        return None, "no_fragment"
    if len(fragments) > 1:
        return None, "multiple_fragments"
    hf = fragments[0]
    cf = counts[hf]
    bits = [b for b in range(6) if state.hex_masks[hf] >> b & 1]
    starts = [s for s in range(6) if all((s + i) % 6 in bits for i in range(cf))]
    if len(bits) != cf or not starts:
        return None, "fragment_not_contiguous"
    word = HEX_WORD[(hf, (starts[0] + cf) % 6)]
    ell = 5 - cf
    cursor = word
    for _ in range(ell):
        cursor = core.word_after(cursor, core.SIGMA)
    targets = []
    for move in macro.NONROT_H0:
        t = core.word_after(cursor, move.action)
        targets.append(dict(joint=move.label, orbit=OP[t][0], phase=OP[t][1]))
    return dict(hex=hf, c_f=cf, word=list(word), port=list(OP[word]), ell=ell,
                targets=targets, departs_legally=state.visited(
                    core.word_after(cursor, core.SIGMA))), "ok"


# ------------------------------------------------------------------ M2 판정


def generate_all_g5(S, A, forced=None):
    """A-rooted, port-단사, 전부 G5 인 부모 배정을 하나 찾는다 (완전 판정, 첫 해에서 중단).

    `forced` 는 (r, (q, f)) — 고정 short edge 가 r 을 열 때 미리 소비되는 port.
    """
    Aset = set(A)
    pool = sorted(Aset | set(S))
    Sset = set(S)
    options = {r: [(q, f) for q in pool if q != r for f in range(5) if r in SRC[(q, f)]]
               for r in S}
    parent, used = {}, set()
    st = {"nodes": 0, "complete": True, "solution": None}
    if forced:
        r0, port0 = forced
        parent[r0] = port0[0]
        used.add(tuple(port0))

    def reaches(a, b):
        seen = set()
        while a in parent and a not in seen:
            seen.add(a)
            if a == b:
                return True
            a = parent[a]
        return a == b

    def rec(remaining):
        if st["solution"] is not None:
            return
        if st["nodes"] > NODE_CAP:
            st["complete"] = False
            return
        if not remaining:
            st["solution"] = dict(parent)
            return
        st["nodes"] += 1
        best, fewest = None, 1 << 30
        for r in remaining:
            n = sum(1 for p in options[r] if p not in used)
            if n < fewest:
                best, fewest = r, n
            if n == 0:
                return
        rest = remaining - {best}
        for (q, f) in options[best]:
            if (q, f) in used:
                continue
            if q in Sset and reaches(q, best):
                continue
            used.add((q, f))
            parent[best] = q
            rec(rest)
            used.discard((q, f))
            del parent[best]
            if st["solution"] is not None or not st["complete"]:
                return

    rec(frozenset(r for r in S if not (forced and r == forced[0])))
    return st


def decide_cover(S, A, pin):
    """cover S 가 M2 아래에서 생성 가능한가.  (verdict, 사용한 분기, 노드 수)."""
    nodes = 0
    st = generate_all_g5(S, A)
    nodes += st["nodes"]
    if st["solution"] is not None:
        return "SAT", "all_G5", nodes
    complete = st["complete"]
    if pin:
        port = tuple(pin["port"])
        for r in sorted({t["orbit"] for t in pin["targets"]} & set(S)):
            st2 = generate_all_g5(S, A, forced=(r, port))
            nodes += st2["nodes"]
            complete = complete and st2["complete"]
            if st2["solution"] is not None:
                return "SAT", f"pinned_opens_{r}", nodes
    return ("UNSAT" if complete else "UNKNOWN"), "none", nodes


def scan_covers(row, on_cover, cap_count=COVER_CAP):
    """valid slack-cover 를 하나씩 흘려보내며 `on_cover` 로 판정.  True 를 반환하면 중단.

    전부 열거해 담아두면 cover 가 수천 개인 상태에서 낭비가 크다.  SAT 는 대개 첫 몇 개에서
    나오므로 스트리밍하고, UNSAT 일 때만 끝까지 간다.  캡에 닿으면 complete=False.
    """
    U, K, b, cand = row["U"], row["K"], row["b"], row["candidates"]
    by_hex = defaultdict(list)
    for q in cand:
        m = BLOCKBITS[q] & U
        while m:
            low = m & -m
            by_hex[low.bit_length() - 1].append(q)
            m ^= low
    seen = set()
    st = {"nodes": 0, "complete": True, "stop": False, "covers": 0}

    def rec(remaining, k, chosen):
        if st["stop"]:
            return
        if remaining == 0:
            key = tuple(sorted(chosen))
            if key not in seen:
                seen.add(key)
                st["covers"] += 1
                if on_cover(list(key)):
                    st["stop"] = True
            return
        if k == 0:
            return
        st["nodes"] += 1
        if st["nodes"] > 3_000_000 or len(seen) > cap_count:
            st["complete"] = False
            return
        slackness = 5 * k - pc(remaining)
        if slackness < 0:
            return
        h = (remaining & -remaining).bit_length() - 1
        for q in by_hex[h]:
            if pc(BLOCKBITS[q] & remaining) < 5 - slackness:
                continue
            chosen.append(q)
            rec(remaining & ~BLOCKBITS[q], k - 1, chosen)
            chosen.pop()
            if not st["complete"] or st["stop"]:
                return

    rec(U, K, [])
    return st


# ---------------------------------------------------------------------- CLI


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("census", "pin", "decide"))
    ap.add_argument("--sids", help="쉼표로 구분된 sid 목록 또는 JSON 파일 경로")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = po.load_states()
    if args.sids:
        p = Path(args.sids)
        if p.exists():
            data = json.load(open(p))
            want = {u["sid"] for u in (data["unique_states"] if isinstance(data, dict) else data)}
        else:
            want = set(args.sids.split(","))
        rows = [r for r in rows if r["sid"] in want]
    if args.limit:
        rows = rows[:args.limit]
    print(f"literal states: {len(rows)}", flush=True)
    result = {}

    if args.command == "census":
        profile, budget, identity = Counter(), Counter(), Counter()
        for r in rows:
            counts, current, fragments, empty = hexagon_profile(r["state"])
            profile[(len(fragments) + 1 if counts[current] < 6 else len(fragments),
                     counts[current], r["state"].F)] += 1
            budget[len(fragments) + (0 if counts[current] == 1 else 1)] += 1
            identity[121 - r["state"].P == empty + len(fragments)] += 1
        result = dict(states=len(rows),
                      profile={str(k): v for k, v in profile.items()},
                      future_short_pass_budget={str(k): v for k, v in budget.items()},
                      pass_count_identity={str(k): v for k, v in identity.items()},
                      note="예산은 정리 (iv)(v) 로 결정된다 — 라운드 85 의 상한 2 가 아니다")
    elif args.command == "pin":
        pins, why = [], Counter()
        for r in rows:
            pin, reason = pinned_short_edge(r["state"])
            why[reason] += 1
            if pin:
                pins.append(dict(sid=r["sid"], root=r["root"], **pin))
        result = dict(states=len(rows), reasons=dict(why), pins=pins,
                      all_depart_legally=all(p["departs_legally"] for p in pins))
    else:
        agg, closed, unknown = Counter(), [], []
        t0 = time.time()
        for i, r in enumerate(rows):
            pin, _ = pinned_short_edge(r["state"])
            A = [q for q in range(NORB) if r["open_orbits"] >> q & 1]
            acc = {"verdict": "UNSAT", "branch": "none", "nodes": 0}

            def on_cover(S, _acc=acc, _A=A, _pin=pin):
                v, br, n = decide_cover(S, _A, _pin)
                _acc["nodes"] += n
                if v == "SAT":
                    _acc["verdict"], _acc["branch"] = "SAT", br
                    return True
                if v == "UNKNOWN":
                    _acc["verdict"] = "UNKNOWN"
                return False

            scan = scan_covers(r, on_cover)
            verdict = acc["verdict"]
            if verdict == "UNSAT" and not scan["complete"]:
                verdict = "UNKNOWN"
            agg[verdict] += 1
            if verdict == "UNSAT":
                closed.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=r["K"],
                                   covers=scan["covers"], nodes=acc["nodes"]))
            elif verdict == "UNKNOWN":
                unknown.append(r["sid"])
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{len(rows)} {dict(agg)} {time.time()-t0:.0f}s", flush=True)
        result = dict(states=len(rows), aggregate=dict(agg), closed=closed,
                      unknown=unknown, seconds=round(time.time() - t0))
    print(json.dumps({k: v for k, v in result.items() if k not in ("pins", "closed", "unknown")},
                     ensure_ascii=False, indent=1)[:3000])
    if args.out:
        json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
