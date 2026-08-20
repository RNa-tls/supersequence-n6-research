#!/usr/bin/env python3
"""라운드 109 — 라운드-108 이 캡 때문에 남긴 **166개 상태**를 좁게 마무리한다.

모델은 **라운드 108 과 완전히 같다** (`certify_rr_full_joint` 를 그대로 import 한다):
550개 indecomposable tail 전부 · 정확 비용 `cost(w) = [w>=3] + max(w-3,0)` ·
유일 비용-0 호 `T1` · 자원 예산 `Σcost <= B` · 제한 성분 하한 · 정정된 메모 키.
**(H5) 는 어디에서도 쓰지 않는다.**

이 파일이 더한 것은 **실행 방식**뿐이다:
  * 상태를 하나 끝낼 때마다 JSONL 한 줄을 즉시 flush 한다 (중단돼도 결과가 남는다),
  * `--resume` 으로 이미 판정된 상태를 건너뛴다,
  * `--cap` 으로 단계별 노드 캡을 준다 (**호출당**, 실행 전체 공유가 아니다),
  * 상태 판정은 `UNSAT_COMPLETE` / `SAT` / `UNKNOWN_CAP` 셋 중 하나다,
  * SAT 이면 §7 이 요구하는 증인 전체를 그 자리에서 보존한다.

사용법:
    python3 src/complete_rr_round109.py --cap 50000 --out rr_round109_stage1.jsonl
    python3 src/complete_rr_round109.py --cap 200000 --resume --only-unknown-from <stage1>
"""

from __future__ import annotations

import argparse
import importlib.util as iu
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
VERSION = "claude-r109-complete/1"


def _load(name, path):
    spec = iu.spec_from_file_location(name, path)
    mod = iu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FJ = _load("certify_rr_full_joint", ROOT / "src" / "certify_rr_full_joint.py")
C = FJ.C


