#!/usr/bin/env python3
"""Round 147 Phase 2 -- recompute every load-bearing chain cell SOUNDLY.

For each cell, in an order that never uses a cell before it is verified:
  1. build a full-budget-key pruning table from the cells already verified
     (r147/src/ub147.py), excluding the cell itself;
  2. validate that table independently, by brute force, against the raw
     per-cell data, and refuse to run if anything is off;
  3. run the round-147 searcher with it;
  4. accept the result only if the run ended UNCAPPED, in which case the value
     is the exact capacity of the cell and the cell joins the verified store.

Every record carries: arguments, result, node count, cap status, the
implementation, the source and executable hashes, the elapsed time, the number
of table rows used and the table's validation summary.
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147 = ROOT / "r147"
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

EXE = R147 / "l6chain147.exe"
SRC = R147 / "src" / "l6_chain_capacity_147.c"
OUT = R147 / "tables" / os.environ.get("R147_OUT", "chain_cells_147.json")
# extra already-verified stores to seed the pruning table from (the heavy pass
# is pruned with the plain chain cells as well as with heavy ones)
SEEDS = [R147 / "tables" / f for f in
         os.environ.get("R147_SEEDS", "").split(",") if f]
LOG = R147 / "logs" / "recompute147.log"
NODECAP = int(os.environ.get("R147_NODECAP", "80000000000"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC_SHA, EXE_SHA = sha(SRC), sha(EXE)


def store_from(recs):
    """The verified store in the shape ub147.load_verified returns."""
    out = {}
    for k, v in recs.items():
        if v.get("status") != "EXACT_UNCAPPED":
            continue
        key = tuple(int(x) for x in k.split("|"))
        out[key] = dict(cc=v["cc"], nodes=v.get("nodes"),
                        impl=v.get("impl"), provenance=v.get("provenance"))
    return out


def run_one(cell, store, tmpdir, validate=True):
    b, d, a, bb, e, h = cell
    ubp = Path(tmpdir) / ("ub_%d_%d_%d_%d_%d_%d.txt" % cell)
    info = ub147.write_table(ubp, cell, store, exclude={cell})
    val = (ub147.validate_table(ubp, cell, store, exclude={cell})
           if validate else dict(ok=True, skipped=True))
    if not val["ok"]:
        return dict(status="UB_TABLE_REJECTED", ub=info, ub_validation=val)
    t0 = time.time()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        str(h), str(NODECAP), str(ubp), "0"],
                       capture_output=True, text=True, cwd=ROOT)
    el = round(time.time() - t0, 2)
    if r.returncode != 0:
        return dict(status="ERROR", returncode=r.returncode,
                    stderr=r.stderr[:300], seconds=el, ub=info,
                    ub_validation=val)
    j = json.loads(r.stdout)
    rec = dict(args=[b, d, a, bb, e, h], cc=j["cc"], nodes=j["nodes"],
               capped=j["capped"], bestprune=j["bestprune"],
               pruned_with_table=j["pruned"], seconds=el, impl="C147",
               src_sha256=SRC_SHA, exe_sha256=EXE_SHA,
               ub_rows=info["rows"], ub_verified_used=info["verified_used"],
               ub_validation_ok=val["ok"], node_cap=NODECAP,
               status="UNKNOWN_CAP" if j["capped"] else "EXACT_UNCAPPED")
    return rec


def main(argv):
    cells = [tuple(c) + (0,) if len(c) == 5 else tuple(c)
             for c in json.loads(Path(argv[0]).read_text())["cells"]]
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    tmpdir = R147 / "logs" / "ub"
    tmpdir.mkdir(parents=True, exist_ok=True)
    # cheapest-looking first within a sound order: b, then deficit budget, then
    # total reuse budget, then heavy budget.  A cell is only ever pruned with
    # cells that come strictly earlier in this order (plus any already done).
    cells.sort(key=lambda c: (c[0], c[1], c[2] + c[3] + c[4], c[5]))
    log = LOG.open("a")
    t0 = time.time()
    for i, cell in enumerate(cells):
        key = "|".join(map(str, cell))
        if key in done and done[key].get("status") == "EXACT_UNCAPPED":
            continue
        store = store_from(done)
        for sp in SEEDS:
            if sp.exists():
                for k, v in store_from(json.loads(sp.read_text())).items():
                    store.setdefault(k, v)
        rec = run_one(cell, store, tmpdir)
        rec["provenance"] = "r147 phase2"
        done[key] = rec
        OUT.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n")
        line = (f"[{i + 1}/{len(cells)}] {key} {rec['status']} "
                f"cc={rec.get('cc')} nodes={rec.get('nodes')} "
                f"ubrows={rec.get('ub_rows')} used={rec.get('ub_verified_used')} "
                f"{rec.get('seconds')}s total={time.time() - t0:.0f}s")
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()
        if rec["status"] not in ("EXACT_UNCAPPED",):
            print("  !! " + json.dumps({k: v for k, v in rec.items()
                                        if k not in ("ub",)})[:400], flush=True)
    st = {}
    for v in done.values():
        st[v["status"]] = st.get(v["status"], 0) + 1
    print(json.dumps(dict(cells=len(done), status=st)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
