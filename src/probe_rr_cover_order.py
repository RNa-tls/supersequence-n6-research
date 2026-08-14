#!/usr/bin/env python3
"""Round 81 — can a statically feasible final orbit set actually be OPENED in a legal order?

Round 79's SLACK-COVER decides *which* K closed orbits could form the final set.  It says
nothing about whether they can be reached.  This module adds the weakest sound ordering
condition on top, reading the residual entirely from the Round-80 archive: no frontier
access, no continuation search.

THE CONSERVATIVE OPENING RELATION.  For orbits q != r,

    q -> r   iff   there exist a phase f in {0..4}, a rotation-run length l in {0..5} and a
                   non-rotation joint a in {w2:10, w3:120, w3:201, w3:210} such that
                   word_after(sigma^l(port(q, f)), a) is a port of r.

*It is an over-approximation.*  Any genuine opening of r from q is, in the engine, a macro
edge taken from the walk's endpoint p in orbit q: l rotations followed by one non-rotation
joint whose target lies in r.  The engine imposes strictly more conditions than the relation
above -- every rotation target must be unvisited, the joint target must be unvisited, the
resulting F/H/P/O/Ndef coordinates must survive ``area_a_prune_reason``, and the endpoint
occupies one specific phase.  Every one of those is dropped here, and the phase is
existentially quantified over all five, which in particular allows arbitrary legal ``E^1``
closure beforehand.  Dropping conditions only adds edges, so no genuinely possible opening
is omitted.

*Excluded edges are excluded by exhaustion over the group action, not by absence from a
search.*  From orbit q the 5 phases x 6 rotation lengths x 4 joints give a fixed multiset of
120 target permutations, computed here in full; an orbit not represented in it cannot be
entered from q by any single macro edge whatsoever.  Nothing about visitation, resources or
history enters that statement.

*No weight-2 exclusion is made.*  A weight-2 joint into a fresh orbit is a legal engine
transition (``extend`` classifies abandonment and new_orbit independently and gates neither),
so ``w2:10`` stays in the joint set even though at l = 5 it is the orbit-preserving ``E^1``.

WHAT IS TESTED.  Only orbits in the slack-cover candidate family can ever be opened -- opening
any other would exceed the collision budget -- and the walk only ever occupies open orbits.
So with R initialised to the currently-open set (itself an over-approximation: not every open
orbit need be reachable from the endpoint), R grows by candidates having an in-edge from R,
and a completion needs a K-orbit slack cover entirely inside the fixpoint.

Subcommands: ``relation`` (statistics + excluded-edge audit), ``census`` (stages A-C).
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
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
NORB, NHEX = slack.NORB, slack.NHEX
BLOCKBITS = slack.BLOCKBITS
pc = int.bit_count
ALLHEX = slack.ALLHEX
ARCHIVE = ROOT / "outputs" / "rr_slack_cover_archive"


def build_relation():
    """EDGE[q] = 144-bit mask of orbits reachable from q by one macro edge, any phase."""
    sigma = core.SIGMA
    ports = [core.orbit(core.E_REPS[q], core.E) for q in range(NORB)]
    orbit_of = {w: exact.ORBIT_PHASE[w][0] for w in core.ALL_WORDS}
    edge = [0] * NORB
    targets = [Counter() for _ in range(NORB)]
    for q in range(NORB):
        for w in ports[q]:
            cur = w
            for _ in range(6):
                for move in macro.NONROT_H0:
                    r = orbit_of[core.word_after(cur, move.action)]
                    targets[q][r] += 1
                    if r != q:
                        edge[q] |= 1 << r
                cur = core.word_after(cur, sigma)
    return edge, targets


def relation_report() -> dict:
    edge, targets = build_relation()
    out_deg = [pc(e) for e in edge]
    indeg = Counter()
    for q in range(NORB):
        for r in range(NORB):
            if edge[q] >> r & 1:
                indeg[r] += 1
    per_q_targets = [sum(targets[q].values()) for q in range(NORB)]
    return dict(
        nodes=NORB,
        combinations_per_orbit="5 phases x 6 rotation lengths x 4 joints = 120 target permutations",
        target_multiset_size=sorted(set(per_q_targets)),
        out_degree=dict(sorted(Counter(out_deg).items())),
        in_degree=dict(sorted(Counter(indeg.values()).items())),
        ordered_pairs_with_an_edge=sum(out_deg),
        ordered_pairs_total=NORB * (NORB - 1),
        excluded_pairs=NORB * (NORB - 1) - sum(out_deg),
        exclusion_justification=(
            "an excluded (q,r) means r appears nowhere in the 120-element target multiset of "
            "q under the full macro generator set; this is exhaustion over the fixed group "
            "action, independent of visitation, resources and history"),
    )


def read_jsonl(path):
    with gzip.open(path, "rt") as fh:
        fh.readline()
        for line in fh:
            yield json.loads(line)


def load_residual():
    """The 6,657 audited residual states, straight from the Round-80 archive."""
    inst = {}
    for row in read_jsonl(ARCHIVE / "instances.jsonl.gz"):
        inst[row["iid"]] = row
    states = []
    for row in read_jsonl(ARCHIVE / "states.jsonl.gz"):
        i = inst[row["iid"]]
        if not i["sat"]:
            continue
        states.append(dict(sid=row["sid"], root=row["root"], c=row["c"], b=row["b"],
                           K=row["K"], O=row["O"], Ndef=row["Ndef"], Phi=row["Phi"],
                           U=int(row["U"], 16), open_orbits=int(row["open_orbits"], 16),
                           candidates=i["candidate_orbits"]))
    for row in read_jsonl(ARCHIVE / "collision5_survivors.jsonl.gz"):
        U = int(row["U"], 16)
        states.append(dict(sid=row["sid"], root=row["root"], c=5, b=0, K=row["K"],
                           O=row["O"], Ndef=row["Ndef"], Phi=row["Phi"], U=U,
                           open_orbits=int(row["open_orbits"], 16),
                           candidates=[q for q in range(NORB) if BLOCKBITS[q] & ~U == 0]))
    return states


def census() -> dict:
    edge, _ = build_relation()
    states = load_residual()
    print(f"residual loaded from the archive: {len(states)} states", flush=True)
    ndef = Counter(s["Ndef"] for s in states)
    print(f"Ndef distribution (verified from the preserved ledger): {dict(ndef)}", flush=True)

    agg = Counter()
    first_open_counts = Counter()
    reach_frac = Counter()
    lost_candidates = Counter()
    by_root_closed = Counter()
    for n, s in enumerate(states):
        cand = set(s["candidates"])
        openm = s["open_orbits"]
        # ---- stage B: first-open feasibility ----
        reachable_now = 0
        for q in range(NORB):
            if openm >> q & 1:
                reachable_now |= edge[q]
        first = {r for r in cand if reachable_now >> r & 1}
        first_open_counts[min(len(first), 60)] += 1
        if not first:
            agg["closed_first_open"] += 1
            by_root_closed[s["root"]] += 1
            continue
        # ---- stage C: iterated cover-compatible reachability ----
        R = openm
        frontier = first
        reached = set()
        while frontier:
            nxt = set()
            for r in frontier:
                if R >> r & 1:
                    continue
                R |= 1 << r
                reached.add(r)
                for t in cand:
                    if t not in reached and (edge[r] >> t & 1):
                        nxt.add(t)
            frontier = {t for t in nxt if not (R >> t & 1)}
        usable = sorted(reached)
        lost = len(cand) - len(usable)
        lost_candidates[min(lost, 20)] += 1
        reach_frac[round(100 * len(usable) / max(len(cand), 1) / 10) * 10] += 1
        if lost == 0:
            agg["survives_all_candidates_reachable"] += 1
            continue
        # re-decide the slack cover restricted to the reachable candidates
        keep = set(usable)
        rec = decide_restricted(s["U"], s["K"], s["b"], keep)
        if rec == "UNSAT":
            agg["closed_reachable_cover"] += 1
            by_root_closed[s["root"]] += 1
        elif rec == "UNKNOWN":
            agg["UNKNOWN"] += 1
        else:
            agg["survives_restricted_cover"] += 1
        if (n + 1) % 2000 == 0:
            print(f"  {n+1}/{len(states)} {dict(agg)}", flush=True)

    survivors = agg["survives_all_candidates_reachable"] + agg["survives_restricted_cover"]
    return dict(
        input_states=len(states),
        Ndef_distribution=dict(ndef),
        closed_first_open=agg["closed_first_open"],
        closed_reachable_cover=agg["closed_reachable_cover"],
        unknown=agg["UNKNOWN"],
        survivors=survivors,
        survivors_with_every_candidate_reachable=agg["survives_all_candidates_reachable"],
        survivors_with_some_candidate_unreachable=agg["survives_restricted_cover"],
        first_open_candidate_count_histogram=dict(sorted(first_open_counts.items())),
        unreachable_candidate_histogram=dict(sorted(lost_candidates.items())),
        reachable_candidate_percentage_histogram=dict(sorted(reach_frac.items())),
        closed_by_root=dict(by_root_closed),
    )


def decide_restricted(U, K, b, keep):
    """Slack-cover decision using only the orbits in ``keep``."""
    saved = slack.BLOCKBITS[:]
    try:
        for q in range(NORB):
            if q not in keep:
                slack.BLOCKBITS[q] = 0        # a zero block never qualifies as a candidate
        rec = slack.decide(U, K, b)
    finally:
        slack.BLOCKBITS[:] = saved
    v = rec["verdict"]
    return "SAT" if v == "SAT" else ("UNKNOWN" if v.startswith("UNKNOWN") else "UNSAT")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("relation", "census"))
    ap.add_argument("--out")
    args = ap.parse_args()
    result = {args.command: relation_report() if args.command == "relation" else census()}
    print(json.dumps(result[args.command], indent=1)[:4000])
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