def witness_record(sid, cid, B, A, ell, root, nodes, out, rt, s, stats, word):
    """§7 — SAT 증인을 통째로 보존한다 (그래프 수준)."""
    order = stats.get("witness", [])
    seq = []
    total = 0
    for cost, idx in order:
        node = nodes[idx]
        total += cost
        seq.append({"obligation": list(node), "entry_word": word[A[node]],
                    "ell": ell[node], "arc_cost": cost})
    return {"sid": sid, "cover_id": cid, "B": B, "root_slack": s,
            "root_word": word[root], "total_cost": total,
            "obligation_order": seq,
            "assignment": {str(list(k)): word[v] for k, v in A.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, required=True, help="배정당(호출당) 노드 캡")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only-unknown-from", default="",
                    help="이 JSONL 에서 UNKNOWN_CAP 인 상태만 다시 돈다")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--stop-after", type=int, default=0, help="초 단위 벽시계 상한 (0=무제한)")
    args = ap.parse_args()
    t0 = time.time()

    order = json.loads((OUT / "rr_round109_schedule.json").read_text())["easiest_first"]
    frozen = json.loads((OUT / "rr_h5_audit" / "round109_input_states.json").read_text())
    assert set(order) == set(frozen["sids"]), "일정 목록이 동결된 166 과 다르다"
    targets = list(order)
    if args.only_unknown_from:
        prev = {}
        with open(OUT / args.only_unknown_from) as fh:
            for line in fh:
                r = json.loads(line)
                prev[r["sid"]] = r["verdict"]
        targets = [s for s in targets if prev.get(s) == "UNKNOWN_CAP"]
    outpath = OUT / args.out
    done = set()
    if args.resume and outpath.exists():
        with open(outpath) as fh:
            for line in fh:
                done.add(json.loads(line)["sid"])
        targets = [s for s in targets if s not in done]
    if args.limit:
        targets = targets[:args.limit]

    word, orb, hexm, jt = C.geometry()
    ident = {w: i for i, w in word.items()}
    mc = FJ.min_cost_table(word, ident)
    rot = {(i, k): FJ.rot_id(word, ident, i, k) for i in range(720) for k in range(6)}
    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    _h, covers = C.read_jsonl(C.ARCHIVE / "covers.jsonl.gz")
    _h, hall = C.read_jsonl(C.ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        passing[h["sid"]].append(h["cover_id"])

    print(f"[round109] states={len(targets)} cap={args.cap} solver=full-550-tail "
          f"(H5 unused) out={args.out}", flush=True)
    fh_out = open(outpath, "a", buffering=1)
    tally = Counter()
    for n, sid in enumerate(targets, 1):
        st = S[sid]
        B = 3 + st["K"] - (st["S"] + st["F"] - st["O"]) - st["H"]
        ts = time.time()
        stat = Counter()
        n_assign = n_unsat = n_unknown = n_sat = 0
        max_nodes = 0
        sat_witness = None
        for cid in sorted(passing[sid]):
            dom, ell, root = C.domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
            for A in C.assignments(dom):
                n_assign += 1
                _n2, lout0, lout1, lr0, lr1 = C.weighted_graph(A, ell, root, jt)
                s = B - FJ.root_bound(lout0, lr0)
                if s < 0:
                    n_unsat += 1
                    continue
                if s == 0:
                    # 무거운-호 예산 보조정리: 무거운 호를 쓸 수 없다 → 가벼운 탐색이 완전하다
                    before = stat["nodes"]
                    v = C.solve(lout0, lout1, lr0, lr1, B, stat, node_cap=args.cap)
                    max_nodes = max(max_nodes, stat["nodes"] - before)
                else:
                    nodes, out, rt = FJ.full_graph(A, ell, root, word, ident, mc, rot)
                    keep = min(FJ.MAXC, s + 1)
                    for cc in range(keep + 1, FJ.MAXC + 1):
                        out[cc] = [0] * len(out[cc])
                        rt[cc] = 0
                    before = stat["nodes"]
                    v, _hh = FJ.search(out, rt, B, stat, node_cap=args.cap, excess_budget=s)
                    max_nodes = max(max_nodes, stat["nodes"] - before)
                    if v == "SAT":
                        sat_witness = witness_record(sid, cid, B, A, ell, root, nodes,
                                                     out, rt, s, stat, word)
                if v == "UNSAT":
                    n_unsat += 1
                elif v == "SAT":
                    n_sat += 1
                else:
                    n_unknown += 1
        verdict = ("SAT" if n_sat else
                   "UNSAT_COMPLETE" if n_unknown == 0 else "UNKNOWN_CAP")
        row = {"sid": sid, "verdict": verdict, "cap": args.cap,
               "assignments": n_assign, "unsat": n_unsat, "unknown": n_unknown,
               "sat": n_sat, "frontier_exhausted": n_unknown == 0 and n_sat == 0,
               "nodes": stat["nodes"], "max_nodes_one_solve": max_nodes,
               "prune_cost": stat["prune_cost"], "seconds": round(time.time() - ts, 1),
               "solver": VERSION, "tails": 550, "h5_used": False}
        if sat_witness:
            row["sat_witness"] = sat_witness
        fh_out.write(json.dumps(row, ensure_ascii=False) + "\n")
        tally[verdict] += 1
        if n_sat:
            print(f"[round109] *** SAT at {sid} — 중단하고 증인을 보존한다 ***", flush=True)
            break
        if n % 5 == 0 or verdict != "UNSAT_COMPLETE":
            print(f"  {n}/{len(targets)} {sid[:12]} {verdict} "
                  f"nodes={stat['nodes']} {row['seconds']}s "
                  f"[{dict(tally)}] total={time.time()-t0:.0f}s", flush=True)
        if args.stop_after and time.time() - t0 > args.stop_after:
            print(f"[round109] 벽시계 상한 도달 — {n} 상태에서 멈춘다", flush=True)
            break
    fh_out.close()
    print(json.dumps({"round": 109, "cap": args.cap, "processed": sum(tally.values()),
                      "tally": dict(tally), "seconds": round(time.time() - t0)},
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
