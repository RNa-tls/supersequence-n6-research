#!/usr/bin/env python3
"""Round 80 — export the Round-79 SLACK-COVER audit archive.

Round 79 reported 38,141 closed / 6,657 residual but preserved only aggregate counters, so
the counts could not be replayed independently.  This module re-derives the Round-79 census
from the stored checkpoint frontiers (a read-only pass; no search, no expansion, no state is
re-generated) and writes a self-contained archive an independent verifier can consume
without importing anything from this repository:

  incidence_table.json          orbit/hexagon numbering pinned to explicit permutations,
                                plus the 144 five-hexagon blocks
  states.jsonl.gz               one row per processed c in {1,2,3,4} state (44,650 expected)
  instances.jsonl.gz            one row per distinct (U, b) slack-cover instance, SAT and
                                UNSAT alike, with candidate blocks and a witness for SAT
  collision5_survivors.jsonl.gz the 148 Round-78 c = 5 SAT states carried through untouched
  SCHEMA.md                     bit numbering, field meanings, replay recipe

The per-instance verdicts are recomputed here with ``prove_rr_slack_cover.decide`` so the
archive records *which* test fired, not merely SAT/UNSAT; the aggregate is compared against
the Round-79 report and any difference is reported rather than silently absorbed.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
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
TP, TO, TD = slack.TP, slack.TO, slack.TD
NLIM = slack.NLIM
BLOCKBITS = slack.BLOCKBITS
PORT_HEXBIT = slack.PORT_HEXBIT
PORT_HEX = slack.PORT_HEX
pc = int.bit_count
ALLHEX = slack.ALLHEX

SCHEMA_VERSION = "rr-slack-cover-archive-v1"

# Round-79's reported figures, asserted rather than assumed.
EXPECTED = {
    1: dict(states=1001, closed=0, sat=1001),
    2: dict(states=5369, closed=2151, sat=3218),
    3: dict(states=13446, closed=11795, sat=1651),
    4: dict(states=24834, closed=24195, sat=639),
}
EXPECTED_TOTAL = dict(states=44650, closed=38141, sat=6509,
                      instances=43643, c5_survivors=148, residual=6657)


def state_id(p, hex_masks, orbit_masks, F, S, H) -> str:
    """Stable identifier: sha256 over a canonical, documented text encoding."""
    payload = "|".join((
        "".join(map(str, p)),
        ",".join(map(str, hex_masks)),
        ",".join(map(str, orbit_masks)),
        f"F={F}", f"S={S}", f"H={H}",
    ))
    return hashlib.sha256(payload.encode()).hexdigest()


def incidence_table() -> dict:
    """Pin the numbering to explicit permutations so nothing depends on our code."""
    hexagons = []
    for h, rep in enumerate(core.ROT_REPS):
        hexagons.append(dict(hexagon=h,
                             windows=["".join(map(str, w))
                                      for w in core.orbit(rep, core.SIGMA)]))
    orbits = []
    for q, rep in enumerate(core.E_REPS):
        ports = core.orbit(rep, core.E)
        orbits.append(dict(orbit=q,
                           ports=["".join(map(str, w)) for w in ports],
                           block=[exact.HEX_POSITION[w][0] for w in ports]))
    return dict(schema=SCHEMA_VERSION, n_orbits=NORB, n_hexagons=NHEX,
                orbit_block_size=5, hexagon_window_count=6,
                hexagons=hexagons, orbits=orbits)


def scan(checkpoint_dir: Path):
    """Re-derive the Round-79 census, yielding one record per residual state."""
    for path in sorted(glob.glob(str(checkpoint_dir / "*.json"))):
        root = os.path.basename(path)[:-5]
        data = json.load(open(path))
        for idx, entry in enumerate(data["frontier"]):
            st = entry["state"]
            hm, om = st["hex_masks"], st["orbit_masks"]
            F, S, H = st["F"], st["S"], st["H"]
            P = sum(pc(m) for m in om)
            visited = sum(pc(m) for m in hm)
            O = sum(1 for m in om if m)
            D = 5 * O - P
            Ndef = S + F - O
            Phi = 5 + 6 * (TP - P) - (720 - visited)
            if F > 1 or H > 0 or P > TP or O > TO or Ndef > NLIM:
                continue
            rem = TP - P
            num = TD - D + rem
            if not (rem >= 0 and num % 5 == 0 and 0 <= num // 5 <= rem):
                continue
            if 720 - visited < rem or Phi < 0 or (TO - O) > rem + (1 - F):
                continue
            q0 = exact.ORBIT_PHASE[tuple(st["p"])][0]
            used = pc(om[q0])
            Rcap = max(NLIM - Ndef, 0)
            if (5 - used) + 5 * (TO - O) + 4 * (Rcap + Phi) - rem < 0:
                continue
            dead = 0
            live_elsewhere = []
            for q in range(NORB):
                mask = om[q]
                if not mask:
                    continue
                dq = lq = 0
                for ph in range(5):
                    if mask & (1 << ph):
                        continue
                    h, b = PORT_HEXBIT[q][ph]
                    if hm[h] & (1 << b):
                        dq += 1
                    else:
                        lq += 1
                dead += dq
                if q != q0 and lq:
                    live_elsewhere.append(lq)
            if dead > TD:
                continue
            budget = TD - dead
            live_elsewhere.sort()
            acc = kept = 0
            for x in live_elsewhere:
                if acc + x <= budget:
                    acc += x
                    kept += 1
                else:
                    break
            if len(live_elsewhere) - kept > Rcap + Phi:
                continue
            cbits = openbits = 0
            for q in range(NORB):
                if om[q]:
                    cbits |= BLOCKBITS[q]
                    openbits |= 1 << q
            c = 5 * O - pc(cbits)
            if c > 5:
                continue
            yield dict(sid=state_id(st["p"], hm, om, F, S, H), root=root, idx=idx,
                       c=c, b=5 - c, O=O, K=TO - O, P=P, Phi=Phi, Ndef=Ndef,
                       D=D, D_dead=dead, r=P - (sum(1 for m in hm if m)),
                       C=f"{cbits:030x}", U=f"{ALLHEX ^ cbits:030x}",
                       open_orbits=f"{openbits:036x}")
        del data


def export(checkpoint_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "incidence_table.json").write_text(
        json.dumps(incidence_table(), indent=1), encoding="utf-8")

    rows = []
    c5 = []
    for rec in scan(checkpoint_dir):
        (c5 if rec["c"] == 5 else rows).append(rec)
    print(f"scanned residual: c<=4 {len(rows)}, c=5 {len(c5)}", flush=True)

    # --- the 148 c = 5 survivors, identified from the Round-78 certificate archive ---
    certs = json.load(gzip.open(
        ROOT / "outputs" / "rr_exact_cover_collision5_certificates_claude.json.gz", "rt"))
    c5_sat_keys = {k for k, v in certs.items() if not v["verdict"].startswith("UNSAT")}
    c5_rows = [r for r in c5 if r["U"] in c5_sat_keys]
    print(f"c=5 SAT survivors carried from Round 78: {len(c5_rows)}", flush=True)

    # --- distinct instances, decided (verdict reason recorded, not just SAT/UNSAT) ---
    groups = defaultdict(list)
    for r in rows:
        groups[(r["U"], r["b"])].append(r["sid"])
    print(f"distinct (U,b) instances: {len(groups)}", flush=True)

    verdicts = {}
    agg = defaultdict(Counter)
    inst_rows = []
    for iid, ((uhex, b), sids) in enumerate(sorted(groups.items())):
        U = int(uhex, 16)
        K = (pc(U) + b) // 5
        rec = slack.decide(U, K, b)
        verdicts[(uhex, b)] = rec["verdict"]
        c = 5 - b
        agg[c][rec["verdict"]] += len(sids)
        cand = [q for q in range(NORB) if pc(BLOCKBITS[q] & U) >= 5 - b]
        inst_rows.append(dict(
            iid=iid, c=c, b=b, K=K, size_U=pc(U), U=uhex,
            candidate_orbits=cand,
            candidate_blocks=[sorted(set(PORT_HEX[q])) for q in cand],
            verdict=rec["verdict"],
            sat=rec["verdict"] == "SAT",
            witness_orbits=rec.get("witness_orbits"),
            forced_blocks=rec.get("forced_blocks"),
            components=rec.get("components"),
            search_nodes=rec.get("search_nodes"),
            n_states=len(sids), state_ids=sids))
        if (iid + 1) % 10000 == 0:
            print(f"  decided {iid+1}/{len(groups)}", flush=True)

    index = {(r["U"], r["b"]): i for i, r in
             ((row["iid"], row) for row in inst_rows)}
    with gzip.open(out_dir / "states.jsonl.gz", "wt") as fh:
        fh.write(json.dumps(dict(schema=SCHEMA_VERSION, record="header",
                                 kind="states", n_records=len(rows))) + "\n")
        for r in rows:
            r = dict(r)
            r["iid"] = index[(r["U"], r["b"])]
            r["weight"] = 1
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    with gzip.open(out_dir / "instances.jsonl.gz", "wt") as fh:
        fh.write(json.dumps(dict(schema=SCHEMA_VERSION, record="header",
                                 kind="instances", n_records=len(inst_rows))) + "\n")
        for r in inst_rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    with gzip.open(out_dir / "collision5_survivors.jsonl.gz", "wt") as fh:
        fh.write(json.dumps(dict(schema=SCHEMA_VERSION, record="header",
                                 kind="collision5_survivors",
                                 n_records=len(c5_rows),
                                 note="Round-78 exact-cover SAT states, carried through "
                                      "Round 79 untouched")) + "\n")
        for r in c5_rows:
            r = dict(r)
            r["weight"] = 1
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")

    # --- compare against the Round-79 report ---
    report = {}
    mismatches = []
    for c in (1, 2, 3, 4):
        sat = agg[c]["SAT"]
        unknown = agg[c].get("UNKNOWN_node_cap", 0)
        total = sum(agg[c].values())
        closed = total - sat - unknown
        report[f"c={c}"] = dict(states=total, closed=closed, sat=sat, unknown=unknown,
                                by_verdict=dict(agg[c]))
        e = EXPECTED[c]
        for k, v in (("states", total), ("closed", closed), ("sat", sat)):
            if e[k] != v:
                mismatches.append(dict(band=c, field=k, expected=e[k], got=v))
    totals = dict(states=sum(report[f"c={c}"]["states"] for c in (1, 2, 3, 4)),
                  closed=sum(report[f"c={c}"]["closed"] for c in (1, 2, 3, 4)),
                  sat=sum(report[f"c={c}"]["sat"] for c in (1, 2, 3, 4)),
                  instances=len(inst_rows), c5_survivors=len(c5_rows))
    totals["residual"] = totals["sat"] + totals["c5_survivors"]
    for k, v in EXPECTED_TOTAL.items():
        if totals[k] != v:
            mismatches.append(dict(band="total", field=k, expected=v, got=totals[k]))

    dup = len(rows) - len({r["sid"] for r in rows})
    return dict(schema=SCHEMA_VERSION, per_band=report, totals=totals,
                duplicate_state_ids=dup, mismatches_vs_round_79=mismatches)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoints", default=str(ROOT / "outputs" / "rr_target_a_checkpoints"))
    ap.add_argument("--out-dir", default=str(ROOT / "outputs" / "rr_slack_cover_archive"))
    ap.add_argument("--report", default=str(ROOT / "outputs" / "rr_slack_cover_archive_export_claude.json"))
    args = ap.parse_args()
    summary = export(Path(args.checkpoints), Path(args.out_dir))
    Path(args.report).write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary["totals"], indent=1))
    print("duplicate state ids:", summary["duplicate_state_ids"])
    print("mismatches vs Round 79:", summary["mismatches_vs_round_79"] or "NONE")


if __name__ == "__main__":
    main()
