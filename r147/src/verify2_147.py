#!/usr/bin/env python3
"""Round 147 Phase 6 -- verify the load-bearing cells with the SECOND
implementation (r147/src/chain2_147.c).

Both implementations get the SAME per-cell sound pruning table -- a sound bound
is sound for any search -- but they differ in geometry provenance (B reads the
independent string-algebra reconstruction), state representation (per-permutation
`used[]` plus hexagon/orbit counts vs per-orbit phase masks plus hexagon flags),
control flow (explicit stack vs recursion) and move order (reversed).  With the
best-so-far prune on, a different move order finds the record at a different
moment, so NODE COUNTS ARE EXPECTED TO DIFFER; the capacity must agree exactly.

A second mode runs both with NO table and the best-so-far prune OFF, where the
visited state set is order-independent, so there the node counts must agree too.
That mode is only used on cells cheap enough for it.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
ROOT = R147.parent
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

A = R147 / "l6chain147.exe"
B = R147 / "chain2_147.exe"
OUT = R147 / "certs" / "second_impl_147.json"
TMP = Path(os.environ.get("R147_TMP", str(R147 / "logs" / "ub2")))
# ROUND 148: the round-147 default lives under r147/logs, which round 148
# Phase 4 deliberately DELETES to prove the proof survives losing its
# scratch.  Those two collided once (the running B job lost its table
# mid-search and died with FileNotFoundError), so the directory is now
# settable and round 148 points it outside the deletion target.
WORKERS = int(os.environ.get("R147_WORKERS", "3"))
PER_CELL = int(os.environ.get("R147_B_SECONDS", "1800"))
EXACT_NODE_BUDGET = int(os.environ.get("R147_EXACT_NODES", "20000000"))


def store():
    out = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        p = R147 / "tables" / f
        if p.exists():
            for k, v in json.loads(p.read_text()).items():
                if v.get("status") == "EXACT_UNCAPPED":
                    out[tuple(int(x) for x in k.split("|"))] = dict(cc=v["cc"],
                                                                    nodes=v["nodes"])
    return out


ST = store()


def one(cell):
    want = ST[cell]["cc"]
    a = [str(x) for x in cell]
    ubp = TMP / ("ub_%d_%d_%d_%d_%d_%d.txt" % cell)
    ub147.write_table(ubp, cell, {k: v for k, v in ST.items() if k != cell},
                      exclude={cell})
    rec = dict(cell=list(cell), table_value=want)
    t0 = time.time()
    try:
        r = subprocess.run([str(B)] + a + ["0", str(ubp)], capture_output=True,
                           text=True, cwd=ROOT, timeout=PER_CELL)
    except subprocess.TimeoutExpired:
        rec["status"] = "B_TIMEOUT"
        rec["seconds"] = PER_CELL
        return cell, rec
    if r.returncode != 0:
        rec["status"] = "B_ERROR"
        rec["stderr"] = r.stderr[:200]
        return cell, rec
    j = json.loads(r.stdout)
    rec.update(B_cc=j["cc"], B_nodes=j["nodes"], B_capped=j["capped"],
               seconds=round(time.time() - t0, 2),
               status="AGREES" if (j["cc"] == want and not j["capped"])
               else "DISAGREES")
    # the strict node-count mode, only where it is affordable
    if (ST[cell]["nodes"] or 0) <= EXACT_NODE_BUDGET:
        try:
            ra = json.loads(subprocess.run(
                [str(A)] + a + ["0", "-", "0", "", "0"], capture_output=True,
                text=True, cwd=ROOT, timeout=PER_CELL).stdout)
            rb = json.loads(subprocess.run(
                [str(B)] + a + ["0", "-", "0"], capture_output=True,
                text=True, cwd=ROOT, timeout=PER_CELL).stdout)
            rec["notable_A"] = dict(cc=ra["cc"], nodes=ra["nodes"])
            rec["notable_B"] = dict(cc=rb["cc"], nodes=rb["nodes"])
            rec["notable_nodes_identical"] = (ra["nodes"] == rb["nodes"]
                                              and ra["cc"] == rb["cc"] == want)
        except Exception as e:
            rec["notable_error"] = repr(e)[:120]
    return cell, rec


def main(argv):
    TMP.mkdir(parents=True, exist_ok=True)
    cells = [tuple(c) for c in
             json.loads((R147 / "tables" /
                         "loadbearing_cells_147.json").read_text())["cells"]]
    cells = [c for c in cells if c in ST]
    done = json.loads(OUT.read_text())["cells"] if OUT.exists() else {}
    todo = [c for c in cells
            if "|".join(map(str, c)) not in done
            or done["|".join(map(str, c))].get("status") != "AGREES"]
    todo.sort(key=lambda c: ST[c]["nodes"] or 0)
    print(f"load-bearing cells={len(cells)} todo={len(todo)} workers={WORKERS} "
          f"per-cell budget={PER_CELL}s", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, c) for c in todo]
        for i, f in enumerate(as_completed(futs)):
            cell, rec = f.result()
            done["|".join(map(str, cell))] = rec
            agree = sum(1 for v in done.values() if v["status"] == "AGREES")
            dis = [k for k, v in done.items() if v["status"] == "DISAGREES"]
            nid = sum(1 for v in done.values() if v.get("notable_nodes_identical"))
            OUT.write_text(json.dumps(dict(
                cells_total=len(cells), verified=len(done), agreeing=agree,
                disagreeing=dis,
                identical_node_counts_no_table=nid,
                timeouts=[k for k, v in done.items()
                          if v["status"] == "B_TIMEOUT"],
                ok=(agree == len(cells) and not dis),
                cells=done), indent=1) + "\n")
            if rec["status"] != "AGREES" or i % 25 == 0:
                print(f"[{i + 1}/{len(todo)}] {'|'.join(map(str, cell))} "
                      f"{rec['status']} want={rec['table_value']} "
                      f"B={rec.get('B_cc')} nodes={rec.get('B_nodes')} "
                      f"agree={agree} dis={len(dis)} nodeid={nid} "
                      f"t={time.time() - t0:.0f}s", flush=True)
    print(json.dumps({k: v for k, v in json.loads(OUT.read_text()).items()
                      if k != "cells"}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
