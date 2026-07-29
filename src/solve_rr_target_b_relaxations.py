#!/usr/bin/env python3
"""Round 33, sections 5, 14-20: the relaxation hierarchy R0..R5.

R0  capacity count            -- decided in Round 32 (reused, not re-derived)
R1  hexagon exact cover       -- attacked constructively here
R2  port uniqueness           -- IMPLIED BY R1, 손증명 (see below)
R3  segment flow / order      -- exact on a found R1 solution (<= 25 segments)
R4  literal collision         -- exact engine replay of the reconstructed word
R5  component compatibility   -- NECESSARY-CONDITION ONLY; labels are recorded
                                 but never imposed, because Target B's final
                                 component requirement is uncharacterised

R2 from R1 (손증명): every option covers exactly one port per hexagon it
covers, and the five ports of an E-orbit lie in five DISTINCT hexagons.
So if the chosen options partition the residual hexagons, no hexagon is
touched twice and hence no port is used twice.  Port uniqueness is not an
extra constraint once R1 holds.

Discipline: R1 is attacked by CONSTRUCTION.  Finding a cover certifies
feasibility; failing to find one within the budget is reported as
`bounded incomplete`, never as infeasible.  No solver library exists in
this environment, so nothing is delegated to an unverified oracle.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from collections import Counter, defaultdict
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


macro = _load("srtbr", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
S5 = core.power(core.SIGMA, 5)
mbl = {m.label: m for m in exact.ALL_MOVES}
GEN = {j: core.compose(S5, mbl[j].action) for j in ["w2:10", "w3:120", "w3:201", "w3:210"]}
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(len(core.E_REPS))]


def exact_cover(options, targets, max_segments, budgets, node_cap, deadline):
    """Algorithm-X style exact cover on hexagons, most-constrained-first.

    Returns (status, solution) with status in {FEASIBLE, INCOMPLETE,
    EXHAUSTED_INFEASIBLE}.  EXHAUSTED_INFEASIBLE is only returned when the
    whole search tree was explored inside the budget.
    """
    by_hex = defaultdict(list)
    for o in options:
        for h in o["covered_hexagons"]:
            by_hex[h].append(o)
    nodes = [0]
    truncated = [False]

    def rec(remaining, chosen, o_used, r_used):
        if time.time() > deadline or nodes[0] >= node_cap:
            truncated[0] = True
            return None
        nodes[0] += 1
        if not remaining:
            return list(chosen)
        if len(chosen) >= max_segments:
            return None
        # bound: even all-capacity-5 segments cannot finish
        if len(remaining) > 5 * (max_segments - len(chosen)):
            return None
        h = min(remaining, key=lambda x: sum(
            1 for o in by_hex[x]
            if set(o["covered_hexagons"]) <= remaining
            and o_used + o["O_cost"] <= budgets["O_cap"]
            and r_used + o["R_cost"] <= budgets["R_cap"]))
        cands = [o for o in by_hex[h]
                 if set(o["covered_hexagons"]) <= remaining
                 and o_used + o["O_cost"] <= budgets["O_cap"]
                 and r_used + o["R_cost"] <= budgets["R_cap"]]
        cands.sort(key=lambda o: -o["capacity"])
        for o in cands:
            got = rec(remaining - set(o["covered_hexagons"]), chosen + [o],
                      o_used + o["O_cost"], r_used + o["R_cost"])
            if got is not None:
                return got
        return None

    sol = rec(set(targets), [], 0, 0)
    if sol is not None:
        return "FEASIBLE", sol, nodes[0], truncated[0]
    return ("INCOMPLETE" if truncated[0] else "EXHAUSTED_INFEASIBLE"), None, nodes[0], truncated[0]


def partition_cover(options, model, tries=4000, seed=12345):
    """Constructive R1 strategy that uses the algebraic structure instead of
    blind backtracking.

    The 120 hexagons admit a PERFECT partition into 24 orbits (Round 32).
    So look for a perfect partition whose orbits are all usable at this
    state -- q0 plus unopened orbits -- and then realise each orbit's
    residual hexagons by a legal phase-walk option.  An orbit missing
    exactly one hexagon is coverable by EEE entered one phase after the
    missing one; that is why partial orbits are not an obstacle.
    """
    import random
    rng = random.Random(seed)
    ORBIT_HEX = [tuple(core.hexagon_id(p) for p in PORTS[q]) for q in range(len(PORTS))]
    residual = set(model["residual_hexagons"])
    q0 = model["current_orbit"]
    by_orbit = defaultdict(list)
    for o in options:
        by_orbit[o["orbit"]].append(o)
    usable = [q for q in by_orbit if q != q0]
    # the DETERMINISTIC sorted greedy already yields a perfect 24-orbit
    # partition of all 120 hexagons (Round 32); try it first, then randomise
    orders = [sorted(usable)]
    for _ in range(tries):
        o = usable[:]
        rng.shuffle(o)
        orders.append(o)
    for order in orders:
        used_hex = set()
        # q0 first: take its best initial option
        init = max((o for o in by_orbit[q0] if o["kind"] == "initial"),
                   key=lambda o: o["capacity"], default=None)
        if init is None:
            return None
        used_hex |= set(init["covered_hexagons"])
        picked = [init]
        o_used = init["O_cost"]
        r_used = init["R_cost"]
        ok = True
        for q in order:
            hexes = set(ORBIT_HEX[q])
            if hexes & used_hex:
                continue
            need = hexes & residual
            if not need:
                continue
            cand = [o for o in by_orbit[q]
                    if set(o["covered_hexagons"]) == need
                    and o_used + o["O_cost"] <= model["O_cap"]
                    and r_used + o["R_cost"] <= model["R_cap"]]
            if not cand:
                continue
            o = max(cand, key=lambda x: x["capacity"])
            picked.append(o)
            used_hex |= hexes
            o_used += o["O_cost"]
            r_used += o["R_cost"]
            if len(picked) > model["max_segments"]:
                ok = False
                break
        if ok and residual <= used_hex and len(picked) <= model["max_segments"]:
            return picked
        # partition-SEEDED finish: the deterministic partition typically leaves a
        # handful of hexagons uncovered (q0's residual set is not phase-walk
        # reachable in full), so hand the remainder to the exact-cover search.
        left = residual - used_hex
        if ok and left and len(picked) < model["max_segments"]:
            avail = [o for o in options
                     if not (set(o["covered_hexagons"]) & used_hex)
                     and set(o["covered_hexagons"]) <= left]
            st2, tail, _, _ = exact_cover(
                avail, sorted(left), model["max_segments"] - len(picked),
                {"O_cap": model["O_cap"] - o_used, "R_cap": model["R_cap"] - r_used},
                200000, __import__("time").time() + 20.0)
            if st2 == "FEASIBLE":
                return picked + tail
    return None


def order_segments(sol, start_orbit, start_phase):
    """R3: can the chosen segments be linearly ordered into one walk?

    Segment (q, ph, word) exits at port (q, ph+sum(steps)); the next entry
    port is that port composed with g(w3:201) or g(w3:210).  With <= 25
    segments this is a small exact search.
    """
    idx = {(o["orbit"], o["entry_phase"]): o for o in sol}
    start = next((o for o in sol if o["kind"] == "initial"), None)
    if start is None:
        return {"status": "NO_INITIAL_SEGMENT"}
    succ = defaultdict(list)
    for o in sol:
        p_exit = PORTS[o["orbit"]][o["exit_phase"]]
        for j in ["w3:201", "w3:210"]:
            t = core.compose(p_exit, GEN[j])
            tq, tph = exact.ORBIT_PHASE[t]
            nxt = idx.get((tq, tph))
            if nxt is not None and nxt is not o:
                succ[o["id"]].append((j, nxt["id"]))
    byid = {o["id"]: o for o in sol}
    n = len(sol)
    best = [0]

    def dfs(cur, used, path):
        best[0] = max(best[0], len(used))
        if len(used) == n:
            return list(path)
        for j, nid in succ[cur]:
            if nid in used:
                continue
            got = dfs(nid, used | {nid}, path + [(j, nid)])
            if got is not None:
                return got
        return None

    path = dfs(start["id"], {start["id"]}, [])
    return {"status": ("ORDERED" if path else "NO_ORDER_FOR_THIS_COVER"),
            "discipline": ("a cover with no linear order is NOT an obstruction: another "
                           "cover of the same state may be orderable. Only an exhaustive "
                           "enumeration of covers could turn this into an R3 obstruction, "
                           "and that was not done."),
            "longest_chain": best[0], "n_segments": n,
            "successor_edge_count": sum(len(v) for v in succ.values()),
            "segments_with_no_successor": sum(1 for o in sol if not succ[o["id"]]),
            "path_len": len(path) + 1 if path else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--options", default=str(ROOT / "outputs" / "rr_segment_options.json"))
    ap.add_argument("--models", default=str(ROOT / "outputs" / "rr_target_b_ilp_models.json"))
    ap.add_argument("--node-cap", type=int, default=400000)
    ap.add_argument("--seconds", type=float, default=120.0)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_target_b_relaxation_results.json"))
    ap.add_argument("--out-sol", default=str(ROOT / "outputs" / "rr_target_b_reconstructed_solutions.json"))
    a = ap.parse_args()

    opts_all = json.loads(Path(a.options).read_text(encoding="utf-8"))["options_by_survivor"]
    models = json.loads(Path(a.models).read_text(encoding="utf-8"))["models"]
    results, sols = [], {}
    for m in models:
        key = m["key"]
        options = opts_all[key]
        targets = m["residual_hexagons"]
        budgets = {"O_cap": m["O_cap"], "R_cap": m["R_cap"]}
        t0 = time.time()
        sol = partition_cover(options, m)
        if sol is not None:
            status, nodes, trunc = "FEASIBLE", 0, False
            strategy = "perfect-partition construction"
        else:
            status, sol, nodes, trunc = exact_cover(
                options, targets, m["max_segments"], budgets,
                a.node_cap, time.time() + a.seconds)
            strategy = "algorithm-X backtracking"
        el = time.time() - t0
        row = {"key": key, "root_ell": m["root_ell"], "P_core": m["P_core"],
               "n_options": m["n_options"], "n_residual_hexagons": m["n_residual_hexagons"],
               "max_segments": m["max_segments"],
               "R0_capacity": "FEASIBLE (Round 32: it is a survivor)",
               "R1_hexagon_exact_cover": status,
               "R1_strategy": strategy,
               "R1_nodes": nodes, "R1_seconds": round(el, 1),
               "R1_truncated": trunc,
               "R2_port_uniqueness": ("IMPLIED_BY_R1 (손증명)" if status == "FEASIBLE"
                                      else "not reached"),
               }
        if sol is not None:
            caps = sum(o["capacity"] for o in sol)
            row["R1_solution_segments"] = len(sol)
            row["R1_solution_total_capacity"] = caps
            row["R1_solution_O_cost"] = sum(o["O_cost"] for o in sol)
            row["R1_solution_R_cost"] = sum(o["R_cost"] for o in sol)
            o3 = order_segments(sol, m["current_orbit"], m["current_phase"])
            row["R3_flow_order"] = o3["status"]
            row["R3_detail"] = o3
            row["R4_literal_collision"] = (
                "not reached -- this cover has no linear order"
                if o3["status"] != "ORDERED" else "reached, not yet replayed")
            sols[key] = [{k: o[k] for k in ("id", "kind", "orbit", "entry_phase",
                                            "preserving_word", "capacity",
                                            "covered_hexagons", "O_cost", "R_cost")}
                         for o in sol]
            # NOT "R3": one unorderable cover does not make R3 infeasible
            row["first_failing_layer"] = None
            row["r3_note"] = ("the single cover produced was not orderable; R3 is "
                              "UNDECIDED for this state, not failed")
        else:
            row["first_failing_layer"] = "R1" if status == "EXHAUSTED_INFEASIBLE" else None
        results.append(row)
        print(f"  {key}: R1={status} nodes={nodes} {el:.1f}s"
              + (f" segs={row.get('R1_solution_segments')} "
                 f"cap={row.get('R1_solution_total_capacity')} "
                 f"R3={row.get('R3_flow_order')}" if sol else ""))

    hist = Counter(r["R1_hexagon_exact_cover"] for r in results)
    print(f"\n R1 status histogram: {dict(hist)}")
    print(f" R3 status histogram: "
          f"{dict(Counter(r.get('R3_flow_order', 'not reached') for r in results))}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-target-b-relaxation-results-v1",
        "layer_semantics": {
            "infeasible": "Target B impossible at that state -- but ONLY if the search "
                          "was exhaustive (EXHAUSTED_INFEASIBLE), never on a truncation",
            "feasible": "a RELAXATION survivor only; it is NOT a Target B solution, "
                        "because component compatibility (R5) is not modelled",
        },
        "R2_from_R1": ("손증명: each option covers exactly one port per covered hexagon and "
                       "an orbit's five ports lie in five distinct hexagons, so a hexagon "
                       "partition forces port uniqueness"),
        "no_solver_library": True,
        "node_cap": a.node_cap, "seconds_per_survivor": a.seconds,
        "results": results,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out_sol).write_text(json.dumps({
        "schema": "rr-target-b-reconstructed-solutions-v1",
        "warning": ("these are R1-layer covers only. A cover is NOT a Target B "
                    "continuation: it ignores segment order (R3), literal collisions (R4) "
                    "and component compatibility (R5)."),
        "solutions": sols,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)
    print("wrote", a.out_sol)


if __name__ == "__main__":
    main()
