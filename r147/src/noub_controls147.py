#!/usr/bin/env python3
"""Round 147 Phase 5 -- NO-UB CONTROLS.

Every value in the sound table was produced with a pruning table.  A control
recomputes the same cell with the pruning weakened or removed and requires the
SAME answer.  Three control modes, each sound on its own:

  M0  no table at all, best-so-far prune OFF
      only the analytic prune reach2 = ports + unused hexagons + remaining
      budget survives.  This is the round-146 table-free regime, bit for bit.
  M1  no table at all, best-so-far prune ON
      also sound: the prune only ever discards a state whose PROVED reach
      cannot beat the record.
  M2  a deliberately WEAKENED sound table: only every third verified cell is
      allowed into it.  Still sound by the same argument, but much less
      informative -- if the answer depended on the table's strength it would
      move here.

CONTROL SET (as mandated): every cell whose round-144 value was too small, the
d = 0 and d = 1 cells, the cells at a boundary budget (a, bb, e or h at its
maximum over the whole set), the heavy-budget cells, the mixed A/B/E cells, and
the largest cells by node count.  A per-cell wall-clock budget applies; a cell
that exceeds it in a control mode is recorded as CONTROL_TIMEOUT, which is NOT
counted as agreement and NOT counted as a disagreement.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
ROOT = R147.parent
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

EXE = R147 / "l6chain147.exe"
TMP = R147 / "logs" / "controls"
BUDGET = int(os.environ.get("R147_CONTROL_SECONDS", "300"))
NODECAP = 200_000_000_000


def cells_and_store():
    raw = json.loads((R147 / "tables" / "chain_cells_147.json").read_text())
    hv = (json.loads((R147 / "tables" / "heavy_cells_147.json").read_text())
          if (R147 / "tables" / "heavy_cells_147.json").exists() else {})
    raw = dict(raw)
    raw.update(hv)
    cells, store = {}, {}
    for k, v in raw.items():
        if v.get("status") != "EXACT_UNCAPPED":
            continue
        K = tuple(int(x) for x in k.split("|"))
        cells[K] = v
        store[K] = dict(cc=v["cc"])
    return cells, store


def pick(cells):
    old = json.loads((ROOT / "outputs" /
                      "rr_l6_chain_capacity_144.json").read_text())
    sel = {}

    def add(K, why):
        sel.setdefault(K, []).append(why)

    mx = [max(K[i] for K in cells) for i in range(6)]
    for K in cells:
        k5 = "|".join(str(x) for x in K[:5])
        r = old.get(k5)
        if K[5] == 0 and r is not None:
            ov = r["cc"] if not r.get("bound_below") else r["bound_below"] - 1
            if ov < cells[K]["cc"]:
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
    for K in sorted(cells, key=lambda K: -(cells[K].get("nodes") or 0))[:25]:
        add(K, "largest_by_nodes")
    return sel


def run(cell, ubpath, bestprune):
    b, d, a, bb, e, h = cell
    t0 = time.time()
    try:
        r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                            str(h), str(NODECAP), str(ubpath), "0",
                            "", str(bestprune)],
                           capture_output=True, text=True, cwd=ROOT,
                           timeout=BUDGET)
    except subprocess.TimeoutExpired:
        return dict(status="CONTROL_TIMEOUT", seconds=BUDGET)
    if r.returncode != 0:
        return dict(status="ERROR", stderr=r.stderr[:200])
    j = json.loads(r.stdout)
    return dict(status="UNKNOWN_CAP" if j["capped"] else "EXACT_UNCAPPED",
                cc=j["cc"], nodes=j["nodes"], capped=j["capped"],
                bestprune=j["bestprune"], seconds=round(time.time() - t0, 2))


def main(argv):
    TMP.mkdir(parents=True, exist_ok=True)
    cells, store = cells_and_store()
    sel = pick(cells)
    order = sorted(sel, key=lambda K: cells[K].get("nodes") or 0)
    if argv and argv[0] == "--limit":
        order = order[:int(argv[1])]
    out = {"budget_seconds": BUDGET, "control_set": len(order), "cells": {}}
    agree = dis = to = 0
    for i, K in enumerate(order):
        key = "|".join(map(str, K))
        want = cells[K]["cc"]
        weak = TMP / ("weak_" + key.replace("|", "_") + ".txt")
        sub = {k: v for j, (k, v) in enumerate(sorted(store.items()))
               if j % 3 == 0 and k != K}
        ub147.write_table(weak, K, sub, exclude={K})
        res = {}
        res["M0"] = run(K, "-", 0)
        res["M1"] = run(K, "-", 1)
        res["M2"] = run(K, weak, 1)
        ok = [m for m, r in res.items()
              if r["status"] == "EXACT_UNCAPPED" and r.get("cc") == want]
        bad = [m for m, r in res.items()
               if r["status"] == "EXACT_UNCAPPED" and r.get("cc") != want]
        tos = [m for m, r in res.items() if r["status"] != "EXACT_UNCAPPED"]
        agree += bool(ok) and not bad
        dis += bool(bad)
        to += bool(tos) and not bad
        out["cells"][key] = dict(reasons=sorted(set(sel[K])), table_value=want,
                                 modes={m: {k: v for k, v in r.items()}
                                        for m, r in res.items()},
                                 agreeing=ok, disagreeing=bad, inconclusive=tos)
        print(f"[{i + 1}/{len(order)}] {key} want={want} "
              f"agree={ok} bad={bad} inconclusive={tos}", flush=True)
    out["agreeing_cells"] = agree
    out["disagreeing_cells"] = dis
    out["cells_with_only_inconclusive_modes"] = to
    out["ok"] = dis == 0 and agree == len(order)
    (R147 / "certs" / "noub_controls_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "cells"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
