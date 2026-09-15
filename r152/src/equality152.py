#!/usr/bin/env python3
"""Round 152 -- provenance of the two L = 871 equality rows.

They are the only rows the capacity argument does not strictly close, so what
they rest on has to be nailed down:

  1. which rows the round-152 certified-only census leaves standing;
  2. that they are the SAME two rows round 147 and round 148 found;
  3. which capacity cell each one's bound comes from, and that those cells are
     EXACT_CERTIFIED -- witness replayed and C+1 exhausted -- in this round;
  4. that the explicit exhaustion tree covers those cells too;
  5. that the round-148 exhaustive witness enumeration was run on the same
     cells at the same targets (recorded, not re-run: excluding the witnesses
     is the coexistence layer, which is not a capacity claim).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R152 = ROOT / "r152"
COORD = ("k", "Z", "H", "Bstar", "G", "g", "c", "d", "D2", "Qs", "h")


def jload(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def main():
    out = {}
    cen = jload(R152 / "certs" / "census_152.json")
    eq = [r for L, v in cen["layers"].items() for r in v["non_strict"]
          if r["verdict"] == "EQUALITY" and L == "L871"]
    out["census_equality_rows"] = eq
    out["census_surviving_rows"] = [r for L, v in cen["layers"].items()
                                    for r in v["non_strict"]
                                    if r["verdict"] == "SURVIVING"]

    # round 147's independently produced survivor list
    r147 = jload(ROOT / "r147" / "rows" / "rows_eval_147.json")
    old = [{k: r[k] for k in COORD} | {"required": r["required"]}
           for r in r147["L871_survivors"]]
    new = [{k: r[k] for k in COORD} | {"required": r["required"]} for r in eq]
    out["same_rows_as_round147"] = sorted(map(json.dumps, old, )) == \
        sorted(map(json.dumps, new))
    out["round147_survivors"] = old

    # the cells each equality row rests on, from the row coordinates
    #   deficit budget 5k - G, tokens B* - s = 0, a <= D2, bb <= Qs,
    #   e <= max(0, Z - Qs), h = H
    cells = []
    for r in eq:
        cell = (r["Bstar"], 5 * r["k"] - r["G"], min(r["D2"], 2 * r["g"]),
                min(r["Qs"], 2 * r["g"]),
                min(max(0, r["Z"] - r["Qs"]), 2 * r["g"]), r["H"])
        cells.append(dict(row={k: r[k] for k in COORD},
                          required=r["required"],
                          cell="|".join(map(str, cell)),
                          bounds=r["bounds"]))
    out["cells"] = cells

    chain = {r["cell"]: r for r in jload(R152 / "certs" / "verify_all_c152.json")["rows"]}
    for c in cells:
        row = chain.get(c["cell"])
        c["certified"] = row and row["status"]
        c["certified_cap"] = row and row["cap"]
        c["nodes"] = row and row.get("nodes")
        c["cap_equals_required"] = bool(row) and row["cap"] == c["required"]
    out["all_cells_exact"] = all(c["certified"] == "EXACT_CERTIFIED"
                                 and c["cap_equals_required"] for c in cells)

    tree = jload(R152 / "certs" / "extree_pilot_152.json") or {"rows": []}
    treecells = {r["cell"]: r for r in tree["rows"]}
    for c in cells:
        t = treecells.get(c["cell"])
        c["explicit_tree"] = t and t["status"]
        c["explicit_tree_nodes"] = t and t["nodes"]
    out["all_cells_have_an_explicit_tree"] = all(
        c["explicit_tree"] == "EXACT_CERTIFIED" for c in cells)

    w148 = jload(ROOT / "r148" / "certs" / "witnesses_148.json") or {"rows": []}
    out["round148_witness_enumeration"] = [
        dict(name=r["name"], cell="|".join(map(str, r["cell"])),
             target=r["target"], status=r["route_table"]["status"],
             capped=r["route_table"]["capped"],
             witnesses=r["route_table"]["witnesses"],
             routes_agree=r["routes_agree"], all_excluded=r["all_excluded"])
        for r in w148["rows"]]
    seen = {x["cell"] + "@" + str(x["target"])
            for x in out["round148_witness_enumeration"]}
    out["round148_covers_the_same_cells"] = all(
        c["cell"] + "@" + str(c["required"]) in seen for c in cells)

    out["ok"] = (out["all_cells_exact"]
                 and out["all_cells_have_an_explicit_tree"]
                 and out["same_rows_as_round147"]
                 and out["round148_covers_the_same_cells"]
                 and not out["census_surviving_rows"])
    (R152 / "certs" / "equality_152.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
