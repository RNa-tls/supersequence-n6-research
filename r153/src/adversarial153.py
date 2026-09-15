#!/usr/bin/env python3
"""Round 153 Phase 12 -- the adversarial trace.

Assume a cover of length <= 871 exists and follow it until something breaks.

  step 1  Round 152.  Its certified-only census closes every coordinate row at
          L <= 870 strictly, and 1,154 of the 1,156 rows at L = 871.  So the
          cover realises E1 or E2.
  step 2  For that row the certified capacity EQUALS the required port count,
          so the induced chain attains the capacity exactly.
  step 3  Round 153.  Every capacity-attaining walk was enumerated, five ways,
          with identical raw and canonical sets.  The cover's chain is one of
          them (up to a relabelling of the six letters, which is a symmetry of
          the whole catalogue).
  step 4  For that witness the row's incidence bound is tight, so the chain is
          hexagon-simple and the c deleted pure circuits must cover the
          |F| = 4c unused hexagons.
  step 5  No c tau-orbits cover F.  Contradiction.

This file re-derives steps 2, 4 and 5 from the artefacts, and then tries to
BUILD an escaping object: it searches for any family of at most c orbits that
covers F, and reports the smallest family that does cover it.  If such a family
of size <= c were found the theorem would be refuted; the smallest one found is
larger than c, and the gap is reported.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r153" / "src"))
sys.path.insert(0, str(ROOT / "r152" / "src"))
import coexist153 as CO                                             # noqa: E402
from checker152 import HEX, ORB                                     # noqa: E402

ROWS = [("E1", "r153/certs/E1_table.jsonl", (0, 14, 0, 0, 0, 0), 96, 6,
         dict(k=4, Z=0, H=0, Bstar=0, G=6, g=0, c=6, d=0, D2=0, Qs=0, h=0)),
        ("E2", "r153/certs/E2_table.jsonl", (0, 8, 0, 0, 0, 1), 92, 7,
         dict(k=3, Z=0, H=1, Bstar=0, G=7, g=0, c=7, d=0, D2=0, Qs=0, h=1))]


def main():
    cen = json.loads((ROOT / "r152" / "certs" / "census_152.json").read_text())
    cap = {r["cell"]: r for r in json.loads(
        (ROOT / "r152" / "certs" / "verify_all_c152.json").read_text())["rows"]}
    out = dict(step1=dict(
        source="r152/certs/census_152.json",
        layers={L: v["tally"] for L, v in cen["layers"].items()},
        survivors_at_871=[r for r in cen["layers"]["L871"]["non_strict"]],
        every_row_below_871_strictly_closed=all(
            set(v["tally"]) == {"STRICTLY_CLOSED"}
            for L, v in cen["layers"].items() if L != "L871"),
        only_two_rows_left_at_871=(
            cen["layers"]["L871"]["tally"].get("EQUALITY") == 2
            and cen["layers"]["L871"]["tally"].get("SURVIVING", 0) == 0)),
        rows=[])

    for name, path, cell, target, c, coords in ROWS:
        key = "|".join(map(str, cell))
        wits = [json.loads(x) for x in (ROOT / path).read_text().splitlines()
                if x.strip()]
        entry = dict(name=name, row=coords, cell=key, target=target, circuits=c,
                     step2=dict(certified_cap=cap[key]["cap"],
                                status=cap[key]["status"],
                                required=target,
                                capacity_equals_required=cap[key]["cap"] == target,
                                deficit_budget=cell[1],
                                D_sum_from_row=5 * coords["k"] - coords["G"],
                                deficit_budget_matches_row=(
                                    cell[1] == 5 * coords["k"] - coords["G"])),
                     step3=dict(witnesses=len(wits)),
                     step4=[], step5=[])
        for i, w in enumerate(wits):
            ports = w["ports"]
            Hc = {HEX[v] for v in ports}
            F = sorted(set(range(120)) - Hc)
            entry["step4"].append(dict(
                index=i, ports=len(ports), hexagons=len(Hc),
                hex_simple=len(Hc) == len(ports),
                F_size=len(F), four_c=4 * c, F_equals_4c=len(F) == 4 * c,
                chain_orbits=len({ORB[v] for v in ports})))
            inst = CO.instance(ports, c, False)
            escape = CO.solve_dfs_lowest(inst, c)
            mc = CO.min_cover(inst)
            cnt = CO.counting_bound(inst)
            entry["step5"].append(dict(
                index=i,
                escaping_family_of_size_at_most_c=escape["coverable"],
                search_nodes=escape["nodes"],
                smallest_family_that_covers_F=mc["min_orbits"],
                gap_over_c=None if mc["min_orbits"] is None
                else mc["min_orbits"] - c,
                example_of_a_covering_family=mc.get("solution"),
                counting_bound=cnt,
                contradiction=(f"|F| = {len(F)} = 4c must be covered by c = {c} "
                               f"tau-orbits, but the smallest family of orbits "
                               f"covering F has "
                               f"{mc['min_orbits']} members")))
        entry["refuted"] = any(s["escaping_family_of_size_at_most_c"]
                               for s in entry["step5"])
        out["rows"].append(entry)

    out["any_escaping_object"] = any(r["refuted"] for r in out["rows"])
    out["ok"] = (out["step1"]["every_row_below_871_strictly_closed"]
                 and out["step1"]["only_two_rows_left_at_871"]
                 and not out["any_escaping_object"]
                 and all(r["step2"]["capacity_equals_required"]
                         and r["step2"]["deficit_budget_matches_row"]
                         for r in out["rows"])
                 and all(s["hex_simple"] and s["F_equals_4c"]
                         for r in out["rows"] for s in r["step4"]))
    (ROOT / "r153" / "certs" / "adversarial_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["step1"]["layers"], indent=1))
    for r in out["rows"]:
        print(f"  {r['name']} cell={r['cell']} cap={r['step2']['certified_cap']}"
              f" required={r['step2']['required']} "
              f"deficit budget {r['step2']['deficit_budget']} = 5k-G="
              f"{r['step2']['D_sum_from_row']}")
        for s4, s5 in zip(r["step4"], r["step5"]):
            print(f"    witness #{s4['index']}: hex_simple={s4['hex_simple']} "
                  f"|F|={s4['F_size']}=4c={s4['four_c']} -> escaping family "
                  f"of size <= {r['circuits']}: "
                  f"{s5['escaping_family_of_size_at_most_c']} "
                  f"(search {s5['search_nodes']} nodes); smallest covering "
                  f"family has {s5['smallest_family_that_covers_F']} orbits, "
                  f"gap +{s5['gap_over_c']}")
    print("any escaping object:", out["any_escaping_object"], " ok:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
