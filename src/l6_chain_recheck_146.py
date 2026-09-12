#!/usr/bin/env python3
"""Round 146 (adversarial) -- SOUND recomputation of every chain-capacity cell
the length-870 / 871 closure actually leans on.

THE DEFECT.  `l6_chain_rows_144.write_ub` emitted one pruning-table line per
CACHED CELL, i.e. one line per budget split (a, bb, e), all under the key
S = a + bb + e, while the searcher consults that key with the COMBINED
remaining budget and the C loader keeps the SMALLEST value per key.  A valid
bound for a combined budget S must be the MAXIMUM over splits, so the table
handed the searcher values far below the truth (163 of 425 keys carry
split-dependent values; b=0, d=0, S=10 ranges from 20 to 50).  The searcher
over-pruned and recorded capacities BELOW the true ones -- measured on
0|0|0|0|9 (45 recorded, 50 true) and 0|0|0|0|10 (40 recorded, 55 true), and on
87 of the 377 cells with b = 0, d <= 1.

WHY IT MATTERS.  The chain capacity is used as an UPPER BOUND on the ports a
row can carry, and a row is closed when the bound is below the required port
count.  A bound that is too small closes rows that are not actually closed.
Of the coordinate rows:
    L = 869 (t=2):    0 of   85 rows need a chain bound  -> unaffected
    L = 870 (t=3):   61 of  353 rows are closed ONLY by a chain bound
    L = 871 (t=4):  552 of 1156 rows are closed ONLY by a chain bound
so the steps L6 >= 871 and L6 >= 872 are the ones in question.

THE REPAIR.  Run each consulted cell with NO pruning table at all (argv[8] =
"-").  The searcher then keeps only its table-free, analytic prune

    reach2 = ports + (unused hexagons) + (remaining combined budget)

which is sound on its own (every further port needs a fresh hexagon or one
unit of reuse budget), so the value it returns is the exact capacity of the
cell.  Nothing here consults the suspect table, and nothing here writes to the
audited round-144 ledger: results go to outputs/rr_l6_chain_recheck_146.json.

STATUS of a cell in the output: "exact" (uncapped, this is the true capacity),
or "UNKNOWN_CAP" (hit the node cap -- NOT promoted to anything).
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "outputs" / "l6chain_144.exe"
LEDGER = ROOT / "outputs" / "rr_l6_chain_capacity_144.json"
OUT = ROOT / "outputs" / "rr_l6_chain_recheck_146.json"
NODECAP = 200_000_000_000
WORKERS = int(os.environ.get("RECHECK_WORKERS", "3"))


def run_cell(cell):
    b, d, a, bb, e = cell
    t0 = time.time()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        "0", str(NODECAP), "-", "0"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return cell, dict(status="ERROR", stderr=r.stderr[:200])
    j = json.loads(r.stdout)
    return cell, dict(cc=j["cc"], nodes=j["nodes"], capped=j["capped"],
                      seconds=round(time.time() - t0, 1),
                      pruned_with_table=j["pruned"],
                      status="UNKNOWN_CAP" if j["capped"] else "exact")


def main(argv):
    cells = [tuple(c) for c in json.loads(Path(argv[0]).read_text())["cells"]]
    ledger = json.loads(LEDGER.read_text())
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [c for c in cells if "%d|%d|%d|%d|%d" % c not in done]
    # cheapest first, so coverage grows fast and a kill loses little
    todo.sort(key=lambda c: ledger.get("%d|%d|%d|%d|%d" % c, {}).get("nodes", 0))
    print(f"cells={len(cells)} already={len(done)} todo={len(todo)} "
          f"workers={WORKERS}", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        for i, (cell, rec) in enumerate(ex.map(run_cell, todo, chunksize=1)):
            key = "%d|%d|%d|%d|%d" % cell
            old = ledger.get(key, {})
            oldv = (old.get("bound_below", 0) - 1) if old.get("bound_below") else old.get("cc")
            rec["recorded_144"] = oldv
            rec["verdict"] = ("TOO_SMALL" if rec.get("cc") is not None and oldv is not None
                              and not rec["capped"] and rec["cc"] > oldv
                              else "agrees" if rec.get("cc") == oldv else rec["status"])
            done[key] = rec
            OUT.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n")
            if rec["verdict"] == "TOO_SMALL":
                print(f"TOO_SMALL {key}: recorded {oldv} < true {rec['cc']}", flush=True)
            if i % 25 == 0:
                bad = sum(1 for v in done.values() if v["verdict"] == "TOO_SMALL")
                print(f"[{i + 1}/{len(todo)}] {key} {rec['verdict']} "
                      f"too_small_so_far={bad} elapsed={time.time() - t0:.0f}s",
                      flush=True)
    bad = [k for k, v in done.items() if v["verdict"] == "TOO_SMALL"]
    cap = [k for k, v in done.items() if v["status"] == "UNKNOWN_CAP"]
    print(json.dumps(dict(cells=len(done), too_small=len(bad),
                          unknown_cap=len(cap), too_small_keys=bad[:40])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
