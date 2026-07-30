#!/usr/bin/env python3
"""Round 34, sections 1, 2, 5, 6: the segment successor index.

Round 33 built a COVER-FIRST model: pick a set of segments that partitions
the residual hexagons, then try to order them.  Four survivors admitted a
cover; none of those covers could be ordered, and the reason was visible in
one number -- among the 24-25 segments of a cover there were 0 or 1
successor edges.  That says nothing about Target B, because the cover was
chosen without any regard for connectability.

This round inverts the model.  A Target B continuation is not a SET of
segments, it is a WALK: the segment you may enter next is not a free
choice, it is determined by where the previous segment ends.  So the
primitive object is a directed transition, and the first thing to build is
the transition relation itself.

BOUNDARY.  A segment is entered at a port (a permutation that is one of the
five ports of an E-orbit) and left at a port of the same orbit:

    entry boundary   K_in(x)  = entry port  = PORTS[q][ph]
    exit  boundary   K_out(x) = exit  port  = PORTS[q][ph + sum(steps)]

Every permutation is a port of exactly one E-orbit (144 x 5 = 720), so a
port and a boundary key are the same thing; the index is over 720 keys, not
over the ~9,000 options, and no O(n^2) pairwise comparison is needed
(section 2).

TRANSITION.  Leaving a segment means applying an orbit-CHANGING joint.  Of
the four joints only w3:201 and w3:210 leave <E>; w2:10 and w3:120 act as E
and E^2 and are the preserving steps INSIDE a segment.  So

    succ(x) = union over j in {w3:201, w3:210} of options entered at
              K_out(x) . g_j

RESOURCES ARE NOT PART OF THE KEY.  R-used, F-def and the covered-hexagon
set are path-dependent, so they cannot be folded into a static index
without destroying it.  The index is purely geometric; the resource guards
are applied at traversal time by search_rr_target_b_flow.py.  Recording
that split explicitly is the point -- an index keyed on resources would be
a different (and much larger) object.

Also proved here, because it is cheap once the port structure is in hand:
the HEXAGON-DISJOINTNESS THEOREM of section 5.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("brss", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
S5 = core.power(core.SIGMA, 5)
mbl = {m.label: m for m in exact.ALL_MOVES}
GEN = {j: core.compose(S5, mbl[j].action) for j in ["w2:10", "w3:120", "w3:201", "w3:210"]}
EXIT_JOINTS = ["w3:201", "w3:210"]
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(len(core.E_REPS))]
ORBIT_HEX = [tuple(core.hexagon_id(p) for p in PORTS[q]) for q in range(len(PORTS))]
PORT_INDEX = {}
for _q in range(len(PORTS)):
    for _ph in range(5):
        PORT_INDEX[PORTS[_q][_ph]] = (_q, _ph)


# --------------------------------------------------------------------------
# section 5: the hexagon-disjointness theorem
# --------------------------------------------------------------------------
def hexagon_disjointness_theorem():
    """Does hexagon-disjointness of ell=5 segments imply permutation-
    disjointness?  YES, and the proof is two facts about the port structure.

    (i) The 120 hexagons -- the orbits of right multiplication by SIGMA --
        PARTITION the 720 permutations into blocks of 6.
    (ii) An ell=5 rotation run from a port p visits p.SIGMA^0 .. p.SIGMA^5,
         which is exactly the 6 permutations of hexagon(p).

    So the permutation set consumed by a capacity-k segment is the disjoint
    union of the k hexagons it covers, and two segments covering disjoint
    hexagons consume disjoint permutations.  There is no counterexample to
    find; R4 (literal collision) is therefore IMPLIED by R1 (hexagon exact
    cover) for all segments made of full ell=5 runs.

    ONE EXCEPTION, and it is the reason R4 is not deleted.  The very first
    hexagon of the very first segment is the hexagon the boundary state is
    standing in, which is already PARTIALLY visited.  Completing it is not a
    fresh ell=5 run, and whether the remaining rotations avoid the already
    visited positions is a property of the state, not of the hexagon
    algebra.  That single case is checked by engine replay, never by this
    theorem.
    """
    allp = list(permutations(range(6)))
    blocks = defaultdict(list)
    for p in allp:
        blocks[core.hexagon_id(p)].append(p)
    sizes = sorted({len(v) for v in blocks.values()})
    partition_ok = (len(allp) == 720 and len(blocks) == 120 and sizes == [6]
                    and sum(len(v) for v in blocks.values()) == 720)

    # (ii) verified at every one of the 720 ports
    run_ok, run_sizes = True, set()
    for p in allp:
        run = [core.compose(p, core.power(core.SIGMA, k)) for k in range(6)]
        run_sizes.add(len(set(run)))
        if set(core.hexagon_id(x) for x in run) != {core.hexagon_id(p)}:
            run_ok = False
    # every orbit's five ports lie in five DISTINCT hexagons (this is what
    # makes R2 follow from R1 as well)
    orbit_ports_distinct = all(len(set(ORBIT_HEX[q])) == 5 for q in range(len(PORTS)))
    return {
        "statement": ("for segments built from full ell=5 rotation runs, hexagon-"
                      "disjointness implies permutation-disjointness"),
        "grade": "손증명",
        "hexagons_partition_S6": partition_ok,
        "hexagon_block_size": sizes,
        "ell5_run_covers_exactly_its_hexagon": run_ok,
        "ell5_run_distinct_permutation_counts": sorted(run_sizes),
        "ports_checked": len(allp),
        "every_orbit_has_5_distinct_port_hexagons": orbit_ports_distinct,
        "consequence": ("R4 literal collision is implied by R1 for every segment "
                        "whose hexagons are all freshly entered; it does NOT cover "
                        "the partially visited hexagon the boundary state starts in, "
                        "which stays an engine-replay obligation"),
        "counterexample": None,
        "permutation_conflict_mask_still_needed": False,
        "exception": "the initial partially visited hexagon only",
    }


# --------------------------------------------------------------------------
# section 6: which segment-count / capacity profiles are even arithmetically
# possible?  "24-25 segments" was one solution's value, not a theorem.
# --------------------------------------------------------------------------
def capacity_profiles(model):
    """Exact enumeration of feasible (s, capacity multiset) profiles.

    Facts used, all previously proved:
      * a capacity-5 segment must be the word EEEE (the saturating-block
        theorem: the other two saturating blocks need 2 and 4 E^2 steps and
        R_cap is 1), so it costs no R and it can only be a FRESH opening --
        an already opened orbit has a visited port, so an R-entry segment
        has capacity <= 4;
      * the initial segment's capacity is at most the true phase-walk
        capacity of the boundary state (Round 33, 손증명);
      * total capacity must equal B+1 = the residual hexagon count;
      * segments <= O_cap + R_cap + 1, fresh <= O_cap, R-entries <= R_cap.

    This is a SAFE RELAXATION of the profile question, not an exact answer:
    it enforces the counting constraints but not the geometry (which orbits
    are actually available, which words are actually legal there).  Every
    genuinely feasible profile appears in the list; the converse is not
    claimed.
    """
    H = model["B_plus_1"]
    O_cap, R_cap = model["O_cap"], model["R_cap"]
    c_init_max = model.get("initial_capacity_max", 2)
    out = []
    for n_r in range(0, R_cap + 1):
        # R budget spent on re-entries leaves R_cap - n_r for E^2 steps;
        # a capacity-5 segment needs zero E^2, so E^2 only ever buys defect.
        # c_init >= 1: the walk stands at p, and p's hexagon (popcount 1 at
        # every boundary state) must be completed by the first ell=5 run
        for c_init in range(1, c_init_max + 1):
            for n_fresh in range(0, O_cap + 1):
                s = 1 + n_fresh + n_r
                if s > O_cap + R_cap + 1:
                    continue
                # fresh capacities in 1..5, R-entry capacities in 1..4
                lo = c_init + n_fresh * 1 + n_r * 1
                hi = c_init + n_fresh * 5 + n_r * 4
                if lo <= H <= hi:
                    out.append({"n_segments": s, "c_initial": c_init,
                                "n_fresh": n_fresh, "n_r_entry": n_r,
                                "total_defect": 5 * s - H,
                                "min_full_orbit_segments": max(0, H - c_init - 4 * (n_fresh + n_r))})
    return out


def build(model, options):
    by_entry = defaultdict(list)
    for o in options:
        by_entry[(o["orbit"], o["entry_phase"])].append(o["id"])
    trans, succ_counts, deg_by_kind = [], [], defaultdict(list)
    edge_total = 0
    for o in options:
        p_exit = PORTS[o["orbit"]][o["exit_phase"]]
        outs = []
        for j in EXIT_JOINTS:
            t = core.compose(p_exit, GEN[j])
            tq, tph = PORT_INDEX[t]
            ids = by_entry.get((tq, tph), [])
            outs.append({"joint": j, "entry_key": [tq, tph], "n_options": len(ids)})
            edge_total += len(ids)
        d = sum(x["n_options"] for x in outs)
        succ_counts.append(d)
        deg_by_kind[o["kind"]].append(d)
        trans.append({"id": o["id"], "kind": o["kind"],
                      "entry_key": [o["orbit"], o["entry_phase"]],
                      "exit_key": [o["orbit"], o["exit_phase"]],
                      "capacity": o["capacity"], "defect": o["defect"],
                      "O_cost": o["O_cost"], "R_cost": o["R_cost"],
                      "preserving_word": o["preserving_word"],
                      "covered_hexagons": o["covered_hexagons"],
                      "successors": outs, "out_degree": d})
    hist = Counter(succ_counts)
    return trans, {
        "n_options": len(options),
        "n_distinct_entry_keys": len(by_entry),
        "n_successor_edges": edge_total,
        "out_degree_min": min(succ_counts), "out_degree_max": max(succ_counts),
        "out_degree_mean": round(sum(succ_counts) / len(succ_counts), 3),
        "out_degree_histogram": {str(k): v for k, v in sorted(hist.items())},
        "options_with_no_successor": hist.get(0, 0),
        "out_degree_mean_by_kind": {k: round(sum(v) / len(v), 3)
                                    for k, v in sorted(deg_by_kind.items())},
        "options_per_entry_key_max": max(len(v) for v in by_entry.values()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--options", default=str(ROOT / "outputs" / "rr_segment_options.json"))
    ap.add_argument("--models", default=str(ROOT / "outputs" / "rr_target_b_ilp_models.json"))
    ap.add_argument("--certs", default=str(ROOT / "outputs" / "rr_target_b_unsat_certificates.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_segment_successor_index.json"))
    a = ap.parse_args()

    thm = hexagon_disjointness_theorem()
    print("=== section 5: hexagon-disjointness theorem ===")
    for k in ("hexagons_partition_S6", "hexagon_block_size",
              "ell5_run_covers_exactly_its_hexagon",
              "ell5_run_distinct_permutation_counts",
              "every_orbit_has_5_distinct_port_hexagons"):
        print(f"  {k}: {thm[k]}")
    print("  => hexagon-disjoint segments are permutation-disjoint; R4 is implied by R1")
    print("     EXCEPT for the initial partially visited hexagon.")

    opts_all = json.loads(Path(a.options).read_text(encoding="utf-8"))["options_by_survivor"]
    models = json.loads(Path(a.models).read_text(encoding="utf-8"))["models"]
    cert = json.loads(Path(a.certs).read_text(encoding="utf-8"))
    icap = {(r["root_ell"], r["P_core"]): r["true_phase_walk_capacity"]
            for r in cert["initial_capacity_refinement"]["rows"]}

    print("\n=== section 2: successor distribution over the WHOLE option universe ===")
    print("  (Round 33 saw 0-1 successor edges among the 24-25 segments of a cover)")
    rows, index = [], {}
    for m in models:
        key = m["key"]
        options = opts_all[key]
        m2 = dict(m)
        m2["initial_capacity_max"] = icap.get((m["root_ell"], m["P_core"]), 2)
        trans, stats = build(m2, options)
        profs = capacity_profiles(m2)
        index[key] = trans
        rows.append({"key": key, "root_ell": m["root_ell"], "P_core": m["P_core"],
                     "initial_capacity_max": m2["initial_capacity_max"],
                     **stats,
                     "n_feasible_capacity_profiles": len(profs),
                     "segment_counts_possible": sorted({p["n_segments"] for p in profs}),
                     "min_full_orbit_segments": (min(p["min_full_orbit_segments"] for p in profs)
                                                 if profs else None),
                     "capacity_profiles": profs})
        print(f"  {key}: options={stats['n_options']:>5} entry keys={stats['n_distinct_entry_keys']:>3} "
              f"edges={stats['n_successor_edges']:>6} out-degree min/mean/max="
              f"{stats['out_degree_min']}/{stats['out_degree_mean']}/{stats['out_degree_max']} "
              f"dead={stats['options_with_no_successor']}")
        print(f"      section 6: segment counts arithmetically possible = "
              f"{sorted({p['n_segments'] for p in profs})}, "
              f"profiles={len(profs)}, forced full-orbit segments >= "
              f"{min(p['min_full_orbit_segments'] for p in profs) if profs else '-'}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-segment-successor-index-v1",
        "model": ("a segment is a directed transition entry-port -> exit-port; the next "
                  "segment's entry port is exit_port . g_j for j in {w3:201, w3:210}. "
                  "Every permutation is a port of exactly one E-orbit, so boundary keys "
                  "and ports coincide and the index has 720 slots."),
        "resources_excluded_from_key": ["R_used", "O_used", "F_def", "covered hexagons"],
        "resource_note": ("path-dependent resources are deliberately NOT in the index key; "
                          "they are enforced at traversal time by the flow search"),
        "hexagon_disjointness_theorem": thm,
        "per_survivor": rows,
        "grade": "exact segment graph (index) + 손증명 (the disjointness theorem)",
        "successor_index": index,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
