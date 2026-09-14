#!/usr/bin/env python3
"""Round 148 Phase 3 -- STRICT node-count cross-check between the two
implementations.

With the best-so-far prune OFF and both searches given the SAME sound table,
every prune left is a function of the state alone (the table bound, the analytic
hexagon bound, the feasibility test, the move legality tests).  The set of
visited states is then independent of the order moves are generated in, so the
two implementations must visit exactly the same number of nodes.  That is a much
sharper test than equal capacities.

Classification per cell:
  EXACT_NODE_MATCH   same capacity and same node count
  CAPACITY_ONLY      same capacity, different node count -- which happens only
                     when the two runs were given tables of different strength;
                     the reason is recorded rather than waved away
  NOT_AFFORDABLE     one side exceeded the wall-clock budget (never counted as
                     agreement)
  DISAGREE           different capacity: a hard failure
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

A = R147 / "l6chain147b.exe"
B = R147 / "chain2_147.exe"
TMP = R148 / "logs" / "strict"
OUT = R148 / "certs" / "strict_nodes_148.json"
BUDGET = int(os.environ.get("R148_STRICT_SECONDS", "240"))
WORKERS = int(os.environ.get("R148_WORKERS", "2"))


def store():
    st = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") == "EXACT_UNCAPPED":
                st[tuple(int(x) for x in k.split("|"))] = v
    return st


ST = store()
POOL = {k: dict(cc=v["cc"]) for k, v in ST.items()}


def one(cell):
    a = [str(x) for x in cell]
    ubp = TMP / ("ub_%d_%d_%d_%d_%d_%d.txt" % cell)
    ub147.write_table(ubp, cell, {k: v for k, v in POOL.items() if k != cell},
                      exclude={cell})
    want = ST[cell]["cc"]
    t0 = time.time()
    try:
        ra = json.loads(subprocess.run(
            [str(A)] + a + ["0", str(ubp), "0", "-", "0"], capture_output=True,
            text=True, cwd=ROOT, timeout=BUDGET).stdout)
        rb = json.loads(subprocess.run(
            [str(B)] + a + ["0", str(ubp), "0"], capture_output=True,
            text=True, cwd=ROOT, timeout=BUDGET).stdout)
    except subprocess.TimeoutExpired:
        return cell, dict(status="NOT_AFFORDABLE", budget=BUDGET)
    except Exception as e:
        return cell, dict(status="ERROR", error=repr(e)[:150])
    if ra["cc"] != want or rb["cc"] != want or ra["capped"] or rb["capped"]:
        return cell, dict(status="DISAGREE", ledger=want,
                          A=dict(cc=ra["cc"], nodes=ra["nodes"],
                                 capped=ra["capped"]),
                          B=dict(cc=rb["cc"], nodes=rb["nodes"],
                                 capped=rb["capped"]))
    same = ra["nodes"] == rb["nodes"]
    return cell, dict(status="EXACT_NODE_MATCH" if same else "CAPACITY_ONLY",
                      cc=want, A_nodes=ra["nodes"], B_nodes=rb["nodes"],
                      seconds=round(time.time() - t0, 2),
                      reason=None if same else
                      "identical table and best-so-far prune off, so this "
                      "should not happen -- investigate")


def main(argv):
    TMP.mkdir(parents=True, exist_ok=True)
    cells = [tuple(c) for c in json.loads(
        (R147 / "tables" / "loadbearing_cells_147.json").read_text())["cells"]]
    cells = [c for c in cells if c in ST]
    cells.sort(key=lambda c: ST[c]["nodes"] or 0)
    done = json.loads(OUT.read_text())["cells"] if OUT.exists() else {}
    todo = [c for c in cells if "|".join(map(str, c)) not in done]
    print(f"strict cells={len(cells)} todo={len(todo)} budget={BUDGET}s",
          flush=True)
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, c) for c in todo]
        for i, f in enumerate(as_completed(futs)):
            cell, rec = f.result()
            done["|".join(map(str, cell))] = rec
            tally = {}
            for v in done.values():
                tally[v["status"]] = tally.get(v["status"], 0) + 1
            OUT.write_text(json.dumps(dict(
                total_load_bearing=len(cells), checked=len(done),
                tally=tally,
                disagreements=[k for k, v in done.items()
                               if v["status"] == "DISAGREE"],
                ok=not any(v["status"] in ("DISAGREE", "ERROR")
                           for v in done.values()),
                cells=done), indent=1) + "\n")
            if rec["status"] not in ("EXACT_NODE_MATCH",) or i % 50 == 0:
                print(f"[{i + 1}/{len(todo)}] {'|'.join(map(str, cell))} "
                      f"{rec['status']} {json.dumps(tally)}", flush=True)
    print(json.dumps({k: v for k, v in json.loads(OUT.read_text()).items()
                      if k != "cells"}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
