#!/usr/bin/env python3
"""Round 69 (Claude): the structural invariant that decides whether a post-R1
legal R joint can EVER become same-component.

The question this module answers is not "is this R joint same-component now?"
(that is the one-step screen of Round 68) but "can any descendant of this state
present a same-component R joint at any depth?".

The answer turns out to be carried by a single integer already present in every
committed coordinate record, the window-capacity slack

    Phi(s) = 5 + 6*(TARGET_P - P(s)) - (720 - visited_count(s)),

which ``superperm_partial_f1_macro.remaining_window_capacity_prune`` requires to
be non-negative and which ``build_rr_target_a_roots.is_target_a`` therefore also
requires, because the recognizer calls ``area_a_prune_reason`` on its own child.

Sections
  1  Phi arithmetic and the forced rotation length (FRL).
  2  The incidence excess r = P - |T| and the bound 6r <= 11 - Phi.
  3  The incidence geometry B_full and the sigma-adjacency admissibility lemma.
  4  The short-root hub gap-run and the ell0 classification.
  5  Corpus application, if the Round-68 residual corpus is supplied.

Nothing here runs a continuation search.  Section 6 offers a BOUNDED forward
probe used only to try to falsify sections 1-4; it always reports whether it
terminated or hit its node cap, and it never claims exhaustion.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(name, fname):
    p = WORK / fname
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("cci_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
AREA_A = macro.AREA_A

N = core.N
NORB = len(core.E_REPS)
NHEX = len(core.ROT_REPS)
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]
PORT_HEX = [[core.hexagon_id(PORTS[q][ph]) for ph in range(N - 1)] for q in range(NORB)]
HUB = core.hexagon_id(exact.initial_state().p)
HUB_WINDOWS = core.orbit(core.ROT_REPS[HUB], core.SIGMA)

# the RR alphabet exactly as build_rr_target_a_roots.joint_kind defines it
KIND = {(2, False, False): "Z2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3"}
W3_MOVES = [m for m in exact.ALL_MOVES if m.weight == 3]
W2_MOVES = [m for m in exact.ALL_MOVES if m.weight == 2]
RR_MOVES = W2_MOVES + W3_MOVES


# --------------------------------------------------------------------------
# section 1: Phi arithmetic and the forced rotation length
# --------------------------------------------------------------------------
def phi(st) -> int:
    """Identical to build_rr_target_a_roots.phi; >= 0 is remaining_window_capacity_prune."""
    return 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count)


def forced_ell(st) -> int:
    """m - 1, with m = min{ j >= 1 : sigma^j(p) visited }.

    FRL: when F is already at TARGET_F, this is the ONLY rotation length whose
    joint keeps F, because ``extend`` sets abandonment = not visited(sigma(u))
    at the run end u, and dF = int(abandonment).
    """
    w = st.p
    for j in range(1, N + 1):
        w = core.word_after(w, core.SIGMA)
        if st.visited(w):
            return j - 1
    raise AssertionError("sigma^6(p) = p is always visited")


def touched_hexagons(st):
    return [h for h, m in enumerate(st.hex_masks) if m]


def incidence_excess(st) -> int:
    """r = P - |T| = sum over hexagon nodes of (degree - 1)."""
    return st.P - len(touched_hexagons(st))


def hexagon_degrees(st):
    deg = Counter()
    for q, m in enumerate(st.orbit_masks):
        for ph in range(N - 1):
            if m & (1 << ph):
                deg[PORT_HEX[q][ph]] += 1
    return deg


def component_forest(st):
    """The same forest build_rr_target_a_roots.component_forest uses."""
    par = {}

    def find(n):
        while par[n] != n:
            par[n] = par[par[n]]
            n = par[n]
        return n

    for q, m in enumerate(st.orbit_masks):
        if not m:
            continue
        par.setdefault(("q", q), ("q", q))
        for ph in range(N - 1):
            if m & (1 << ph):
                hn = ("h", PORT_HEX[q][ph])
                par.setdefault(hn, hn)
                a, b = find(("q", q)), find(hn)
                if a != b:
                    par[b] = a
    return par, find


def dead_permutations(st):
    """visited but never registered: no future joint can ever target them."""
    out = []
    for w in core.ALL_WORDS:
        if not st.visited(w):
            continue
        q, ph = exact.ORBIT_PHASE[w]
        if not (st.orbit_masks[q] & (1 << ph)):
            out.append(w)
    return out


# --------------------------------------------------------------------------
# section 3: incidence geometry and the sigma-adjacency admissibility lemma
# --------------------------------------------------------------------------
def build_geometry():
    adj = defaultdict(set)
    for q in range(NORB):
        for ph in range(N - 1):
            h = PORT_HEX[q][ph]
            adj[("q", q)].add(("h", h))
            adj[("h", h)].add(("q", q))

    def bfs(src):
        d = {src: 0}
        dq = deque([src])
        while dq:
            x = dq.popleft()
            for y in adj[x]:
                if y not in d:
                    d[y] = d[x] + 1
                    dq.append(y)
        return d

    dist = {q: bfs(("q", q)) for q in range(NORB)}
    w3_ord, w2_ord = set(), set()
    for w in core.ALL_WORDS:
        a = core.e_orbit_id(w)
        for m in W3_MOVES:
            w3_ord.add((a, core.e_orbit_id(core.word_after(w, m.action))))
        for m in W2_MOVES:
            w2_ord.add((a, core.e_orbit_id(core.word_after(w, m.action))))
    return adj, dist, w3_ord, w2_ord


def geometry_report():
    adj, dist, w3_ord, w2_ord = build_geometry()
    w3_pairs = {frozenset(p) for p in w3_ord}
    d2 = {frozenset((a, b)) for a in range(NORB) for b in range(NORB)
          if a < b and dist[a][("q", b)] == 2}
    # every macro generator sigma^ell . tail changes both the E orbit and the hexagon
    self_orbit = self_hex = 0
    for ell in range(N):
        rot = core.power(core.SIGMA, ell)
        for m in RR_MOVES:
            g = core.compose(rot, m.action)
            for w in core.ALL_WORDS:
                u = core.word_after(w, rot)
                v = core.word_after(w, g)
                self_orbit += int(core.e_orbit_id(u) == core.e_orbit_id(v))
                self_hex += int(core.hexagon_id(u) == core.hexagon_id(v))
    # sigma-adjacency lemma over every co-hexagonal port pair
    agree = disagree = 0
    tally = Counter()
    for h in range(NHEX):
        ws = core.orbit(core.ROT_REPS[h], core.SIGMA)
        for i in range(N):
            for j in range(i + 1, N):
                a, b = core.e_orbit_id(ws[i]), core.e_orbit_id(ws[j])
                rot = min((j - i) % N, (i - j) % N)
                adm = frozenset((a, b)) in w3_pairs
                tally[(rot, adm)] += 1
                if (rot == 1) == adm:
                    agree += 1
                else:
                    disagree += 1
    dd = Counter()
    for a, b in w3_ord:
        dd[dist[a][("q", b)]] += 1
    return {
        "orbit_nodes": NORB, "hexagon_nodes": NHEX, "incidence_edges": 720,
        "orbit_node_degree": sorted({len(adj[("q", q)]) for q in range(NORB)}),
        "hexagon_node_degree": sorted({len(adj[("h", h)]) for h in range(NHEX)}),
        "connected": len(build_geometry()[1][0]) == NORB + NHEX,
        "diameter": max(max(d.values()) for d in dist.values()),
        "macro_generators": 6 * len(RR_MOVES),
        "generator_orbit_fixed_points": self_orbit,
        "generator_hexagon_fixed_points": self_hex,
        "w3_ordered_orbit_pairs": len(w3_ord),
        "w3_ordered_pairs_by_incidence_distance": dict(sorted(dd.items())),
        "unordered_orbit_pairs_at_distance_2": len(d2),
        "distance_2_pairs_with_a_w3_transition": len(w3_pairs & d2),
        "distance_2_pairs_without_any_w3_transition": len(d2 - w3_pairs),
        "sigma_adjacency_lemma_agree": agree,
        "sigma_adjacency_lemma_disagree": disagree,
        "sigma_adjacency_tally": {f"rotdist={k[0]},admissible={k[1]}": v for k, v in sorted(tally.items())},
        "hub_hexagon": HUB,
        "hub_port_position_by_orbit": {core.e_orbit_id(w): i for i, w in enumerate(HUB_WINDOWS)},
        "hub_pairs_admissible": sorted(sorted(p) for p in
                                       ({frozenset((core.e_orbit_id(HUB_WINDOWS[i]), core.e_orbit_id(HUB_WINDOWS[j])))
                                         for i in range(N) for j in range(i + 1, N)} & w3_pairs)),
    }


def short_root_table():
    """Section 4: for each short-root rotation length, the whole future is decided."""
    rows = []
    for ell0 in range(0, N):
        head = ell0 + 1                      # first free hub position
        if head > N - 1:
            rows.append({"root_ell": ell0, "note": "no free hub position"})
            continue
        hub0 = core.e_orbit_id(HUB_WINDOWS[0])
        budget = ell0 + 1
        # a bridge is created by a joint into hub position g; g must be free
        # (g >= ell0+1) and the FOLLOWING macro edge then costs exactly g, so the
        # bridged state has a legal successor only when g <= Phi = ell0+1.
        # Both constraints together force g = ell0+1.
        entries = []
        for g in range(ell0 + 1, N):
            partner = core.e_orbit_id(HUB_WINDOWS[g])
            rot = min(g, N - g)
            entries.append({"hub_position": g, "bridged_pair": sorted((hub0, partner)),
                            "hub_rotation_distance": rot, "w3_admissible": rot == 1,
                            "cost_of_next_edge": g, "survivable": g <= budget,
                            "outcome": ("LIVE" if (g <= budget and rot == 1) else
                                        ("DEAD_END_no_legal_macro_edge" if g > budget
                                         else "SURVIVES_BUT_PAIR_HAS_NO_WEIGHT_3_TRANSITION"))})
        live = [e for e in entries if e["outcome"] == "LIVE"]
        rows.append({
            "root_ell": ell0,
            "root_phi": budget,
            "hub_dead_positions": list(range(1, ell0 + 1)),
            "hub_free_positions": list(range(ell0 + 1, N)),
            "forced_bridge_position": head,
            "bridged_pair": sorted((hub0, core.e_orbit_id(HUB_WINDOWS[head]))),
            "hub_rotation_distance": min(head, N - head),
            "w3_admissible": min(head, N - head) == 1,
            "bridge_entry_analysis": entries,
            "verdict": ("TARGET_A_REACHABLE_NOT_EXCLUDED" if live
                        else "PERMANENTLY_NO_SAME_COMPONENT_R_JOINT"),
        })
    return rows


# --------------------------------------------------------------------------
# section 6: bounded adversarial probe (never an exhaustion claim)
# --------------------------------------------------------------------------
def probe(root, node_cap=40000, seconds_cap=1e9, relaxed=False):
    def prune(st):
        if relaxed:
            if st.F > exact.TARGET_F: return "F_exceeded"
            if st.H > 0: return "H_positive"
            if st.P > exact.TARGET_P: return "P_exceeded"
            if st.O > exact.TARGET_O: return "O_exceeded"
            if st.Ndef > AREA_A.n_limit: return "N_exceeded_monotone"
            return None
        return macro.area_a_prune_reason(st, AREA_A)

    t0 = time.time()
    seen = {root.stable_key()}
    fr = deque([(root, 0)])
    n = maxd = 0
    r2 = Counter(); pairs = Counter(); ell_used = Counter()
    frl_bad = frl_ok = 0
    bridge_events = Counter(); nonvirgin = 0
    r_max = incidence_excess(root); deg_max = max(hexagon_degrees(root).values() or [0])
    status = "EXHAUSTED"
    while fr:
        if n >= node_cap:
            status = "NODE_CAP"; break
        if n % 512 == 0 and time.time() - t0 > seconds_cap:
            status = "TIME_CAP"; break
        cur, d = fr.popleft(); n += 1; maxd = max(maxd, d)
        ellmax = macro.rotation_runs(cur)[-1].ell
        for e in macro.macro_edges(cur):
            tr = e.joint
            if prune(tr.state) is not None:
                continue
            k = KIND.get((tr.move.weight, tr.abandonment, tr.new_orbit), "other")
            if k == "other":
                continue
            if e.run.ell == ellmax: frl_ok += 1
            else: frl_bad += 1
            ell_used[e.run.ell] += 1
            if k == "R":
                sq, _ = exact.ORBIT_PHASE[e.run.state.p]
                tq, _ = exact.ORBIT_PHASE[tr.target]
                par, find = component_forest(e.run.state)
                if ("q", sq) not in par or ("q", tq) not in par:
                    r2["source_or_target_orbit_not_in_forest"] += 1
                elif find(("q", sq)) != find(("q", tq)):
                    r2["different_components"] += 1
                else:
                    r2["SAME_COMPONENT"] += 1
                    pairs[tuple(sorted((sq, tq)))] += 1
                continue
            h = core.hexagon_id(tr.target)
            if cur.hex_masks[h] != 0:
                nonvirgin += 1
                deg = hexagon_degrees(tr.state)
                bridged = tuple(sorted(q for q in range(NORB) for ph in range(N - 1)
                                       if tr.state.orbit_masks[q] & (1 << ph) and PORT_HEX[q][ph] == h))
                survivors = sum(1 for e2 in macro.macro_edges(tr.state)
                                if prune(e2.joint.state) is None
                                and KIND.get((e2.joint.move.weight, e2.joint.abandonment,
                                              e2.joint.new_orbit), "other") != "other")
                pos = next((i for i, w in enumerate(HUB_WINDOWS) if w == tr.target), None)
                bridge_events[(h, pos, bridged, phi(cur), phi(tr.state), survivors)] += 1
                r_max = max(r_max, incidence_excess(tr.state))
                deg_max = max(deg_max, max(deg.values()))
            kk = tr.state.stable_key()
            if kk in seen:
                continue
            seen.add(kk); fr.append((tr.state, d + 1))
    return {
        "status": status, "exhaustion_claimed": status == "EXHAUSTED",
        "nodes_expanded": n, "frontier_left": len(fr), "max_depth": maxd,
        "R2_evaluations": dict(r2), "same_component_pairs": {str(k): v for k, v in pairs.items()},
        "rotation_lengths_used": dict(ell_used),
        "FRL_violations": frl_bad, "FRL_conforming": frl_ok,
        "nonvirgin_targets": nonvirgin,
        "bridge_events": {str(k): v for k, v in sorted(bridge_events.items(), key=str)},
        "max_incidence_excess_r": r_max, "max_hexagon_degree": deg_max,
        "seconds": round(time.time() - t0, 1),
    }


def state_from_sparse(js):
    hm = [0] * exact.HEX_COUNT
    om = [0] * exact.ORBIT_COUNT
    for i, m in js["hex_masks"]:
        hm[i] = m
    for i, m in js["orbit_masks"]:
        om[i] = m
    return exact.ExactState(tuple(js["p"]), tuple(hm), tuple(om),
                            F=js["F"], S=js["S"], H=js["H"])


def state_report(st):
    deg = hexagon_degrees(st)
    bridges = sorted(h for h, d in deg.items() if d >= 2)
    return {
        "p": list(st.p), "F": st.F, "S": st.S, "H": st.H, "P": st.P, "O": st.O,
        "Ndef": st.Ndef, "visited_count": st.visited_count, "phi": phi(st),
        "visited_identity_6P_plus_phi_minus_11": 6 * st.P + phi(st) - 11,
        "touched_hexagons": len(touched_hexagons(st)),
        "incidence_excess_r": incidence_excess(st),
        "bound_6r_le_11_minus_phi": 6 * incidence_excess(st) <= 11 - phi(st),
        "max_hexagon_degree": max(deg.values()),
        "bridge_hexagons": bridges,
        "bridged_orbits": [sorted(q for q in range(NORB) for ph in range(N - 1)
                                  if st.orbit_masks[q] & (1 << ph) and PORT_HEX[q][ph] == h)
                           for h in bridges],
        "current_hexagon_occupancy": bin(st.hex_masks[st.current_hex]).count("1"),
        "forced_ell": forced_ell(st),
        "gaps_outside_current": {h: N - bin(st.hex_masks[h]).count("1")
                                 for h in touched_hexagons(st)
                                 if h != st.current_hex and st.hex_masks[h] != exact.FULL_HEX},
        "dead_permutation_count": len(dead_permutations(st)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", nargs="*", default=[],
                    help="Round-68 residual corpus parts (optional)")
    ap.add_argument("--probe-cap", type=int, default=0,
                    help="if > 0, run the bounded adversarial probe with this node cap")
    ap.add_argument("--probe-seconds", type=float, default=60.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    report = {"schema": "rr-short-cocomponent-invariant-claude-v1",
              "engine_sha256": exact.CODE_SHA256, "core_sha256": exact.CORE_SHA256,
              "geometry": geometry_report(),
              "short_root_table": short_root_table()}

    states = []
    if args.corpus:
        anchors = []
        for f in args.corpus:
            d = json.load(open(f))
            for fam in d["families"]:
                for a in fam["anchors"]:
                    anchors.append((fam["mechanism_family"], a))
        report["corpus"] = {"anchors": len(anchors),
                            "phi_distribution": dict(sorted(Counter(a["coordinates"]["Phi"] for _, a in anchors).items())),
                            "root_ell_distribution": dict(sorted(Counter(a["canonical_decoration"]["root_ell"] for _, a in anchors).items()))}
        seen = {}
        for _, a in anchors:
            pv = a.get("first_R1_hub_merge_provenance")
            if not pv:
                continue
            st = state_from_sparse(pv["literal_child_state"])
            seen.setdefault(st.stable_key(), st)
        states = list(seen.values())
        report["certified_literal_post_R1_states"] = [state_report(s) for s in states]
        report["certified_states_all_satisfy_r_le_1"] = all(incidence_excess(s) <= 1 for s in states)

    if args.probe_cap and states:
        report["adversarial_probe"] = []
        for i, s in enumerate(states):
            r = probe(s, node_cap=args.probe_cap, seconds_cap=args.probe_seconds)
            r["root_index"] = i
            r["root_phi"] = phi(s)
            r["root_incidence_excess"] = incidence_excess(s)
            report["adversarial_probe"].append(r)
            print(f"[{i}] phi={r['root_phi']} r={r['root_incidence_excess']} {r['status']} "
                  f"n={r['nodes_expanded']} R2={r['R2_evaluations']} FRLviol={r['FRL_violations']} "
                  f"maxr={r['max_incidence_excess_r']}", flush=True)

    text = json.dumps(report, indent=1, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text)
        print("wrote", args.out)
    else:
        print(text[:4000])


if __name__ == "__main__":
    main()
