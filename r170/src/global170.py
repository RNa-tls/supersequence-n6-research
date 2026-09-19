#!/usr/bin/env python3
"""Round 170 -- the global cost, with measured and modelled kept apart.

Every earlier forecast in this project quoted one number.  Round 167 said
82.8 billion nodes remained, round 169 said 78.5 billion, and both came from
running one cost model over every uncertified cell.  Round 170 measured two of
those cells at a census-safe bound and got 8,099,282 and 218 -- four orders of
magnitude apart, from the same model, the same lemma and the same fallback.
A single point estimate over the other thirty-three would be arithmetic
performed on an unknown.

So the total is reported in four separate registers and never summed into one
headline:

  MEASURED      a genuine certificate exists and its proof nodes were counted
                by the generator and both verifiers;
  LOWER BOUND   a capped run did not finish, so the true cost is strictly
                greater than the cap.  This is knowledge, not an estimate;
  MODELLED      no run exists; round 152's table-dependent node count is the
                only figure available, and it is quoted AS a round-152 figure,
                not as a prediction of the table-free cost;
  UNKNOWN       neither measured nor modelled.

Verification cost is counted separately from generation, because verifier A
and verifier B each replay every proof node: dual verification roughly triples
the node budget and that has never been in a forecast in this project.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def main():
    rows152 = json.loads((ROOT / "r152" / "certs"
                          / "verify_all_c152.json").read_text())["rows"]
    N152 = {parse(r["cell"]): r["nodes"] for r in rows152
            if r["status"] in GOOD}
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = sorted(set([parse(c) for c in src["minimum"]["cells"]]
                       + [parse(c) for c in
                          bas["minimum"]["witness_completion"]]))
    recl = json.loads((ROOT / "r170" / "certs" / "reclass_170.json").read_text())
    sched = json.loads((ROOT / "r170" / "certs"
                        / "schedule_170.json").read_text())
    rate = sched["measured_throughput"]["used_for_schedule"]

    # ---- measured: the four r170 artifacts
    measured = {}
    for gen, ver_a, ver_b, label in (
        ("generation_ladder_h_170", "verification_a_h_170",
         "verification_b_h_170", "H ladder (12 rungs)"),
        ("generation_ladder_a2_170", "verification_a_a2_170",
         "verification_b_a2_170", "A2 ladder (16 rungs)"),
        (None, "verification_a_targeth_170", "verification_b_targeth_170",
         "H target 0|15|0|0|0|1 <= 115"),
        (None, "verification_a_targeta2_170", "verification_b_targeta2_170",
         "A2 target 0|18|2|0|0|0 <= 117"),
    ):
        a = json.loads((ROOT / "r170" / "certs" / f"{ver_a}.json").read_text())
        b = json.loads((ROOT / "r170" / "certs" / f"{ver_b}.json").read_text())
        g = (json.loads((ROOT / "r170" / "certs" / f"{gen}.json").read_text())
             if gen else None)
        measured[label] = dict(
            proof_nodes=a["total_nodes"],
            generation_search_nodes=g["total_search_nodes"] if g else None,
            verifier_a_nodes=a["total_nodes"],
            verifier_b_nodes=b["total_proof_nodes"],
            three_way_identical=(a["total_nodes"] == b["total_proof_nodes"]
                                 and (g is None
                                      or g["total_proof_nodes"]
                                      == a["total_nodes"])),
            stored_bytes=(g["stored_bytes"] if g else None))
    for label, rel in (("H target 0|15|0|0|0|1 <= 115",
                        "genuine_target_h_170"),
                       ("A2 target 0|18|2|0|0|0 <= 117",
                        "genuine_target_a2_170")):
        r = json.loads((ROOT / "r170" / "certs" / f"{rel}.json").read_text())
        measured[label]["generation_search_nodes"] = r["search_nodes"]
        measured[label]["stored_bytes"] = r.get("stored_bytes")

    meas_proof = sum(v["proof_nodes"] for v in measured.values())
    meas_gen = sum(v["generation_search_nodes"] or 0
                   for v in measured.values())
    meas_bytes = sum(v["stored_bytes"] or 0 for v in measured.values())

    # ---- the cheapest measured route, over EVERY report that built one.
    # Reading a single report was wrong: the H minimum came from the sweep's
    # prefix family, not from the structurally-predicted subsets, and quoting
    # only the latter understated the saving.  Both are scanned and the
    # schemas normalised, since the two modules name their fields differently.
    def scan_best(*rels):
        cands = []
        for rel in rels:
            p = ROOT / "r170" / "certs" / rel
            if not p.exists():
                continue
            r = json.loads(p.read_text())
            for v in r.get("variants", []):
                if v.get("completed") and v.get("total_nodes"):
                    cands.append(dict(
                        source=rel, variant=v["variant"],
                        rungs=v.get("rungs_n", v.get("rungs_kept_n")),
                        investment=v["ladder_investment"],
                        target=v["proof_nodes"], total=v["total_nodes"]))
        cands.sort(key=lambda c: c["total"])
        return cands

    hcand = scan_best("sweep_h_170.json", "predicted_h_170.json")
    acand = scan_best("sweep_a2_170.json")
    cheapest = {}
    if hcand:
        cheapest["H"] = hcand[0]
        cheapest["H"]["basin_within_10_percent"] = [
            c["variant"] for c in hcand if c["total"] <= hcand[0]["total"] * 1.1]
    if acand:
        cheapest["A2"] = acand[0]
        cheapest["A2"]["basin_within_10_percent"] = [
            c["variant"] for c in acand if c["total"] <= acand[0]["total"] * 1.1]

    # ---- lower bounds from capped runs
    sub = json.loads((ROOT / "r170" / "certs"
                      / "subset_h_170.json").read_text())
    ctl = [v for v in sub["variants"] if v["variant"] == "no_ladder"][0]
    cf = [json.loads(l) for l in (ROOT / "r170" / "certs"
                                  / "counterfactual_170.json").read_text()
          .splitlines() if l.strip().startswith("{")]
    lower = [dict(what="H target at S=115 with NO ladder",
                  strictly_greater_than=ctl["search_nodes"],
                  evidence="capped run did not finish"),
             dict(what="A2 target at S=117 with NO ladder",
                  strictly_greater_than=20000001,
                  evidence="capped run did not finish")]

    # ---- modelled / unknown: the 33 basis cells with no measurement
    todo = [parse(c) for c in recl["basis_cells_still_to_certify"]]
    modelled, unknown = [], []
    for K in sorted(todo, key=cellstr):
        n = N152.get(K)
        if n:
            modelled.append(dict(cell=cellstr(K), round_152_nodes=n))
        else:
            unknown.append(cellstr(K))
    modelled_total = sum(r["round_152_nodes"] for r in modelled)

    out = dict(
        registers_are_separate="measured, lower-bounded, modelled and unknown "
                               "are never added together; a single total would "
                               "hide that 33 of 35 basis cells have no "
                               "table-free measurement",
        measured=dict(
            artifacts=measured,
            proof_nodes=meas_proof,
            generation_search_nodes=meas_gen,
            stored_bytes=meas_bytes,
            dual_verification_nodes=2 * meas_proof,
            dual_verification_note="verifier A and verifier B each replay "
                                   "every proof node, so verification costs "
                                   "about twice generation's proof output on "
                                   "top of generation itself",
            one_core_seconds_at_measured_rate=round(meas_gen / rate, 1),
            one_core_hours=round(meas_gen / rate / 3600, 2)),
        cheapest_measured_route=dict(
            per_family=cheapest,
            note="the shipped ladders were over-provisioned; these are the "
                 "cheapest subsets actually built and measured, not projections"),
        lower_bounds_from_capped_runs=lower,
        modelled=dict(
            cells=len(modelled),
            round_152_node_total=modelled_total,
            caveat="these are ROUND 152 figures, produced with the full "
                   "capacity table available.  Round 170's two table-free "
                   "measurements came in at 8,099,282 and 218 against the "
                   "same kind of target, so this total is a reference point "
                   "and not a forecast of the table-free cost",
            per_cell=modelled),
        unknown=dict(cells=len(unknown), list=unknown),
        superseded_forecasts=dict(
            round_167="82,812,460,012 nodes remaining",
            round_169="78,530,698,586 nodes remaining",
            why_not_reused="both extrapolated one cost model across every "
                           "uncertified cell; round 170 measured two and got "
                           "figures four orders of magnitude apart"),
        basis=dict(size=len(BASIS),
                   certified_and_dual_verified=len(
                       recl["basis_cells_with_certificate"]),
                   still_to_certify=len(todo)),
        helper_certificates=dict(
            count=recl["tally"].get("USEFUL_INVESTMENT_PREDECESSOR", 0),
            note="cells carried by existing certificates that close no census "
                 "row but are cited as dependencies by a shipped proof"),
        seconds_noncanonical=0.0,
        ok=True,
    )
    (ROOT / "r170" / "certs" / "global_cost_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("modelled",)}, ensure_ascii=False,
                     indent=1))
    print(f"\nmodelled: {len(modelled)} cells, round-152 total "
          f"{modelled_total:,} (reference point, not a forecast)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
