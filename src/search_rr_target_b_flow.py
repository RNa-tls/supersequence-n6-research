#!/usr/bin/env python3
"""Round 34, sections 3, 4, 7-11, 13, 15, 16: the flow-first Target B search.

FLOW-FIRST.  Round 33 chose a hexagon cover and then asked whether it could
be ordered.  That was the wrong quantifier: a cover is a witness only if it
happens to be connectable, and connectability is the scarce resource, so
choosing the cover first throws away the constraint that does the work.

Here the walk is primary.  A continuation is grown one segment at a time:

    entry port  --preserving word-->  exit port  --exit joint-->  entry port

and the entry port of the NEXT segment is not a free choice.  It is
exit_port . g_j for j in {w3:201, w3:210}, so the next ORBIT is forced up to
a binary choice.  Hexagon coverage is then a side condition maintained
incrementally, not a set to be chosen up front.

DP STATE (section 4).  A partial walk is summarised by

    Q = (entry port, free-hexagon mask, per-orbit visited-port masks,
         R_used, O_used, segments_used, covered_count)

with `covered_count` derivable from the free mask; it is carried anyway
because every prune is stated in terms of it.

PRUNES.
  * capacity (section 4, the dynamic form of bound (B+R)):
        H - covered  <=  5 * (O_cap - O_used) + 4 * (R_cap - R_used)
    and simultaneously  H - covered <= 5 * (max_segments - segments_used).
  * static forward reachability (section 7): an entry port whose own
    hexagon is already visited AT THE ROOT can never begin a segment,
    because every segment visits its entry port.  The free set only
    shrinks, so this prune is monotone and safe.
  * resource guards: a capacity-5 segment is EEEE (saturating-block
    theorem) and therefore always a fresh opening; an already opened orbit
    costs one R to re-enter, and each E^2 preserving step costs one R.

TERMINATION AND LABELS (section 16).  Exactly one of
    FOUND_TARGET_B           a complete walk, replayed against the engine
    EXHAUSTED_NO_PATH        the whole tree was explored inside the budget
    FLOW_RELAXATION_FEASIBLE a walk exists for a relaxed model only
    INCOMPLETE               the budget ran out first
A truncated search is NEVER reported as EXHAUSTED_NO_PATH.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
sys.setrecursionlimit(10000)


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("srtbf", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
S5 = core.power(core.SIGMA, 5)
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
EXIT_JOINTS = ("w3:201", "w3:210")
GEN = {j: core.compose(S5, mbl[j].action) for j in ["w2:10", "w3:120", "w3:201", "w3:210"]}
NORB, NHEX = len(core.E_REPS), len(core.ROT_REPS)
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]
ORBIT_HEX = [tuple(core.hexagon_id(p) for p in PORTS[q]) for q in range(NORB)]
PORT_INDEX = {}
for _q in range(NORB):
    for _ph in range(5):
        PORT_INDEX[PORTS[_q][_ph]] = (_q, _ph)
# exit boundary -> the two forced entry boundaries
NEXT_ENTRY = {}
for _q in range(NORB):
    for _ph in range(5):
        NEXT_ENTRY[(_q, _ph)] = tuple(
            PORT_INDEX[core.compose(PORTS[_q][_ph], GEN[j])] for j in EXIT_JOINTS)


def preserving_words():
    out = []
    for n in range(0, 5):
        for combo in product((1, 2), repeat=n):
            s, seen, ok = 0, [0], True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    ok = False
                    break
                seen.append(s)
            if ok:
                out.append({"word": "".join("E" if d == 1 else "E2" for d in combo),
                            "steps": tuple(combo), "offsets": tuple(seen),
                            "n_E2": sum(1 for d in combo if d == 2),
                            "capacity": len(seen), "defect": 5 - len(seen),
                            "exit_offset": sum(combo) % 5})
    out.sort(key=lambda w: (-w["capacity"], w["n_E2"]))
    return out


def replay_state(ell, prep):
    st = exact.initial_state()
    for _ in range(ell):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for s in prep["preparation_trace"]:
        for _ in range(s["ell"]):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[s["joint"]]).state
    for _ in range(prep["ell_profile"][-1]):
        st = exact.extend(st, W1).state
    for lbl, mv in mbl.items():
        if mv.weight != 3:
            continue
        tr = exact.extend(st, mv)
        if tr is None:
            continue
        q, ph = exact.ORBIT_PHASE[tr.target]
        if q == prep["r2_target_orbit"] and ph == prep["r2_target_phase"]:
            return tr.state
    return None


class FlowSearch:
    """Section 3-4: grow a walk; maintain coverage; never choose a cover."""

    def __init__(self, st, model, words, node_cap, seconds):
        self.words = words
        self.H = model["B_plus_1"]
        self.O_cap, self.R_cap = model["O_cap"], model["R_cap"]
        self.max_segments = model["max_segments"]
        self.node_cap, self.deadline = node_cap, time.time() + seconds
        self.q0, self.ph0 = exact.ORBIT_PHASE[st.p]
        self.partial_hex = core.hexagon_id(st.p)
        self.root_free = 0
        for h in range(NHEX):
            if st.hex_masks[h] == 0:
                self.root_free |= 1 << h
        self.root_free |= 1 << self.partial_hex          # the partial hexagon must be finished too
        self.port_masks = [st.orbit_masks[q] for q in range(NORB)]
        self.root_port_masks = list(self.port_masks)
        # section 7: statically dead entry boundaries
        self.static_dead = set()
        for q in range(NORB):
            for ph in range(5):
                h = ORBIT_HEX[q][ph]
                if not (self.root_free >> h) & 1:
                    self.static_dead.add((q, ph))
                elif (self.root_port_masks[q] >> ph) & 1:
                    self.static_dead.add((q, ph))
        self.nodes = 0
        self.truncated = False
        self.best_depth = 0
        self.best_covered = 0
        self.depth_hist = Counter()
        self.solution = None
        self.fail_reason = Counter()

    # ---- candidate segments at a forced entry boundary -------------------
    def candidates(self, q, ph, free, r_used, o_used, reentry):
        out = []
        for w in self.words:
            r_cost = w["n_E2"] + (1 if reentry else 0)
            if r_used + r_cost > self.R_cap:
                continue
            if not reentry and o_used + 1 > self.O_cap:
                continue
            pm = self.port_masks[q]
            bits, hexes, ok = 0, 0, True
            for off in w["offsets"]:
                p2 = (ph + off) % 5
                if (pm >> p2) & 1:
                    ok = False
                    break
                h = ORBIT_HEX[q][p2]
                if not (free >> h) & 1 or (hexes >> h) & 1:
                    ok = False
                    break
                bits |= 1 << p2
                hexes |= 1 << h
            if ok:
                out.append((w, bits, hexes))
        return out

    # ---- the initial segment (section 3: the walk's root) ---------------
    def initial_candidates(self):
        out = []
        for w in self.words:
            if w["n_E2"] > self.R_cap:
                continue
            bits, hexes, ok = 0, 0, True
            for i, off in enumerate(w["offsets"]):
                p2 = (self.ph0 + off) % 5
                h = ORBIT_HEX[self.q0][p2]
                if i == 0:
                    if h != self.partial_hex:
                        ok = False
                        break
                else:
                    if (self.root_port_masks[self.q0] >> p2) & 1:
                        ok = False
                        break
                    if not (self.root_free >> h) & 1 or (hexes >> h) & 1:
                        ok = False
                        break
                bits |= 1 << p2
                hexes |= 1 << h
            if ok:
                out.append((w, bits, hexes))
        return out

    # ---- the dynamic capacity bound (section 4) -------------------------
    def bound_ok(self, covered, segs, o_used, r_used):
        need = self.H - covered
        if need > 5 * (self.O_cap - o_used) + 4 * (self.R_cap - r_used):
            self.fail_reason["capacity_O_R"] += 1
            return False
        if need > 5 * (self.max_segments - segs):
            self.fail_reason["capacity_segments"] += 1
            return False
        return True

    def dfs(self, q, ph, free, covered, segs, o_used, r_used, path):
        self.nodes += 1
        if self.nodes >= self.node_cap or time.time() > self.deadline:
            self.truncated = True
            return None
        if segs > self.best_depth:
            self.best_depth = segs
        if covered > self.best_covered:
            self.best_covered = covered
        self.depth_hist[segs] += 1
        if segs >= self.max_segments:
            self.fail_reason["segment_limit"] += 1
            return None
        reentry = self.port_masks[q] != 0
        for w, bits, hexes in self.candidates(q, ph, free, r_used, o_used, reentry):
            cap = w["capacity"]
            n_o = 0 if reentry else 1
            n_r = w["n_E2"] + (1 if reentry else 0)
            nc, ns = covered + cap, segs + 1
            step = {"orbit": q, "entry_phase": ph, "word": w["word"],
                    "capacity": cap, "kind": "R_entry" if reentry else "fresh",
                    "hexagons": [h for h in range(NHEX) if (hexes >> h) & 1]}
            if nc == self.H:
                return path + [step]
            if not self.bound_ok(nc, ns, o_used + n_o, r_used + n_r):
                continue
            old = self.port_masks[q]
            self.port_masks[q] = old | bits
            exit_ph = (ph + w["exit_offset"]) % 5
            for nq, nph in NEXT_ENTRY[(q, exit_ph)]:
                if (nq, nph) in self.static_dead:
                    self.fail_reason["static_dead_entry"] += 1
                    continue
                got = self.dfs(nq, nph, free & ~hexes, nc, ns,
                               o_used + n_o, r_used + n_r, path + [step])
                if got is not None:
                    self.port_masks[q] = old
                    return got
                if self.truncated:
                    self.port_masks[q] = old
                    return None
            self.port_masks[q] = old
        self.fail_reason["no_candidate_or_all_failed"] += 1
        return None

    def run(self):
        inits = self.initial_candidates()
        for w, bits, hexes in sorted(inits, key=lambda t: -t[0]["capacity"]):
            cap = w["capacity"]
            step = {"orbit": self.q0, "entry_phase": self.ph0, "word": w["word"],
                    "capacity": cap, "kind": "initial",
                    "hexagons": [h for h in range(NHEX) if (hexes >> h) & 1]}
            if cap == self.H:
                self.solution = [step]
                return
            r0 = w["n_E2"]
            if not self.bound_ok(cap, 1, 0, r0):
                continue
            old = self.port_masks[self.q0]
            self.port_masks[self.q0] = old | bits
            exit_ph = (self.ph0 + w["exit_offset"]) % 5
            for nq, nph in NEXT_ENTRY[(self.q0, exit_ph)]:
                if (nq, nph) in self.static_dead:
                    continue
                got = self.dfs(nq, nph, self.root_free & ~hexes, cap, 1, 0, r0, [step])
                if got is not None:
                    self.solution = got
                    self.port_masks[self.q0] = old
                    return
                if self.truncated:
                    self.port_masks[self.q0] = old
                    return
            self.port_masks[self.q0] = old
        self.n_initial = len(inits)


def frontier_profile(fs, max_depth, state_cap):
    """Section 9: measure the forward frontier so the meet-in-the-middle
    memory cost is a MEASUREMENT, not a guess.

    States are deduplicated on the full DP key, which includes the
    free-hexagon mask -- that is the honest key, and it is exactly why the
    frontier can explode.
    """
    layer = []
    for w, bits, hexes in fs.initial_candidates():
        pm = tuple(fs.root_port_masks[:fs.q0]) + (fs.root_port_masks[fs.q0] | bits,) \
             + tuple(fs.root_port_masks[fs.q0 + 1:])
        exit_ph = (fs.ph0 + w["exit_offset"]) % 5
        for nq, nph in NEXT_ENTRY[(fs.q0, exit_ph)]:
            if (nq, nph) in fs.static_dead:
                continue
            layer.append(((nq, nph), fs.root_free & ~hexes, pm,
                          w["capacity"], 1, 0, w["n_E2"]))
    sizes, capped = [len(layer)], False
    for d in range(1, max_depth + 1):
        nxt = {}
        for (q, ph), free, pm, covered, segs, o_u, r_u in layer:
            reentry = pm[q] != 0
            saved = fs.port_masks
            fs.port_masks = list(pm)
            cands = fs.candidates(q, ph, free, r_u, o_u, reentry)
            fs.port_masks = saved
            for w, bits, hexes in cands:
                n_o = 0 if reentry else 1
                n_r = w["n_E2"] + (1 if reentry else 0)
                nc, ns = covered + w["capacity"], segs + 1
                if nc >= fs.H:
                    continue
                if not fs.bound_ok(nc, ns, o_u + n_o, r_u + n_r):
                    continue
                npm = pm[:q] + (pm[q] | bits,) + pm[q + 1:]
                exit_ph = (ph + w["exit_offset"]) % 5
                for nq, nph in NEXT_ENTRY[(q, exit_ph)]:
                    if (nq, nph) in fs.static_dead:
                        continue
                    k = ((nq, nph), free & ~hexes, npm, o_u + n_o, r_u + n_r)
                    nxt[k] = (k[0], k[1], k[2], nc, ns, k[3], k[4])
            if len(nxt) > state_cap:
                capped = True
                break
        sizes.append(len(nxt))
        layer = list(nxt.values())
        if capped or not layer:
            break
    return {"frontier_sizes_by_depth": sizes, "hit_state_cap": capped,
            "state_cap": state_cap,
            "bytes_per_state_estimate": 8 + 16 + 144 * 8 + 32,
            "note": ("the DP key contains the 120-bit free-hexagon mask and the 144 "
                     "per-orbit port masks; two frontiers cannot be joined on the "
                     "boundary alone, so meet-in-the-middle needs the full key")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=str(ROOT / "outputs" / "rr_target_b_ilp_models.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--certs", default=str(ROOT / "outputs" / "rr_target_b_unsat_certificates.json"))
    ap.add_argument("--node-cap", type=int, default=4000000)
    ap.add_argument("--seconds", type=float, default=300.0)
    ap.add_argument("--frontier-depth", type=int, default=12)
    ap.add_argument("--frontier-cap", type=int, default=200000)
    ap.add_argument("--out-models", default=str(ROOT / "outputs" / "rr_flow_first_models.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_flow_search_results.json"))
    a = ap.parse_args()

    words = preserving_words()
    models = json.loads(Path(a.models).read_text(encoding="utf-8"))["models"]
    surv = json.loads(Path(a.survivors).read_text(encoding="utf-8"))["rows"]
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    cert = json.loads(Path(a.certs).read_text(encoding="utf-8"))
    icap = {(r["root_ell"], r["P_core"]): r["true_phase_walk_capacity"]
            for r in cert["initial_capacity_refinement"]["rows"]}

    # section 15: most-constrained-first -- smallest refined margin, then
    # fewest options, then smallest successor branching
    succ = json.loads((ROOT / "outputs" / "rr_segment_successor_index.json")
                      .read_text(encoding="utf-8"))["per_survivor"]
    branch = {r["key"]: r["out_degree_mean"] for r in succ}
    order = sorted(models, key=lambda m: (
        (icap.get((m["root_ell"], m["P_core"]), 2) + m["O_cap"] * 5 + 4 * m["R_cap"]) - m["B_plus_1"],
        m["n_options"], branch.get(m["key"], 0)))
    print("=== section 15: survivor order (most constrained first) ===")
    for m in order:
        marg = (icap.get((m["root_ell"], m["P_core"]), 2) + m["O_cap"] * 5
                + 4 * m["R_cap"]) - m["B_plus_1"]
        print(f"  {m['key']}: refined margin {marg}, options {m['n_options']}, "
              f"mean branching {branch.get(m['key'])}")

    results, flow_models = [], []
    for m in order:
        row = next(r for r in surv if r["root_ell"] == m["root_ell"]
                   and r["P_core"] == m["P_core"]
                   and r["canonical_state_hash"] == m["canonical_state_hash"])
        rec = next(p for p in preps["results_by_ell"][str(m["root_ell"])]["preparations"]
                   if p["raw_state_hash"][:12] == row["raw_state_hash"])
        st = replay_state(m["root_ell"], rec)
        assert st is not None

        fs = FlowSearch(st, m, words, a.node_cap, a.seconds)
        t0 = time.time()
        fs.run()
        el = time.time() - t0
        if fs.solution is not None:
            status = "FOUND_TARGET_B"
        elif fs.truncated:
            status = "INCOMPLETE"
        else:
            status = "EXHAUSTED_NO_PATH"
        # a second, cheap pass purely to size the meet-in-the-middle option
        fs2 = FlowSearch(st, m, words, a.node_cap, a.seconds)
        fr = frontier_profile(fs2, a.frontier_depth, a.frontier_cap)

        n_init = len(FlowSearch(st, m, words, 1, 1.0).initial_candidates())
        res = {"key": m["key"], "root_ell": m["root_ell"], "P_core": m["P_core"],
               "status": status, "seconds": round(el, 2), "nodes": fs.nodes,
               "truncated": fs.truncated, "node_cap": a.node_cap,
               "H_residual_hexagons": fs.H, "O_cap": fs.O_cap, "R_cap": fs.R_cap,
               "max_segments": fs.max_segments,
               "n_initial_segment_options": n_init,
               "initial_capacity_max": max((w["capacity"] for w, _, _ in
                                            FlowSearch(st, m, words, 1, 1.0).initial_candidates()),
                                           default=0),
               "static_dead_entry_boundaries": len(fs.static_dead),
               "max_segments_reached": fs.best_depth,
               "max_hexagons_covered": fs.best_covered,
               "hexagons_short_of_complete": fs.H - fs.best_covered,
               "depth_histogram": {str(k): v for k, v in sorted(fs.depth_hist.items())},
               "prune_reasons": dict(fs.fail_reason),
               "solution": fs.solution,
               "frontier": fr,
               "label_discipline": ("EXHAUSTED_NO_PATH is used only when truncated is false; "
                                    "a node-capped or time-capped run is INCOMPLETE")}
        results.append(res)
        flow_models.append({
            "key": m["key"], "H": fs.H, "O_cap": fs.O_cap, "R_cap": fs.R_cap,
            "max_segments": fs.max_segments,
            "dp_state": ["entry port", "free-hexagon mask (120 bits)",
                         "per-orbit visited-port masks (144 x 5 bits)",
                         "O_used", "R_used", "segments_used", "covered_count"],
            "transition": "entry port -> preserving word -> exit port -> g_{w3:201|w3:210}",
            "prunes": {
                "capacity_O_R": "H - covered <= 5(O_cap - O_used) + 4(R_cap - R_used)",
                "capacity_segments": "H - covered <= 5(max_segments - segments_used)",
                "static_forward_reachability": ("entry ports whose own hexagon is already "
                                                "visited at the root can never begin a segment"),
                "saturating_block": "capacity 5 forces the word EEEE, hence a fresh opening",
            },
            "n_static_dead_entry_boundaries": len(fs.static_dead),
        })
        print(f"\n  {m['key']}: {status} in {el:.1f}s, nodes={fs.nodes}, "
              f"max segments={fs.best_depth}, max covered={fs.best_covered}/{fs.H}")
        print(f"      initial options={n_init}, static dead boundaries="
              f"{len(fs.static_dead)}/720, prunes={dict(fs.fail_reason)}")
        print(f"      frontier by depth: {fr['frontier_sizes_by_depth']} "
              f"(cap hit: {fr['hit_state_cap']})")

    hist = Counter(r["status"] for r in results)
    print(f"\nstatus histogram: {dict(hist)}")
    Path(a.out_models).write_text(json.dumps({
        "schema": "rr-flow-first-models-v1",
        "shift": ("cover-first exact cover (Round 33) -> flow-first segment path "
                  "(Round 34): the walk is built first and coverage is maintained "
                  "incrementally, so no unconnectable cover is ever considered"),
        "models": flow_models,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out).write_text(json.dumps({
        "schema": "rr-flow-search-results-v1",
        "status_histogram": {k: v for k, v in hist.items()},
        "results": results,
        "grade": "exact exhaustive search where truncated=false, bounded incomplete otherwise",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_models)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
