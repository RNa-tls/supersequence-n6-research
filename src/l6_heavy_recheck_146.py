#!/usr/bin/env python3
"""Round 146 -- sound (table-free) recheck of the HEAVY chain cells.

Same defect, same repair as src/l6_chain_recheck_146.py: the merged-chain model
reads `outputs/rr_l6_heavychain_capacity_144.json`, whose cells were produced
with the invalid pruning table, so each one has to be recomputed with no table
at all (argv[8] = "-", leaving only the sound analytic prune).

Of the 276 heavy cells the merged model would consult, 42 exist; the rest were
never computed, and for those the model simply contributes nothing to the
minimum.  So these 42 are exactly the heavy cells the closure can lean on.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "outputs" / "l6chain_144.exe"
LEDGER = ROOT / "outputs" / "rr_l6_heavychain_capacity_144.json"
OUT = ROOT / "outputs" / "rr_l6_heavy_recheck_146.json"
NODECAP = 200_000_000_000
WORKERS = int(os.environ.get("RECHECK_WORKERS", "3"))


def run_cell(job):
    cell, target = job
    b, d, a, bb, e, h = cell
    t0 = time.time()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        str(h), str(NODECAP), "-", str(target)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return cell, dict(status="ERROR", returncode=r.returncode,
                          stderr=r.stderr[:200])
    j = json.loads(r.stdout)
    return cell, dict(cc=j["cc"], nodes=j["nodes"], capped=j["capped"],
                      seconds=round(time.time() - t0, 1), target=target,
                      pruned_with_table=j["pruned"],
                      status=("UNKNOWN_CAP" if j["capped"]
                              else "exact" if not target
                              else "bound_below" if j["cc"] < target
                              else "target_reached"))


def main():
    ledger = json.loads(LEDGER.read_text())
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    jobs = [(tuple(int(x) for x in k.split("|")), v.get("bound_below", 0))
            for k, v in ledger.items() if k not in done]
    jobs.sort(key=lambda j: ledger["|".join(map(str, j[0]))].get("nodes", 0))
    print(f"heavy cells={len(ledger)} todo={len(jobs)} workers={WORKERS}", flush=True)
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_cell, j) for j in jobs]
        for i, fut in enumerate(as_completed(futs)):
            cell, rec = fut.result()
            key = "|".join(map(str, cell))
            old = ledger.get(key, {})
            oldv = (old.get("bound_below", 0) - 1) if old.get("bound_below") else old.get("cc")
            rec["recorded_144"] = oldv
            if rec["status"] == "ERROR" or rec.get("capped"):
                rec["verdict"] = rec["status"] if rec["status"] == "ERROR" else "UNKNOWN_CAP"
            elif rec["status"] == "target_reached":
                rec["verdict"] = "TOO_SMALL"
            elif rec["status"] == "bound_below":
                rec["verdict"] = "agrees"
            elif oldv is not None and rec["cc"] > oldv:
                rec["verdict"] = "TOO_SMALL"
            elif rec["cc"] == oldv:
                rec["verdict"] = "agrees"
            else:
                rec["verdict"] = "smaller_than_recorded"
            done[key] = rec
            OUT.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n")
            print(f"[{i + 1}/{len(jobs)}] {key} {rec['verdict']} "
                  f"recorded={oldv} now={rec.get('cc')}", flush=True)
    bad = [k for k, v in done.items() if v["verdict"] == "TOO_SMALL"]
    print(json.dumps(dict(cells=len(done), too_small=len(bad), keys=bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
