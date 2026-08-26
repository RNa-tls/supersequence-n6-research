#!/usr/bin/env python3
"""라운드 121 — `(k,F) = (2,1)` 칸의 정확 탐색.

자원 표(`src/verify_f1_k2_budget_121.py`)에서 **17개 그룹**이 나온다.  `S+H <= 26` 이
`e + x + H <= 1 + f_out` 과 동치이므로 `(e, f_out, H, 조성)` 을 고정하면 `x` 의 상한이
`1 + f_out - e - H` 로 정해지고, 그 넷이 24개 자원 행 전체를 **정확히** 덮는다.

    e = 0 : f_out = 0, 1                    (Lemma E: f_out <= 1 + e)
    e = 1 : f_out = 0, 1, 2
    e = 2 : f_out = 1, 2                    (e + x + H <= 1 + f_out)
    e = 3 : f_out = 2
    H = 2 는 조성이 둘이다 — 무게-4 두 개 또는 무게-5 하나 (브리프 §12: 합치지 않는다).

`f_out` 을 정확히 고정하는 것이 실측으로 큰 차이를 냈다 (`e=1, H=0` 에서
5.19e9 -> 2.09e9 노드).  `costcap = 26 - H`, `dcap = 9`, `exccap = 10`, `fod = 1`.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_cell_121.bin"
SRC = ROOT / "src" / "f1_cell_121.c"
JSONL = OUT / "rr_f1_k2_121.jsonl"
NODECAP = 150_000_000_000


def groups():
    """the 17 exact groups; their union is precisely the 24 resource rows of (2,1)."""
    out = []
    for e in range(0, 4):
        for f in range(0, min(2, 1 + e) + 1):
            budget = 1 + f - e                      # max x + H
            if budget < 0:
                continue
            for H in range(0, min(2, budget) + 1):
                x = budget - H
                comps = {0: [("H0", 1, 0)],
                         1: [("H1w4", 1, 1)],
                         2: [("H2w4w4", 1, 2), ("H2w5", 2, 1)]}[H]
                for tag, hw, hjcap in comps:
                    # Round 121 section 5.  Phi preserves O exactly when X's exit
                    # joint is free, which f_out = 2 forces, so on those groups Phi maps
                    # the cell (2,1) onto itself.  Phi sends b -> 6-b, so for f_out = 2 we
                    # may CANONICALISE ON b <= 3: a walk with b in {4,5} has a Phi-image
                    # with b in {2,1}, which some group covers at that split.  Measured:
                    # this beats the prefix<=suffix canonical form by a wide margin
                    # (40% of the runs versus 2% of the nodes).
                    splits = [1, 2, 3] if f == 2 else [1, 2, 3, 4, 5]
                    # Round 121 section 8: at f_out = 2 both short passes exit freely, so
                    # X's free successor opens a run of orb(Y) and orb(X) already spends one
                    # unit of e on R_X^end / R_X^start.  If orb(Y) has a SINGLE run it goes
                    # from phase phi+1 to phi, advancing +4 in at most 4 steps, so
                    # dist(X,Y) <= 5.  At e = 1 that is forced.  At e >= 2 we split:
                    #   A: dist(X,Y) <= 5
                    #   B: dist(X,Y) >= 6  =>  orb(Y) has >= 2 runs; at e = 2 that uses up
                    #      the whole revisit budget, so the revisited orbits are exactly
                    #      orb(X) and orb(Y) (revonly) and orb(Y) cannot have been entered
                    #      before X (yfresh) -- Round 119 section 3's argument, re-derived.
                    if f == 2 and e == 1:
                        variants = [("", 5, 0, 0, 0)]           # gap <= 5 is forced
                    elif f == 2 and e == 2:
                        variants = [("A", 5, 0, 0, 0), ("B", 0, 6, 1, 1)]
                    elif f == 2 and e >= 3:
                        variants = [("A", 5, 0, 0, 0), ("B", 0, 6, 0, 0)]
                    else:
                        variants = [("", 0, 0, 0, 0)]
                    for vtag, ygap, ygapmin, revonly, yfresh in variants:
                        out.append(dict(
                            label=f"e{e}_f{f}_{tag}" + (f"_{vtag}" if vtag else ""),
                            e=e, f_out=f, H=H, xcap=x, heavy=tag, variant=vtag,
                            S_max=25 + e + x - f, ygap=ygap, ygapmin=ygapmin,
                            revonly=revonly, yfresh=yfresh, splits=splits,
                            rows=[(e, xx, f, H) for xx in range(x + 1)],
                            # b cost orb x fout e fmin ygap rmax hcap dcap bf rev hreg yf
                            # exc seam pmax sym shcap hw hjcap hubmin fod ygapmin
                            args=[26 - H, 26, x, f, e, f, ygap, 26 + e, H, 9, 0, revonly,
                                  0, yfresh, 10, 0, 0, 0, 26, hw, hjcap, H, 1, ygapmin]))
    return out


GROUPS = groups()


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done_keys():
    if not JSONL.exists():
        return set()
    return {(json.loads(l)["label"], json.loads(l)["b"])
            for l in JSONL.read_text().splitlines() if l.strip()}


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    by = {}
    for g in GROUPS:
        rs = [r for r in rows if r["label"] == g["label"]]
        by[g["label"]] = dict(
            e=g["e"], f_out=g["f_out"], H=g["H"], xcap=g["xcap"], heavy=g["heavy"],
            variant=g["variant"], ygap=g["ygap"], ygapmin=g["ygapmin"],
            runs=len(rs),
            splits=g["splits"],
            closed=(len(rs) == len(g["splits"])
                    and all(r["verdict"] == "UNSAT_COMPLETE" for r in rs)),
            nodes=sum(r["nodes"] for r in rs), seconds=round(sum(r["seconds"] for r in rs)),
            max_passes=max((r["best_passes"] for r in rs), default=0))
    closed = [k for k, v in by.items() if v["closed"]]
    covered = set()
    for g in GROUPS:
        if by[g["label"]]["closed"]:
            covered |= {tuple(r) for r in g["rows"]}
    all_rows = set()
    for g in GROUPS:
        all_rows |= {tuple(r) for r in g["rows"]}
    rep = dict(round=121, cell=[2, 1], node_cap=NODECAP,
               n_groups=len(GROUPS), runs=len(rows), verdicts=verdicts,
               by_group=by, groups_closed=closed,
               rows_total=len(all_rows), rows_closed=len(covered),
               rows_open=sorted(all_rows - covered),
               cell_closed=(len(closed) == len(GROUPS)),
               total_nodes=sum(r["nodes"] for r in rows),
               total_seconds=round(sum(r["seconds"] for r in rows)),
               max_passes_reached=max((r["best_passes"] for r in rows), default=0),
               sat_found=any(r["verdict"] == "SAT" for r in rows),
               label="ROUND-121 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
               rows=rows,
               ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                       "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                       "unchanged_by_this_round": True},
               disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k2_121.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main(bs=range(1, 6)):
    build()
    have = done_keys()
    fh = open(JSONL, "a", buffering=1, encoding="utf-8")
    for b in bs:
        for g in GROUPS:
            if b not in g["splits"] or (g["label"], b) in have:
                continue
            t0 = time.time()
            r = subprocess.run([str(BIN), str(b)] + [str(a) for a in g["args"]]
                               + [str(NODECAP)], capture_output=True, text=True, check=True)
            lines = [x for x in r.stdout.splitlines() if x.strip()]
            d = json.loads(lines[0])
            d.update(label=g["label"], e=g["e"], f_out_row=g["f_out"], H_row=g["H"],
                     heavy=g["heavy"], seconds=round(time.time() - t0, 1),
                     splits=[b, 6 - b])
            if len(lines) > 1:
                d["witness"] = json.loads(lines[1])
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            print(f"  {g['label']:16s} b={b}: {d['verdict']:15s} best={d['best_passes']:3d} "
                  f"nodes={d['nodes']:>15,} {d['seconds']:>8}s", flush=True)
            summarise()
            if d["verdict"] == "SAT":
                print("  *** SAT - stopping this group; section 21 replay handling ***",
                      flush=True)
                fh.close()
                return
    fh.close()
    rep = summarise()
    print(f"verdicts: {rep['verdicts']}  groups closed: {len(rep['groups_closed'])}"
          f"/{rep['n_groups']}  cell closed: {rep['cell_closed']}")


if __name__ == "__main__":
    import sys
    bs = [int(a) for a in sys.argv[1:]] or list(range(1, 6))
    main(bs)
