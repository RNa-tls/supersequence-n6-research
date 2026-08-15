#!/usr/bin/env python3
"""라운드 92 — 일반 short 예외를 fragment-local short 기회로 교체한다.

라운드 88/90 의 결합 모델은 short 예외를 `Gshort ∖ G5` 의 **아무 edge** 로 허용했다.
라운드 91 에서 독립 확인된 SHORT-PASS LOCALITY 는 그것이 지나치게 관대함을 보인다.

감사된 구조 (Q2 / Area-A / F=1 완성 범위).
    * 미래 short 예산은 `1 − r` 이다 (아카이브 6,657: 예산 1 이 5,947, 0 이 710).
    * abandonment 없이 새 부분 육각형이 생길 수 없고, 빈 육각형에서의 short 출발은
      abandonment 이며, 가득 찬 육각형은 no-repeat 상 매크로 edge 를 낼 수 없고,
      1칸짜리 현재 육각형은 `ℓ=5` 로만 떠나 곧 가득 찬다.
    * 따라서 남은 미래 short edge 는 **기존 fragment 구조에서만** 나온다.
    * 그 자리에서 출발 위치는 fragment 점유가 결정하고 `ℓ = 5 − c_f` 다.
      `c_f = 5` 면 `ℓ = 0` 이다 — "매크로 진입 마스크는 항상 부분적" 으로 강화하지 않는다.
      시간 상대적 locality 진술만 쓴다.

SHORT_LOCAL(s).
    예산 0 이면 공집합.  예산 1 이면 fragment 의 유일한 미방문 run 시작 칸에서 `ℓ = 5 − c_f`
    회전 후 4개 joint 로 갈 수 있는 target 을 모두 담는다 — fresh 궤도면 opening 후보다.
    **과대근사이어야 하므로** blocked-w2 보조정리로 제외 가능한 `w2` joint 도 남겨두고,
    착지 위상이 정해져도 후보를 좁히지 않는다.

공유 규칙.
    fragment 수리 edge 는 **모든** 완성에서 그 port 에서 발사되므로(라운드 87: port 당 1회),
    그 port 는 G5 opening 의 source 가 될 수 없다.  short 기회를 쓰든 안 쓰든 배제한다.
    생성과 용량이 각자 다른 short edge 를 쓰는 일이 없도록, 하나의 기회를 모델 전체가 공유한다.

사용법:
    python3 src/probe_rr_short_local.py build     # SHORT_LOCAL census (§2)
    python3 src/probe_rr_short_local.py control --model {budget2,generic1}   # §5
    python3 src/probe_rr_short_local.py sweep     # §6 본 판정
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.setrecursionlimit(20000)
ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ssp = _load("probe_rr_single_short_pass", "src/probe_rr_single_short_pass.py")
uc = _load("probe_rr_universal_cover", "src/probe_rr_universal_cover.py")
core, exact, macro = ssp.core, ssp.exact, ssp.macro
OP, HP, SRC, NORB = ssp.OP, ssp.HP, ssp.SRC, ssp.NORB
HEX_WORD = ssp.HEX_WORD
G5 = uc.G5


# ------------------------------------------------------------- SHORT_LOCAL


def short_local(state, open_bits):
    """상태의 fragment-local short 기회.  예산 0 이면 targets 는 비어 있다."""
    counts, current, fragments, _ = ssp.hexagon_profile(state)
    if not fragments:
        return dict(budget=0, targets=[], source_port=None, source_ports=[], ell=None,
                    hex=None, c_f=None, fresh_target_orbits=[])
    hf = fragments[0]
    cf = counts[hf]
    bits = [b for b in range(6) if state.hex_masks[hf] >> b & 1]
    unvisited = [b for b in range(6) if b not in bits]
    # 미방문 run 의 시작 = 앞 칸이 방문된 미방문 칸.  과대근사로 run 이 여러 개면 모두 담는다.
    entries = [b for b in unvisited if (b - 1) % 6 not in unvisited]
    targets, ports = [], []
    for entry in entries:
        word = HEX_WORD[(hf, entry)]
        run = [entry]
        while (run[-1] + 1) % 6 in unvisited and (run[-1] + 1) % 6 not in run:
            run.append((run[-1] + 1) % 6)
        ell = len(run) - 1
        cursor = word
        for _ in range(ell):
            cursor = core.word_after(cursor, core.SIGMA)
        ports.append(list(OP[word]))
        for move in macro.NONROT_H0:
            t = core.word_after(cursor, move.action)
            orbit, phase = OP[t]
            targets.append(dict(joint=move.label, ell=ell, source_port=list(OP[word]),
                                source_word=list(word), target_orbit=orbit, landing_phase=phase,
                                fresh=not (open_bits >> orbit & 1)))
    return dict(budget=1, hex=hf, c_f=cf, ell=5 - cf, source_port=ports[0] if ports else None,
                source_ports=ports, targets=targets,
                fresh_target_orbits=sorted({t["target_orbit"] for t in targets if t["fresh"]}))


# ------------------------------------------------------------- joint model


def port_matchable(targets, pool_orbits, banned_ports=()):
    """targets 를 pool 궤도의 port 에 매칭.  banned_ports 는 이미 소비된 port."""
    banned = set(map(tuple, banned_ports))
    adjacency = {t: [] for t in targets}
    for q in pool_orbits:
        for f in range(5):
            if (q, f) in banned:
                continue
            for t in SRC[(q, f)]:
                if t in adjacency:
                    adjacency[t].append((q, f))
    matched, size = {}, 0

    def augment(x, seen):
        for p in adjacency[x]:
            if p in seen:
                continue
            seen.add(p)
            if p not in matched or augment(matched[p], seen):
                matched[p] = x
                return True
        return False

    for t in sorted(targets):
        if augment(t, set()):
            size += 1
    return size == len(targets)


def feasible(S, a_bits, sl, model):
    """(SAT?, 사용한 short target).  model: 'local' | 'generic1' | 'budget2'."""
    S = set(S)
    pool = {q for q in range(NORB) if a_bits >> q & 1} | S
    if model == "local":
        banned = [tuple(p) for p in (sl["source_ports"] if sl["budget"] else [])]
        allowed = [r for r in sl["fresh_target_orbits"] if r in S] if sl["budget"] else []
        candidates = [()] + [(r,) for r in allowed]
    else:
        banned = []
        budget = 2 if model == "budget2" else sl["budget"]
        candidates = [T for k in range(budget + 1) for T in combinations(sorted(S), k)]
    for T in candidates:
        rest = S - set(T)
        a_eff = a_bits
        for q in T:
            a_eff |= 1 << q
        if not uc.g5_induced_reachable(a_eff, rest):
            continue
        if port_matchable(rest, pool, banned):
            return True, list(T)
    return False, None


def decide_state(row, sl, model):
    """모든 valid cover 를 흘려보내며 판정.  UNSAT 은 완전 유한 판정일 때만."""
    acc = {"verdict": "UNSAT", "cover": None, "short": None, "covers": 0}

    def on_cover(S, _a=row["open_orbits"], _sl=sl, _acc=acc):
        ok, T = feasible(S, _a, _sl, model)
        if ok:
            _acc["verdict"], _acc["cover"], _acc["short"] = "SAT", list(S), T
            return True
        return False

    scan = ssp.scan_covers(row, on_cover)
    acc["covers"] = scan["covers"]
    if acc["verdict"] == "UNSAT" and not scan["complete"]:
        acc["verdict"] = "UNKNOWN"
    return acc


# ---------------------------------------------------------------------- CLI


def run(rows, model, label):
    agg, out = Counter(), []
    t0 = time.time()
    for i, r in enumerate(rows):
        sl = short_local(r["state"], r["open_orbits"])
        res = decide_state(r, sl, model)
        agg[res["verdict"]] += 1
        out.append(dict(sid=r["sid"], root=r["root"], c=r["c"], K=r["K"],
                        budget=sl["budget"], verdict=res["verdict"], covers=res["covers"],
                        short_local_size=len(sl["fresh_target_orbits"]) if sl["budget"] else 0,
                        witness_cover=res["cover"], witness_short=res["short"]))
        if (i + 1) % 1000 == 0:
            print(f"  [{label}] {i+1}/{len(rows)} {dict(agg)} {time.time()-t0:.0f}s", flush=True)
    print(f"[{label}] {dict(agg)} {time.time()-t0:.0f}s", flush=True)
    return agg, out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("build", "control", "sweep"))
    ap.add_argument("--model", choices=("local", "generic1", "budget2"), default="local")
    ap.add_argument("--exclude", help="이미 닫힌 sid 목록 JSON (sweep 의 기준선 축소용)")
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = ssp.po.load_states()
    print(f"archive states: {len(rows)}", flush=True)

    if args.command == "build":
        size, tgt, ports, cf, byc, zero = Counter(), Counter(), Counter(), Counter(), defaultdict(Counter), 0
        table = []
        for r in rows:
            sl = short_local(r["state"], r["open_orbits"])
            n = len(sl["fresh_target_orbits"])
            size[n if sl["budget"] else "budget0"] += 1
            if sl["budget"]:
                cf[sl["c_f"]] += 1
                tgt[len({t["target_orbit"] for t in sl["targets"]})] += 1
                ports[len(sl["source_ports"])] += 1
                byc[r["c"]][n] += 1
                if n == 0:
                    zero += 1
            table.append(dict(sid=r["sid"], root=r["root"], c=r["c"], budget=sl["budget"],
                              hex=sl["hex"], c_f=sl["c_f"], ell=sl["ell"],
                              source_ports=sl["source_ports"] if sl["budget"] else [],
                              fresh_target_orbits=sl["fresh_target_orbits"] if sl["budget"] else [],
                              targets=sl["targets"] if sl["budget"] else []))
        result = dict(states=len(rows),
                      short_local_size_histogram={str(k): v for k, v in sorted(size.items(), key=str)},
                      distinct_target_orbits={str(k): v for k, v in sorted(tgt.items())},
                      source_ports={str(k): v for k, v in sorted(ports.items())},
                      c_f_histogram={str(k): v for k, v in sorted(cf.items())},
                      budget1_with_zero_fresh_targets=zero,
                      by_collision_band={str(k): dict(v) for k, v in sorted(byc.items())},
                      table=table)
    elif args.command == "control":
        agg, out = run(rows, args.model, f"control:{args.model}")
        result = dict(model=args.model, states=len(rows), aggregate=dict(agg),
                      closed=[o["sid"] for o in out if o["verdict"] == "UNSAT"], ledger=out)
    else:
        closed = set()
        if args.exclude:
            data = json.load(open(args.exclude))
            closed = set(data if isinstance(data, list) else data["closed"])
        base = [r for r in rows if r["sid"] not in closed]
        print(f"baseline after excluding {len(closed)} already-closed: {len(base)}", flush=True)
        agg, out = run(base, "local", "sweep")
        newly = [o for o in out if o["verdict"] == "UNSAT"]
        result = dict(model="local", input_states=len(base), aggregate=dict(agg),
                      new_closures=len(newly),
                      by_c=dict(Counter(o["c"] for o in newly)),
                      by_root=dict(Counter(o["root"] for o in newly)),
                      by_budget=dict(Counter(o["budget"] for o in newly)),
                      survivors_short_usage=dict(Counter(
                          "no_short" if o["verdict"] == "SAT" and not o["witness_short"]
                          else "uses_short" if o["verdict"] == "SAT" else "closed_or_unknown"
                          for o in out)),
                      ledger=out)
    print(json.dumps({k: v for k, v in result.items() if k not in ("table", "ledger", "closed")},
                     ensure_ascii=False, indent=1)[:3000])
    if args.out:
        json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
