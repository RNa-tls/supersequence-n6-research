#!/usr/bin/env python3
"""Round 147 Phase 6 (strict mode) -- where the two implementations must agree
on the NODE COUNT as well as the capacity.

With no pruning table and the best-so-far prune off, the set of states a DFS
visits does not depend on the order the moves are generated in, so the two
implementations must visit exactly the same number of nodes.  That is a much
sharper agreement test than equal capacities, and it is run on every
load-bearing cell cheap enough to afford it with no table at all.

(The main pass in r147/src/verify2_147.py could not run this mode: it invoked
the phase-2 binary, whose witness-argument gate treated the empty witness path
as a request for witness mode.  The rebuilt binary r147/l6chain147b.exe fixes
only that gate -- it reproduces phase-2 cells with identical node counts,
r147/certs/binaries_147.json.)
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
ROOT = R147.parent
A = R147 / "l6chain147b.exe"
B = R147 / "chain2_147.exe"
OUT = R147 / "certs" / "nodeid_147.json"
BUDGET = int(os.environ.get("R147_NODEID_SECONDS", "600"))
MAXN = int(os.environ.get("R147_NODEID_MAXNODES", "60000000"))
WORKERS = int(os.environ.get("R147_WORKERS", "3"))


def store():
    out = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        p = R147 / "tables" / f
        if p.exists():
            for k, v in json.loads(p.read_text()).items():
                if v.get("status") == "EXACT_UNCAPPED":
                    out[tuple(int(x) for x in k.split("|"))] = v
    return out


ST = store()


def one(cell):
    a = [str(x) for x in cell]
    t0 = time.time()
    try:
        ra = json.loads(subprocess.run([str(A)] + a + ["0", "-", "0", "-", "0"],
                                       capture_output=True, text=True,
                                       cwd=ROOT, timeout=BUDGET).stdout)
        rb = json.loads(subprocess.run([str(B)] + a + ["0", "-", "0"],
                                       capture_output=True, text=True,
                                       cwd=ROOT, timeout=BUDGET).stdout)
    except subprocess.TimeoutExpired:
        return cell, dict(status="TIMEOUT", seconds=BUDGET)
    except Exception as e:
        return cell, dict(status="ERROR", error=repr(e)[:150])
    want = ST[cell]["cc"]
    ok = (ra["cc"] == rb["cc"] == want and ra["nodes"] == rb["nodes"]
          and not ra["capped"] and not rb["capped"])
    return cell, dict(status="IDENTICAL" if ok else "DIFFERS",
                      table_value=want, A=dict(cc=ra["cc"], nodes=ra["nodes"]),
                      B=dict(cc=rb["cc"], nodes=rb["nodes"]),
                      seconds=round(time.time() - t0, 2))


def main():
    cells = [tuple(c) for c in json.loads(
        (R147 / "tables" / "loadbearing_cells_147.json").read_text())["cells"]]
    cells = [c for c in cells if c in ST and (ST[c]["nodes"] or 0) <= MAXN]
    cells.sort(key=lambda c: ST[c]["nodes"] or 0)
    print(f"cells affordable with no table at all: {len(cells)} "
          f"(node ceiling {MAXN})", flush=True)
    done = {}
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, c) for c in cells]
        for i, f in enumerate(as_completed(futs)):
            cell, rec = f.result()
            done["|".join(map(str, cell))] = rec
            if rec["status"] != "IDENTICAL" or i % 50 == 0:
                print(f"[{i + 1}/{len(cells)}] {'|'.join(map(str, cell))} "
                      f"{rec['status']} {json.dumps(rec.get('A'))} "
                      f"{json.dumps(rec.get('B'))}", flush=True)
    ident = sum(1 for v in done.values() if v["status"] == "IDENTICAL")
    diff = [k for k, v in done.items() if v["status"] == "DIFFERS"]
    out = dict(cells=len(done), identical=ident, differing=diff,
               timeouts=[k for k, v in done.items() if v["status"] == "TIMEOUT"],
               errors=[k for k, v in done.items() if v["status"] == "ERROR"],
               ok=not diff, detail=done)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
