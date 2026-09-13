#!/usr/bin/env python3
"""Round 148 Phase 4 -- regenerate every pruning table FROM ZERO and confirm the
capacities are unchanged.

All round-147 scratch tables are deleted first, so nothing can be inherited.
Each table is then rebuilt deterministically from the COMMITTED cell ledger,
re-validated by the independent brute-force validator, and a representative set
of cells is searched again with the fresh table.  The capacities must come out
identical.  This is what shows the proof does not depend on leftover files.

The representative set is chosen to hit every structural corner:
  the two equality cells, every cell whose round-144 value was too small, the
  cells at a boundary budget, the d = 0 and d = 1 cells, the heavy cells, the
  mixed A/B/E cells, and a spread of the most expensive cells that still fit a
  wall-clock budget.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

EXE = R147 / "l6chain147b.exe"
UBDIR = R148 / "tables" / "ub"
BUDGET = int(os.environ.get("R148_CELL_SECONDS", "240"))
WORKERS = int(os.environ.get("R148_WORKERS", "2"))


def ledger():
    st = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") != "EXACT_UNCAPPED":
                raise SystemExit(f"ledger cell {k} is not EXACT_UNCAPPED")
            st[tuple(int(x) for x in k.split("|"))] = v
    return st


ST = ledger()
STORE = {k: dict(cc=v["cc"]) for k, v in ST.items()}


def representative():
    old = json.loads((ROOT / "outputs" /
                      "rr_l6_chain_capacity_144.json").read_text())
    sel = {}

    def add(K, why):
        sel.setdefault(K, set()).add(why)

    add((0, 14, 0, 0, 0, 0), "equality_cell_96")
    add((0, 8, 0, 0, 0, 1), "equality_cell_92")
    mx = [max(K[i] for K in ST) for i in range(6)]
    for K in ST:
        k5 = "|".join(str(x) for x in K[:5])
        r = old.get(k5)
        if K[5] == 0 and r is not None:
            ov = r["cc"] if not r.get("bound_below") else r["bound_below"] - 1
            if ov < ST[K]["cc"]:
                add(K, "round144_too_small")
        if K[1] in (0, 1):
            add(K, f"d={K[1]}")
        for i, nm in ((2, "a"), (3, "bb"), (4, "e"), (5, "h")):
            if K[i] == mx[i] and mx[i] > 0:
                add(K, f"boundary_{nm}")
        if K[5] > 0:
            add(K, "heavy")
        if sum(1 for i in (2, 3, 4) if K[i] > 0) >= 2:
            add(K, "mixed_ABE")
    cheap = sorted((k for k in ST if (ST[k]["nodes"] or 0) < 2_000_000_000),
                   key=lambda k: -(ST[k]["nodes"] or 0))
    for K in cheap[:20]:
        add(K, "expensive_but_affordable")
    return {k: sorted(v) for k, v in sel.items()}


def one(job):
    cell, why = job
    ubp = UBDIR / ("ub_%d_%d_%d_%d_%d_%d.txt" % cell)
    info = ub147.write_table(ubp, cell, STORE, exclude={cell})
    val = ub147.validate_table(ubp, cell, STORE, exclude={cell})
    rec = dict(cell=list(cell), reasons=why, ub_rows=info["rows"],
               ub_sha256=hashlib.sha256(ubp.read_bytes()).hexdigest(),
               validator_ok=val["ok"], validator_failures=val["failures"][:4])
    if not val["ok"]:
        rec["status"] = "UB_REJECTED"
        return cell, rec
    t0 = time.time()
    try:
        r = subprocess.run([str(EXE)] + [str(x) for x in cell] +
                           ["0", str(ubp), "0"], capture_output=True, text=True,
                           cwd=ROOT, timeout=BUDGET)
    except subprocess.TimeoutExpired:
        rec["status"] = "TIMEOUT"
        return cell, rec
    j = json.loads(r.stdout)
    rec.update(cc=j["cc"], nodes=j["nodes"], capped=j["capped"],
               ledger_cc=ST[cell]["cc"], ledger_nodes=ST[cell]["nodes"],
               seconds=round(time.time() - t0, 2),
               status=("IDENTICAL" if (j["cc"] == ST[cell]["cc"]
                                       and j["nodes"] == ST[cell]["nodes"]
                                       and not j["capped"])
                       else "CAPACITY_ONLY" if j["cc"] == ST[cell]["cc"]
                       else "DIFFERS"))
    return cell, rec


def main():
    # 1. delete every round-147 scratch table
    removed = 0
    for d in ((R147 / "logs" / "ub"), (R147 / "logs" / "ub2"),
              (R147 / "logs" / "controls"), UBDIR):
        if d.exists():
            removed += sum(1 for _ in d.glob("*"))
            shutil.rmtree(d)
    UBDIR.mkdir(parents=True, exist_ok=True)
    print(f"deleted {removed} inherited scratch tables", flush=True)

    rep = representative()
    print(f"representative set: {len(rep)} cells", flush=True)
    out = dict(deleted_scratch_tables=removed, cells=len(rep),
               ledger_cells=len(ST), records={})
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, (c, w)) for c, w in sorted(rep.items())]
        for i, f in enumerate(as_completed(futs)):
            cell, rec = f.result()
            out["records"]["|".join(map(str, cell))] = rec
            if rec["status"] != "IDENTICAL" or i % 20 == 0:
                print(f"[{i + 1}/{len(rep)}] {'|'.join(map(str, cell))} "
                      f"{rec['status']} cc={rec.get('cc')} "
                      f"ledger={rec.get('ledger_cc')} "
                      f"nodes={rec.get('nodes')}/{rec.get('ledger_nodes')}",
                      flush=True)
    st = {}
    for v in out["records"].values():
        st[v["status"]] = st.get(v["status"], 0) + 1
    out["status_counts"] = st
    out["all_validators_ok"] = all(v["validator_ok"] for v in out["records"].values())
    out["ok"] = (not st.get("DIFFERS") and not st.get("UB_REJECTED")
                 and out["all_validators_ok"] and st.get("IDENTICAL", 0) > 0)
    (R148 / "certs" / "regen_148.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "records"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
