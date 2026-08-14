#!/usr/bin/env python3
"""Standalone verifier for the Round-79 SLACK-COVER audit archive.

Deliberately depends on NOTHING from this repository -- only the Python standard library --
so an independent auditor can replay the Round-79 state counts without running, trusting or
even reading the search implementation.  Point it at the archive directory:

    python3 src/verify_rr_slack_cover_archive.py --archive outputs/rr_slack_cover_archive

It checks, in order:

  1. the incidence table is the biregular 144x120 system it claims to be, with every orbit
     block re-derived from the listed port permutations and hexagon window lists;
  2. every state row is internally consistent -- C is exactly the union of the open orbits'
     blocks, U is its complement, c = 5*O - |C|, b = 5 - c, K = 25 - O, |U| = 5K - b -- and
     its ``iid`` points at an instance with the same (U, b);
  3. every instance row's candidate family is exactly the set of orbits with
     |block & U| >= 5 - b, those orbits are closed in every source state mapping to the
     instance, and the state_ids mapping agrees with the states file in both directions;
  4. every SAT witness is K candidate blocks covering U with excess exactly b;
  5. the per-band and total counts, and the final residual once the c = 5 survivors are
     added back.

It does NOT re-decide UNSAT instances -- that requires a solver and is exactly the part an
independent auditor should implement themselves.  Every UNSAT row carries the U mask and the
candidate blocks needed to do so.
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

N_ORBITS = 144
N_HEXAGONS = 120
TARGET_O = 25

CLAIMED_BANDS = {
    1: dict(states=1001, closed=0, sat=1001),
    2: dict(states=5369, closed=2151, sat=3218),
    3: dict(states=13446, closed=11795, sat=1651),
    4: dict(states=24834, closed=24195, sat=639),
}
CLAIMED_TOTAL = dict(states=44650, closed=38141, sat=6509,
                     instances=43643, c5_survivors=148, residual=6657)


def read_jsonl(path: Path):
    with gzip.open(path, "rt") as fh:
        header = json.loads(fh.readline())
        for line in fh:
            yield header, json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", default="outputs/rr_slack_cover_archive")
    ap.add_argument("--out")
    args = ap.parse_args()
    arc = Path(args.archive)
    problems = []

    def bad(msg):
        problems.append(msg)

    # ---- 1. incidence table ----
    table = json.loads((arc / "incidence_table.json").read_text())
    if len(table["orbits"]) != N_ORBITS or len(table["hexagons"]) != N_HEXAGONS:
        bad("incidence table has the wrong number of orbits or hexagons")
    window_hex = {}
    for row in table["hexagons"]:
        if len(row["windows"]) != 6 or len(set(row["windows"])) != 6:
            bad(f"hexagon {row['hexagon']} does not hold 6 distinct windows")
        for w in row["windows"]:
            window_hex[w] = row["hexagon"]
    if len(window_hex) != 720:
        bad(f"hexagon windows cover {len(window_hex)} permutations, expected 720")
    block = {}
    port_count = Counter()
    for row in table["orbits"]:
        q = row["orbit"]
        if len(row["ports"]) != 5:
            bad(f"orbit {q} does not hold 5 ports")
        derived = [window_hex[w] for w in row["ports"]]
        if derived != row["block"]:
            bad(f"orbit {q} block disagrees with the hexagon window lists")
        if len(set(derived)) != 5:
            bad(f"orbit {q} block is not 5 distinct hexagons")
        block[q] = 0
        for h in derived:
            block[q] |= 1 << h
            port_count[h] += 1
    if set(port_count.values()) != {6}:
        bad("the incidence system is not 6-regular on hexagons")
    print(f"1. incidence table: {len(block)} orbits x 5 hexagons, "
          f"{sum(port_count.values())} incidences, "
          f"orbits per hexagon {sorted(set(port_count.values()))}")

    def pc(x):
        return bin(x).count("1")

    ALL = (1 << N_HEXAGONS) - 1

    # ---- 2/3. instances ----
    inst = {}
    inst_states = {}
    n_inst = 0
    for header, row in read_jsonl(arc / "instances.jsonl.gz"):
        n_inst += 1
        U = int(row["U"], 16)
        b, K = row["b"], row["K"]
        if pc(U) != 5 * K - b:
            bad(f"instance {row['iid']}: |U| != 5K - b")
        if row["c"] != 5 - b:
            bad(f"instance {row['iid']}: c != 5 - b")
        want = [q for q in range(N_ORBITS) if pc(block[q] & U) >= 5 - b]
        if row["candidate_orbits"] != want:
            bad(f"instance {row['iid']}: candidate family does not match |block & U| >= 5-b")
        for q, blk in zip(row["candidate_orbits"], row["candidate_blocks"]):
            if sum(1 << h for h in blk) != block[q]:
                bad(f"instance {row['iid']}: candidate block for orbit {q} is wrong")
        if row["n_states"] != len(row["state_ids"]):
            bad(f"instance {row['iid']}: n_states disagrees with state_ids")
        if row["sat"] != (row["verdict"] == "SAT"):
            bad(f"instance {row['iid']}: sat flag disagrees with verdict")
        if row["sat"]:
            w = row["witness_orbits"]
            if w is None or len(w) != K:
                bad(f"instance {row['iid']}: SAT witness is not K orbits")
            else:
                if not set(w) <= set(row["candidate_orbits"]):
                    bad(f"instance {row['iid']}: witness uses a non-candidate orbit")
                union = 0
                for q in w:
                    union |= block[q]
                if U & ~union:
                    bad(f"instance {row['iid']}: witness does not cover U")
                excess = 5 * K - pc(union & U)
                if excess != b:
                    bad(f"instance {row['iid']}: witness excess {excess} != b {b}")
        elif not row["verdict"].startswith("UNSAT"):
            bad(f"instance {row['iid']}: verdict {row['verdict']} is neither SAT nor UNSAT")
        inst[row["iid"]] = (row["U"], b, row["sat"], row["verdict"], K)
        inst_states[row["iid"]] = set(row["state_ids"])
    print(f"2. instances: {n_inst} rows, "
          f"{sum(1 for v in inst.values() if v[2])} SAT, "
          f"{sum(1 for v in inst.values() if not v[2])} UNSAT")

    # ---- 3. states ----
    seen = set()
    bands = defaultdict(Counter)
    mapped = defaultdict(set)
    n_states = 0
    for header, row in read_jsonl(arc / "states.jsonl.gz"):
        n_states += 1
        sid = row["sid"]
        if sid in seen:
            bad(f"duplicate state id {sid}")
        seen.add(sid)
        C, U, openm = int(row["C"], 16), int(row["U"], 16), int(row["open_orbits"], 16)
        O = pc(openm)
        derived_C = 0
        for q in range(N_ORBITS):
            if openm >> q & 1:
                derived_C |= block[q]
        if derived_C != C:
            bad(f"state {sid}: C is not the union of the open orbits' blocks")
        if U != (ALL ^ C):
            bad(f"state {sid}: U is not the complement of C")
        if O != row["O"] or row["K"] != TARGET_O - O:
            bad(f"state {sid}: O/K disagree with the open-orbit mask")
        c = 5 * O - pc(C)
        if c != row["c"] or row["b"] != 5 - c:
            bad(f"state {sid}: c/b disagree with 5*O - |C|")
        if pc(U) != 5 * row["K"] - row["b"]:
            bad(f"state {sid}: |U| != 5K - b")
        iid = row["iid"]
        if iid not in inst or inst[iid][0] != row["U"] or inst[iid][1] != row["b"]:
            bad(f"state {sid}: iid does not point at a matching (U, b) instance")
        else:
            # every candidate orbit of the instance must be CLOSED in this state
            if openm & sum(1 << q for q in range(N_ORBITS)
                           if pc(block[q] & U) >= 5 - row["b"]):
                bad(f"state {sid}: an open orbit appears in the candidate family")
            bands[c]["states"] += row.get("weight", 1)
            bands[c]["sat" if inst[iid][2] else "closed"] += row.get("weight", 1)
            mapped[iid].add(sid)
    for iid, sids in inst_states.items():
        if mapped.get(iid, set()) != sids:
            bad(f"instance {iid}: state_ids mapping disagrees with the states file")
    print(f"3. states: {n_states} rows, {len(seen)} distinct ids, "
          f"{len(mapped)} instances referenced")

    # ---- 4. c = 5 survivors ----
    n_c5 = 0
    for header, row in read_jsonl(arc / "collision5_survivors.jsonl.gz"):
        n_c5 += 1
        if row["c"] != 5 or row["b"] != 0:
            bad(f"c=5 survivor {row['sid']}: c/b wrong")
        if pc(int(row["U"], 16)) != 5 * row["K"]:
            bad(f"c=5 survivor {row['sid']}: |U| != 5K at b = 0")
        if row["sid"] in seen:
            bad(f"c=5 survivor {row['sid']} also appears in the c<=4 ledger")

    # ---- 5. replay the counts ----
    print("\n5. count replay (archive only, no frontier, no search):")
    print(f"   {'band':>6} {'states':>8} {'closed':>8} {'SAT':>7}   claimed")
    totals = Counter()
    for c in (4, 3, 2, 1):
        got = dict(states=bands[c]["states"], closed=bands[c]["closed"], sat=bands[c]["sat"])
        want = CLAIMED_BANDS[c]
        ok = got == want
        for k in got:
            totals[k] += got[k]
        print(f"   c={c:<4} {got['states']:>8} {got['closed']:>8} {got['sat']:>7}   "
              f"{want}  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            bad(f"band c={c}: replayed {got}, claimed {want}")
    totals["instances"] = n_inst
    totals["c5_survivors"] = n_c5
    totals["residual"] = totals["sat"] + n_c5
    print(f"   {'TOTAL':>6} {totals['states']:>8} {totals['closed']:>8} {totals['sat']:>7}")
    print(f"   instances {totals['instances']}, c=5 survivors {totals['c5_survivors']}, "
          f"residual {totals['residual']}")
    for k, v in CLAIMED_TOTAL.items():
        if totals[k] != v:
            bad(f"total {k}: replayed {totals[k]}, claimed {v}")

    print("\n" + ("VERIFIED - archive is internally consistent and replays every claimed count"
                  if not problems else f"PROBLEMS: {len(problems)}"))
    for p in problems[:20]:
        print("  -", p)
    if args.out:
        Path(args.out).write_text(json.dumps(
            dict(problems=problems, totals=dict(totals),
                 per_band={str(c): dict(bands[c]) for c in sorted(bands)}), indent=1))
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
