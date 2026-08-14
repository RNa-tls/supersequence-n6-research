#!/usr/bin/env python3
"""Round 82 — how much legal E^1 phase repair survives port occupancy?

Round 81 located the wall: the ``(orbit, phase)`` opening relation has out-degree 17 against
55, and some phases can open nothing, but ``E^1`` advances the phase for free so no sound
relation may pin a phase.  This module asks the only question that can unpin it -- how far
``E^1`` can actually walk given the literal no-repeat rule.

The residual states are fetched by their Round-80 provenance (`root`, `idx`) directly out of
the stored checkpoint frontiers.  That is a lookup of preserved data, not a frontier replay:
nothing is expanded, searched or re-generated.

DEFINITIONS, all literal.

  ``E^1`` is the macro edge (ell = 5, w2:10) and ``E^2`` is (ell = 5, w3:120).  Both need a
  full five-step rotation run, which is legal exactly when the current hexagon holds only the
  endpoint, and both need their joint target unvisited.  Both preserve the orbit; ``E^1``
  advances the phase by +1 and ``E^2`` by +2.

  ``PhaseClosure(s)`` -- the positions of ``q0`` reachable from the endpoint by any sequence
  of orbit-preserving macro edges.  Until the walk leaves ``q0`` these are the only moves it
  has, so the first orbit-changing edge of any continuation departs from a position in this
  set.  Computed with the exact engine predicates; ``E^2`` is included because every residual
  state has ``Ndef = 0`` and so can afford it.

  ``NEXT(s)`` -- closed cover-candidate orbits openable by one macro edge.  Two versions are
  reported and they must not be confused:

    NEXT_pinned  from the positions of PhaseClosure(s) only.  This is the quantity the phase
                 refinement would buy, and it is a DIAGNOSTIC -- using it to close a state
                 would be unsound, because the walk may instead re-enter another already-open
                 orbit first and open from there.

    NEXT_sound   the above, plus everything openable from any already-open orbit reachable
                 through open orbits, with the arrival phase over-approximated to all five.
                 Only this version may close a state.

Cover compatibility of a candidate ``q`` is decided exactly: force ``q`` into the cover and
re-decide the Round-79 instance on ``U \\ block(q)`` with ``K - 1`` blocks and slack
``b - waste(q)``.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "prove_rr_slack_cover", ROOT / "src" / "prove_rr_slack_cover.py")
slack = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = slack
_SPEC.loader.exec_module(slack)

macro = slack.macro
exact = slack.exact
core = slack.core
AREA_A = slack.AREA_A
NORB, NHEX = slack.NORB, slack.NHEX
BLOCKBITS = slack.BLOCKBITS
pc = int.bit_count
ARCHIVE = ROOT / "outputs" / "rr_slack_cover_archive"

W2 = next(m for m in macro.NONROT_H0 if m.label == "w2:10")
W3_120 = next(m for m in macro.NONROT_H0 if m.label == "w3:120")
PORTS = [core.orbit(core.E_REPS[q], core.E) for q in range(NORB)]
ORBIT_OF = {w: exact.ORBIT_PHASE[w][0] for w in core.ALL_WORDS}


def phase_relation():
    """PEDGE[(q,f)] = 144-bit mask of orbits reachable in one macro edge from that position."""
    out = {}
    for q in range(NORB):
        for f, w in enumerate(PORTS[q]):
            mask = 0
            cur = w
            for _ in range(6):
                for mv in macro.NONROT_H0:
                    r = ORBIT_OF[core.word_after(cur, mv.action)]
                    if r != q:
                        mask |= 1 << r
                cur = core.word_after(cur, core.SIGMA)
            out[(q, f)] = mask
    return out


def orbit_relation(pedge):
    edge = [0] * NORB
    for (q, _f), m in pedge.items():
        edge[q] |= m
    return edge


# --------------------------------------------------------------- literal E^1/E^2


def orbit_preserving_steps(state, allow_e2=True):
    """The literal E^1 / E^2 children of ``state``, or an empty list.

    Uses the engine itself: a full rotation run must be available (``ell == 5``), which the
    no-repeat rule permits exactly when the current hexagon holds only the endpoint, and the
    joint target must be unvisited.
    """
    runs = macro.rotation_runs(state)
    if runs[-1].ell != 5:
        return []
    out = []
    for label, move in (("E1", W2),) + ((("E2", W3_120),) if allow_e2 else ()):
        tr = exact.extend(runs[-1].state, move)
        if tr is not None:
            out.append((label, tr.state))
    return out


def phase_closure(state, allow_e2=True, apply_area_a=False):
    """All (phase, state) positions of q0 reachable by orbit-preserving macro edges."""
    q0, f0 = exact.ORBIT_PHASE[state.p]
    seen = {f0: state}
    order = [(f0, state)]
    stack = [state]
    chain = 0
    while stack:
        cur = stack.pop()
        for label, nxt in orbit_preserving_steps(cur, allow_e2):
            if apply_area_a and macro.area_a_prune_reason(nxt, AREA_A) is not None:
                continue
            q1, f1 = exact.ORBIT_PHASE[nxt.p]
            if q1 != q0 or f1 in seen:
                continue
            seen[f1] = nxt
            order.append((f1, nxt))
            stack.append(nxt)
            chain += 1
    return q0, seen, chain


def e1_chain_length(state, apply_area_a=False):
    """Maximal number of consecutive literal E^1 steps (Round-77 comparison)."""
    n = 0
    cur = state
    while n < 10:
        steps = orbit_preserving_steps(cur, allow_e2=False)
        if not steps:
            break
        nxt = steps[0][1]
        if apply_area_a and macro.area_a_prune_reason(nxt, AREA_A) is not None:
            break
        cur = nxt
        n += 1
    return n


# ------------------------------------------------------------------- cover tests


def cover_with(U, K, b, q):
    """Is there a valid slack cover containing orbit q?  Exact, via the Round-79 decider."""
    inU = pc(BLOCKBITS[q] & U)
    waste = 5 - inU
    if waste > b:
        return False
    U2 = U & ~BLOCKBITS[q]
    K2, b2 = K - 1, b - waste
    if K2 == 0:
        return U2 == 0
    if pc(U2) != 5 * K2 - b2:
        return False
    return slack.decide(U2, K2, b2)["verdict"] == "SAT"


# ------------------------------------------------------------------------ census


def load_states():
    """Residual rows from the archive, joined to their literal checkpoint states."""
    inst = {r["iid"]: r for r in _jsonl(ARCHIVE / "instances.jsonl.gz")}
    rows = []
    for r in _jsonl(ARCHIVE / "states.jsonl.gz"):
        i = inst[r["iid"]]
        if not i["sat"]:
            continue
        rows.append(dict(sid=r["sid"], root=r["root"], idx=r["idx"], c=r["c"], b=r["b"],
                         K=r["K"], O=r["O"], Ndef=r["Ndef"], U=int(r["U"], 16),
                         open_orbits=int(r["open_orbits"], 16),
                         candidates=i["candidate_orbits"]))
    for r in _jsonl(ARCHIVE / "collision5_survivors.jsonl.gz"):
        U = int(r["U"], 16)
        rows.append(dict(sid=r["sid"], root=r["root"], idx=r["idx"], c=5, b=0, K=r["K"],
                         O=r["O"], Ndef=r["Ndef"], U=U,
                         open_orbits=int(r["open_orbits"], 16),
                         candidates=[q for q in range(NORB) if BLOCKBITS[q] & ~U == 0]))
    by_root = defaultdict(dict)
    for r in rows:
        by_root[r["root"]][r["idx"]] = r
    for path in sorted(glob.glob(str(ROOT / "outputs" / "rr_target_a_checkpoints" / "*.json"))):
        root = os.path.basename(path)[:-5]
        if root not in by_root:
            continue
        data = json.load(open(path))
        for idx, r in by_root[root].items():
            st = data["frontier"][idx]["state"]
            r["state"] = exact.ExactState(tuple(st["p"]), tuple(st["hex_masks"]),
                                          tuple(st["orbit_masks"]),
                                          F=st["F"], S=st["S"], H=st["H"])
        del data
        print(f"  loaded {len(by_root[root])} literal states from {root}", flush=True)
    return [r for r in rows if "state" in r]


def _jsonl(path):
    with gzip.open(path, "rt") as fh:
        fh.readline()
        for line in fh:
            yield json.loads(line)


def census(limit=None) -> dict:
    pedge = phase_relation()
    edge = orbit_relation(pedge)
    rows = load_states()
    if limit:
        rows = rows[:limit]
    print(f"literal states loaded: {len(rows)}", flush=True)

    stats = Counter()
    closure_hist = Counter()
    e1_chain = Counter()
    e1_chain_areaa = Counter()
    next_pinned_hist = Counter()
    next_sound_hist = Counter()
    pinned_dead = Counter()
    cur_phase_dead = Counter()
    by_c = defaultdict(Counter)
    witnesses = []
    engine_check = Counter()

    for n, r in enumerate(rows):
        s = r["state"]
        cand = set(r["candidates"])
        # --- literal E^1 / E^2 phase closure ---
        q0, closure, _ = phase_closure(s, allow_e2=True, apply_area_a=False)
        closure_hist[len(closure)] += 1
        e1_chain[e1_chain_length(s, apply_area_a=False)] += 1
        e1_chain_areaa[e1_chain_length(s, apply_area_a=True)] += 1
        # engine cross-check: every position in the closure must really be an engine child
        engine_check["positions"] += len(closure)
        # --- NEXT_pinned: openings from q0's reachable phases only ---
        pinned = 0
        for f in closure:
            pinned |= pedge[(q0, f)]
        next_pinned = {q for q in cand if pinned >> q & 1}
        next_pinned_hist[min(len(next_pinned), 80)] += 1
        # is the CURRENT phase alone dead, and does E^1/E^2 repair it?
        f0 = exact.ORBIT_PHASE[s.p][1]
        cur_only = {q for q in cand if pedge[(q0, f0)] >> q & 1}
        if not cur_only:
            cur_phase_dead["current_phase_has_no_candidate"] += 1
            if next_pinned:
                cur_phase_dead["repaired_by_phase_closure"] += 1
        # --- NEXT_sound: allow re-entry through reachable open orbits ---
        openm = r["open_orbits"]
        reach_open = 1 << q0
        frontier = [q0]
        while frontier:
            nxt = []
            for q in frontier:
                m = pinned if q == q0 else edge[q]
                for t in range(NORB):
                    if (m >> t & 1) and (openm >> t & 1) and not (reach_open >> t & 1):
                        reach_open |= 1 << t
                        nxt.append(t)
            frontier = nxt
        sound = pinned
        for q in range(NORB):
            if (reach_open >> q & 1) and q != q0:
                sound |= edge[q]
        next_sound = {q for q in cand if sound >> q & 1}
        next_sound_hist[min(len(next_sound), 80)] += 1

        # --- classification (only the sound version may close) ---
        if not closure:
            cls = "no_legal_phase"
        elif not next_sound:
            cls = "no_fresh_orbit_openable"
        else:
            ok = next(( q for q in sorted(next_sound)
                        if cover_with(r["U"], r["K"], r["b"], q) ), None)
            if ok is None:
                cls = "openable_but_no_valid_cover"
            else:
                cls = "cover_compatible_next_opening"
                if len(witnesses) < 40:
                    witnesses.append(dict(sid=r["sid"], root=r["root"], c=r["c"],
                                          closure=sorted(closure), witness_orbit=ok,
                                          next_pinned=len(next_pinned),
                                          next_sound=len(next_sound)))
        stats[cls] += 1
        by_c[r["c"]][cls] += 1
        if not next_pinned:
            pinned_dead["pinned_next_empty"] += 1
        if (n + 1) % 1000 == 0:
            print(f"  {n+1}/{len(rows)} {dict(stats)}", flush=True)

    closed = stats["no_legal_phase"] + stats["no_fresh_orbit_openable"] + \
        stats["openable_but_no_valid_cover"]
    return dict(
        input_states=len(rows),
        classification=dict(stats),
        closed=closed,
        survivors=stats["cover_compatible_next_opening"],
        phase_closure_size_histogram=dict(sorted(closure_hist.items())),
        e1_only_chain_length_histogram=dict(sorted(e1_chain.items())),
        e1_chain_length_with_area_a_prune=dict(sorted(e1_chain_areaa.items())),
        next_pinned_histogram=dict(sorted(next_pinned_hist.items())),
        next_sound_histogram=dict(sorted(next_sound_hist.items())),
        current_phase_diagnostics=dict(cur_phase_dead),
        pinned_next_empty=dict(pinned_dead),
        by_collision_count={str(k): dict(v) for k, v in sorted(by_c.items())},
        witnesses=witnesses,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("census",))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out")
    args = ap.parse_args()
    res = census(args.limit)
    print(json.dumps({k: v for k, v in res.items() if k != "witnesses"}, indent=1)[:5000])
    if args.out:
        json.dump(res, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
